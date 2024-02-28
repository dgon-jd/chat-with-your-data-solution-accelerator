
from typing import List
from .AnsweringToolBase import AnsweringToolBase

from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.callbacks import get_openai_callback

from ..helpers.ConfigHelper import ConfigHelper
from ..helpers.LLMHelper import LLMHelper
from ..common.Answer import Answer

from duckduckgo_search import DDGS

from duckduckgo_search import DDGS


class WebSearchTool(AnsweringToolBase):
    def __init__(self) -> None:
        self.name = "WebSearch"
        self.verbose = True
    
    def answer_question(self, question: str, chat_history: List[dict], **kwargs: dict):
        config = ConfigHelper.get_active_config_or_default()    
        # answering_prompt = PromptTemplate(template=config.prompts.answering_prompt, input_variables=["question", "context"])
        answering_prompt = """
            Context: {context}

            Question: {query}
        """
        llm_helper = LLMHelper()
      
        
        # Generate answer from sources
        answer_generator = LLMChain(llm=llm_helper.get_llm(), prompt=PromptTemplate(template=answering_prompt, input_variables=['query', 'context']), verbose=self.verbose)
        with DDGS() as ddgs:
            webResult =  str([r for r in ddgs.text(question, max_results=3)])    
        with get_openai_callback() as cb:
            result = answer_generator({"query": question, "context": webResult})
            
        answer = result["text"]
        print(f"Answer: {answer}")
                    
        
        clean_answer = Answer(question=question,
                              answer=answer,
                              prompt_tokens=cb.prompt_tokens,
                              completion_tokens=cb.completion_tokens)
        return clean_answer