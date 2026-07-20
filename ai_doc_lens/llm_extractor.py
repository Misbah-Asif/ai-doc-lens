"""Schema-driven structured data extraction using a local MLX model."""

import json
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError

from ai_doc_lens.document_registry import get_document_config

DEFAULT_MODEL = "mlx-community/Qwen2.5-1.5B-Instruct-4bit"

ModelLoader = Callable[[str], tuple[Any, Any]]
TextGenerator = Callable[..., str]


class LLMExtractionError(ValueError):
    """Raised when structured fields cannot be extracted or validated."""


def build_extraction_prompt(text: str, document_type: str) -> str:
    """Build a prompt from the registered schema for any document type."""
    if not text.strip():
        raise LLMExtractionError("Document text cannot be empty")

    config = get_document_config(document_type)
    schema = json.dumps(config.schema.model_json_schema(), indent=2)
    specific_rules = "\n".join(f"- {rule}" for rule in config.instructions)

    return f"""Extract structured fields from this {document_type} document.

            Return only one valid JSON object matching this JSON Schema:
            {schema}
            
            Rules:
            - Use only information explicitly present in the supplied document text.
            - Do not guess or hallucinate missing information.
            - Use null when a field is not present.
            - Do not return Markdown fences, commentary, or explanations.
            {specific_rules}
            
            Document text:
            ---BEGIN DOCUMENT---
            {text}
            ---END DOCUMENT---
            """


def _parse_json_object(response: str) -> dict[str, Any]:
    """Parse a JSON object, tolerating whitespace or a Markdown JSON fence."""
    value = response.strip()
    if value.startswith("```") and value.endswith("```"):
        lines = value.splitlines()
        value = "\n".join(lines[1:-1]).strip()

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise LLMExtractionError("LLM returned invalid JSON") from exc

    if not isinstance(parsed, dict):
        raise LLMExtractionError("LLM response must be a JSON object")
    return parsed


class LLMExtractor:
    """Extract validated dictionaries using document registry configuration."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        *,
        loader: ModelLoader | None = None,
        generator: TextGenerator | None = None,
        max_tokens: int = 500,
    ) -> None:
        self.model_name = model_name
        self.max_tokens = max_tokens
        self._loader = loader
        self._generator = generator
        self._model: Any | None = None
        self._tokenizer: Any | None = None

    def _load_model(self) -> tuple[Any, Any]:
        if self._model is None or self._tokenizer is None:
            if self._loader is None:
                try:
                    from mlx_lm import load
                except ImportError as exc:
                    raise LLMExtractionError(
                        "mlx-lm is required for local extraction. Install the MLX extra."
                    ) from exc
                self._loader = load
            self._model, self._tokenizer = self._loader(self.model_name)
        return self._model, self._tokenizer

    def extract(self, text: str, document_type: str) -> dict[str, Any]:
        config = get_document_config(document_type)
        prompt = build_extraction_prompt(text, document_type)
        model, tokenizer = self._load_model()

        formatted_prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False,
            add_generation_prompt=True,
        )

        generator = self._generator
        if generator is None:
            try:
                from mlx_lm import generate
            except ImportError as exc:
                raise LLMExtractionError(
                    "mlx-lm is required for local extraction. Install the MLX extra."
                ) from exc
            generator = generate

        response = generator(
            model,
            tokenizer,
            prompt=formatted_prompt,
            max_tokens=self.max_tokens,
            verbose=False,
        )
        data = _parse_json_object(response)

        try:
            validated = config.schema.model_validate(data)
        except ValidationError as exc:
            raise LLMExtractionError(
                f"LLM response does not match the {document_type} schema"
            ) from exc

        return validated.model_dump()


# Backward-compatible name for callers using the original class.
LLM = LLMExtractor
