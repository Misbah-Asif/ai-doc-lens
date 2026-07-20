import os
from pathlib import Path
import sys, pathlib, pymupdf
import requests
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from ai_doc_lens.llm_extractor import LLMExtractor

from ai_doc_lens.models import DocumentType, PDFValidationResult


class PDFValidationError(ValueError):
    """Raised when an input does not satisfy the PDF requirements."""


async def validate_pdf(
    file: str | os.PathLike[str],
    document_type: DocumentType | str,
) -> PDFValidationResult:
    """Validate a local PDF path and return basic document metadata."""

    try:
        parsed_document_type = DocumentType(document_type)
    except ValueError as exc:
        supported = ", ".join(item.value for item in DocumentType)
        raise PDFValidationError(
            f"Unsupported document type '{document_type}'. Supported types: {supported}."
        ) from exc
    try:
        pdf_bytes = await file.read()
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:  # open document
            text = chr(12).join([page.get_text() for page in doc])
        print("before result", text)
        result = LLMExtractor().extract(text, document_type="salary_slip")

        print("result", result)
    except (OSError, PdfReadError, ValueError) as exc:
        raise PDFValidationError("File cannot be opened as a valid PDF") from exc

    return PDFValidationResult(
        filename="",
        document_type=parsed_document_type,
        validations=result
    )
