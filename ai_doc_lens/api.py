import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status

from ai_doc_lens.models import DocumentType, PDFValidationResult
from ai_doc_lens.validator import PDFValidationError, validate_pdf

app = FastAPI(title="AI Doc Lens", version="0.1.0")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/v1/documents/validate",
    response_model=PDFValidationResult,
    tags=["documents"],
)
async def validate_document(
    file: UploadFile = File(..., description="PDF document"),
    document_type: DocumentType = Form(...),
) -> PDFValidationResult:
    suffix = Path(file.filename or "upload").suffix
    temporary_path: str | None = None

    try:
        print("file", file, type(file))
        print("document_type", document_type)
        result = await validate_pdf(file, document_type)
        return result.model_copy(update={"filename": file.filename or "upload.pdf"})
    except PDFValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    finally:
        await file.close()
