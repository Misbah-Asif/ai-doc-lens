"""Document-specific extraction configuration.

Adding a new document type requires registering its Pydantic schema and its
document-specific instructions. The LLM extractor itself stays unchanged.
"""

from dataclasses import dataclass

from pydantic import BaseModel

from schemas.extractor import SalarySlipFields


@dataclass(frozen=True)
class DocumentExtractionConfig:
    schema: type[BaseModel]
    instructions: tuple[str, ...] = ()


DOCUMENT_REGISTRY: dict[str, DocumentExtractionConfig] = {
    "salary_slip": DocumentExtractionConfig(
        schema=SalarySlipFields,
        instructions=(
            "Return monetary amounts as numbers without currency symbols or commas.",
            "Return salary_month as an integer between 1 and 12.",
            "Return salary_year as a four-digit integer.",
        ),
    ),
}


def register_document_type(
    document_type: str,
    config: DocumentExtractionConfig,
) -> None:
    """Register extraction configuration for another document type."""
    if not document_type.strip():
        raise ValueError("Document type cannot be empty")
    DOCUMENT_REGISTRY[document_type] = config


def get_document_config(document_type: str) -> DocumentExtractionConfig:
    try:
        return DOCUMENT_REGISTRY[document_type]
    except KeyError as exc:
        supported = ", ".join(sorted(DOCUMENT_REGISTRY))
        raise ValueError(
            f"Unsupported document type '{document_type}'. Supported types: {supported}."
        ) from exc
