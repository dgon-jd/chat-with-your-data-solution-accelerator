from typing import List
import pandas as pd
import requests
from io import BytesIO
from .DocumentLoadingBase import DocumentLoadingBase
from ..common.SourceDocument import SourceDocument


class ExcelDocumentLoading(DocumentLoadingBase):
    def __init__(self) -> None:
        super().__init__()

    def _download_document(self, document_url: str) -> BytesIO:
        response = requests.get(document_url)
        file = BytesIO(response.content)
        return file

    def load(self, document_url: str) -> List[SourceDocument]:
        source_documents: List[SourceDocument] = []

        # Read the Excel file
        xls = pd.ExcelFile(self._download_document(document_url))

        # Iterate through each sheet
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)

            # Convert the DataFrame to a text string
            text_content = df.to_string(
                header=True, index=False, index_names=False
            ).strip()

            if text_content:
                source_documents.append(
                    SourceDocument(
                        content=text_content,
                        source=document_url,
                    )
                )

        return source_documents
