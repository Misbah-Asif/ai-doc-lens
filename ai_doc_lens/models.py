import json
from enum import StrEnum

from pydantic import BaseModel


class DocumentType(StrEnum):
    SALARY_SLIP = "salary_slip"
    AADHAR_CARD = "aadhar_card"


class PDFValidationResult(BaseModel):
    filename: str
    document_type: DocumentType
    validations: dict
