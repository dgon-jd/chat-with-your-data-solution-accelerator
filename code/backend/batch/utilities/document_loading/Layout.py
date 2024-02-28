from typing import List
from .DocumentLoadingBase import DocumentLoadingBase
from ..helpers.AzureFormRecognizerHelper import DocumentAnalysisClient
from ..common.SourceDocument import SourceDocument
from ..helpers.EnvHelper import EnvHelper
from azure.core.credentials import AzureKeyCredential

class LayoutDocumentLoading(DocumentLoadingBase):
    def __init__(self) -> None:
        super().__init__()

    def load(self, document_url: str) -> List[SourceDocument]:
        env_helper: EnvHelper = EnvHelper()

        document_analysis_client = DocumentAnalysisClient(
        endpoint=env_helper.AZURE_FORM_RECOGNIZER_ENDPOINT, credential=AzureKeyCredential(env_helper.AZURE_FORM_RECOGNIZER_KEY)
        )
        
        # azure_form_recognizer_client = AzureFormRecognizerClient()
        poller = document_analysis_client.begin_analyze_document_from_url("prebuilt-document", document_url)
        result = poller.result()
        document = ""
        # pages_content = azure_form_recognizer_client.begin_analyze_document_from_url(
        #     document_url, use_layout=True
        # )
        for kv_pair in result.key_value_pairs:
            if kv_pair.key and kv_pair.value:
                document += " Key '{}': Value: '{}'".format(kv_pair.key.content, kv_pair.value.content)
            else:
                document += "Key '{}': Value:".format(kv_pair.key.content)

        document += "\n\n----------------------------------------\n\n"
        documents = [
            SourceDocument(
                content=document,
                source=document_url,
            )
        ]
        return documents
