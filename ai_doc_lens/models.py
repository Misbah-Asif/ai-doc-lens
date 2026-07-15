from enum import StrEnum

from pydantic import BaseModel


class DocumentType(StrEnum):
    SALARY_SLIP = "salary_slip"


class PDFValidationResult(BaseModel):
    filename: str
    document_type: DocumentType
    text: str
