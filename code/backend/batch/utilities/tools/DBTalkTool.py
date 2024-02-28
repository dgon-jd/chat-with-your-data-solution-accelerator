# from langchain.llms import OpenAI
# from langchain.utilities import SQLDatabase
# from langchain_experimental.sql import SQLDatabaseChain

from typing import List
from .AnsweringToolBase import AnsweringToolBase

# from langchain.chains.llm import LLMChain
# from langchain.prompts import PromptTemplate
from langchain.callbacks import get_openai_callback

from ..helpers.ConfigHelper import ConfigHelper
from ..helpers.LLMHelper import LLMHelper
from ..common.Answer import Answer
from ..common.SourceDocument import SourceDocument

from langchain.chains import RetrievalQA

from ..helpers.EnvHelper import EnvHelper

import os
import openai
from llama_index.core import SQLDatabase,ServiceContext
from llama_index.llms.openai import OpenAI
from sqlalchemy import select, create_engine, MetaData, Table,inspect
from llama_index.core.query_engine import NLSQLTableQueryEngine

from llama_index.core.indices.struct_store.sql_query import (
    SQLTableRetrieverQueryEngine,
)
from llama_index.core.objects import (
    SQLTableNodeMapping,
    ObjectIndex,
    SQLTableSchema,
)

from llama_index.core import VectorStoreIndex


import logging
import sys

class DBTalkTool(AnsweringToolBase):
    
    
    def __init__(self) -> None:
        env_helper = EnvHelper()

        self.name = "QuestionAnswer"
        # self.vector_store = AzureSearchHelper().get_vector_store()
        # self.db = SQLDatabase.from_uri(

        connectin_uri = env_helper.DB_CONNECTION_STRING
        engine = create_engine(connectin_uri)
        
        metadata_obj = MetaData()
        metadata_obj.reflect(engine)

        sql_database = SQLDatabase(engine)

        table_node_mapping = SQLTableNodeMapping(sql_database)
        table_schema_objs = [
            (SQLTableSchema(table_name='po_parts_table', context_str="""This table gives information regarding purchase orders and parts in it. Columns description: "part_number" - the PART NUMBER; po_number - order number; part_name - part name; item# - count of these parts in the order. The table connected to the purchase_order table via po_number column, which contains purchase order details""")),
            (SQLTableSchema(table_name='purchase_orders', context_str="""This table gives secondary information regarding the purchase order vendors (vendor), contact, date_ordered. It is connected to vendor table via vendor. The table connected via po_number to the po_parts_table table, which contains parts and part number details.""")),
            (SQLTableSchema(table_name='vendors', context_str="This table gives information regarding the vendor details")),
            (SQLTableSchema(table_name='approved_vendors', context_str="This table gives information regarding the approved vendor details")),
        ]
        # for table_name in metadata_obj.tables.keys():
        #     table_schema_objs.append(SQLTableSchema(table_name=table_name))
        obj_index = ObjectIndex.from_objects(
            table_schema_objs,
            table_node_mapping,
            VectorStoreIndex
        )
            
        llm = LLMHelper().get_llm()
        verbose = True

        service_context = ServiceContext.from_defaults(llm=llm)
    
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        # for table_name in table_names:
        

        self.query_engine = SQLTableRetrieverQueryEngine(sql_database, obj_index.as_retriever(similarity_top_k=1)
)
        # self.converter = llamaindex.TextToSQL()

    
    def answer_question(self, question: str, chat_history: List[dict], **kwargs: dict):
        
        # 
        
        # db_chain = SQLDatabaseChain.from_llm(llm, self.db, verbose=True)

        # Retrieve documents as sources
        # sources = self.vector_store.similarity_search(query=question, k=4, search_type="hybrid")
    

        response_md = ""
        sql = ""
        with get_openai_callback() as cb:
            try:
                response = self.query_engine.query(question + """ Put quotes ("") around the column names.""")
                
                response_md = str(response)
                print(f"Answer: {response_md}")

                sql = response.metadata["sql_query"]
            except Exception as ex:
                response_md = "Error"
                sql = f"ERROR: {str(ex)}" 
            # result = db_chain(question)
            
            # answer = result["result"]
                    
        # Generate Answer Object
        
        clean_answer = Answer(question=question,
                              answer=response_md + "\n\nSQL: " + sql,
                              source_documents=[],
                              prompt_tokens=cb.prompt_tokens,
                              completion_tokens=cb.completion_tokens)
        return clean_answer
