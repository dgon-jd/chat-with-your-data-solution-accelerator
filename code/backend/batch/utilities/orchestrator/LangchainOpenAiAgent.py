from typing import List
from langchain.agents import initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from langchain.agents import ZeroShotAgent, AgentExecutor, OpenAIFunctionsAgent, AgentType
from langchain.chains import LLMChain
from langchain.callbacks import get_openai_callback

from .OrchestratorBase import OrchestratorBase
from ..helpers.LLMHelper import LLMHelper
from ..tools.PostPromptTool import PostPromptTool
from ..tools.QuestionAnswerTool import QuestionAnswerTool
from ..tools.TextProcessingTool import TextProcessingTool
from ..tools.ContentSafetyChecker import ContentSafetyChecker
from ..tools. import WebSearchTool
# from ..tools.FinanceTool import CurrentStockPriceTool, StockPerformanceTool
from ..parser.OutputParserTool import OutputParserTool
from ..common.Answer import Answer
from ..helpers.AzureSearchHelper import AzureSearchHelper

from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.tools.render import format_tool_to_openai_function

from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

class LangChainOpenAIAgent(OrchestratorBase):
    def __init__(self) -> None:
        super().__init__()   
        self.content_safety_checker = ContentSafetyChecker()
        self.question_answer_tool = QuestionAnswerTool()
        self.text_processing_tool = TextProcessingTool()
        self.websearch_tool = WebSearchTool()
        self.vector_store = AzureSearchHelper().get_vector_store()
        prompt_template = """
            You are an assistant whose role is to define and categorize situations using formal definitions
            available to you. 
            Your output must be as exact to the reference ground truth information as possible.
            If the situation falls under a certain headdlinein the ground truth- then mention that headline as a part of
            your response. 
            Also define an associated set of facts related to the situation by using the groung truth information. 

            You are not allowed to create new facts.

            Do NOT assume more information than what the situation and ground truth information gives you. It is alright if as
            as result the response is short.

            You are not required to do anything more than provide the relevant information as described.

            Ground truth information available: {context}

            Situation: {query}
            """
        answering_prompt = PromptTemplate(template=prompt_template, input_variables=["query", "context"])

        self.retriever_chain = RetrievalQA.from_chain_type(llm=LLMHelper().get_llm(), chain_type="stuff", retriever=self.vector_store.as_retriever())
        self.retriever_chain.return_source_documents = True
        self.retriever_chain.verbose = True
        
        self.tools = [
            Tool(
                name="data-question-answering",
                func=self.run_tool.run,
                description="useful for when you need to answer questions about anything. Input should be a fully formed question. Do not call the tool for text processing operations like translate, summarize, make concise.",
            ),
            Tool(
                name="text-processing",
                func=self.run_text_processing_tool,
                description="""useful for when you need to process text like translate to Italian, summarize, make concise, in Spanish. 
                Always start the input with be a proper text operation with language if mentioned and then the full text to process.
                e.g. translate to Spanish: <text to translate>""",
            ),
            Tool(name="web-search", 
                 func=self.run_web_search_tool, 
                 description="Use it only when user directly asks to search in the internet to answer about current events or real-time information. You should ask targeted questions."),
            # CurrentStockPriceTool(), 
            # StockPerformanceTool()
        ]

    def run_web_search_tool(self, user_message):
        answer = self.websearch_tool.answer_question(user_message, chat_history=[])
        return answer.to_json()
        
    def run_tool(self, user_message):
        result = RetrievalQA.from_chain_type(llm=LLMHelper().get_llm(), chain_type="stuff", retriever=self.vector_store.as_retriever()).invoke({"query": user_message})
        # answer = self.question_answer_tool.answer_question(user_message, chat_history=[])
        # answer = Answer(question=user_message, 
        #                 answer=result, 
        #                 source_documents=[],
        #                 prompt_tokens=result['usage']['prompt_tokens'],
        #                 completion_tokens=result['usage']['completion_tokens'])
        return answer.to_json()
    
    def run_text_processing_tool(self, user_message):
        answer = self.text_processing_tool.answer_question(user_message, chat_history=[])
        return answer.to_json()   
    
    def orchestrate(self, user_message: str, chat_history: List[dict], **kwargs: dict) -> dict:
        output_formatter = OutputParserTool()
        
        # Call Content Safety tool
        if self.config.prompts.enable_content_safety:
            filtered_user_message = self.content_safety_checker.validate_input_and_replace_if_harmful(user_message)
            if user_message != filtered_user_message:
                messages = output_formatter.parse(question=user_message, answer=filtered_user_message, source_documents=[])
                return messages
        
        # Call function to determine route
        llm_helper = LLMHelper()
        prefix = """Have a conversation with a human, answering the following questions as best you can. You have access to the following tools. 
        You must prioritize the function call over your general knowledge for any question by calling the data-question-answering function.
        Call the text_processing function when the user request an operation on the current context, such as translate, summarize, or paraphrase. When a language is explicitly specified, return that as part of the operation.
        When directly replying to the user, always reply in English. 
        If you do not know answer - use web_search tool.
        You have access to folowwing tools:"""

        suffix = """Begin!"

        {chat_history}
        Question: {input}
        {agent_scratchpad}"""
        prompt = ZeroShotAgent.create_prompt(
            self.tools,
            prefix=prefix,
            suffix=suffix,
            input_variables=["input", "chat_history", "agent_scratchpad"],
        )

        # Create conversation memory
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        for message in chat_history:
            memory.chat_memory.add_user_message(message[0])
            memory.chat_memory.add_ai_message(message[1])
        # Define Agent and Agent Chain
        # llm_chain = LLMChain(llm=llm_helper.get_llm(), prompt=prompt)
        agent = OpenAIFunctionsAgent(llm = llm_helper.get_llm(), tools=self.tools, prompt=prompt)
        # agent = ZeroShotAgent(llm_chain=llm_chain, tools=self.tools, verbose=True)

        # llm=llm_helper.get_llm()
        # llm_with_tools = llm.bind(functions=[format_tool_to_openai_function(t) for t in self.tools])
        # agent = initialize_agent(llm=llm, tools=self.tools, agent=AgentType.OPENAI_FUNCTIONS, memory=memory, prompt=prompt)


        # agent = (
        #     {
        #         "input": lambda x: x["input"],
        #         "agent_scratchpad": lambda x: format_to_openai_functions(
        #             x["intermediate_steps"]
        #         ),
        #     }
        #     | prompt
        #     | llm_with_tools
        #     | OpenAIFunctionsAgentOutputParser()
        # )
        
        agent_chain = AgentExecutor.from_agent_and_tools(
            agent=agent, tools=self.tools, verbose=True, memory=memory)
        # Run Agent Chain
        with get_openai_callback() as cb:
            try:
                # answer = agent_chain.invoke({"input": user_message})
                answer = agent_chain.run(user_message)
                self.log_tokens(prompt_tokens=cb.prompt_tokens, completion_tokens=cb.completion_tokens)
            except Exception as e:
                answer = str( e)
        try:
            answer = Answer.from_json(answer)
        except:
            answer = Answer(question=user_message, answer=answer)
        
        if self.config.prompts.enable_post_answering_prompt:
            post_prompt_tool = PostPromptTool()
            answer = post_prompt_tool.validate_answer(answer)
            self.log_tokens(prompt_tokens=answer.prompt_tokens, completion_tokens=answer.completion_tokens)                

        # Call Content Safety tool
        if self.config.prompts.enable_content_safety:
            filtered_answer = self.content_safety_checker.validate_output_and_replace_if_harmful(answer.answer)
            if answer.answer != filtered_answer:
                messages = output_formatter.parse(question=user_message, answer=filtered_answer, source_documents=[])
                return messages
        
        # Format the output for the UI        
        messages = output_formatter.parse(question=answer.question, answer=answer.answer, source_documents=answer.source_documents)
        return messages
    