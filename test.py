"""Manual local-model smoke test.

Run after installing the MLX dependency with: pip install -e '.[mlx]'
"""

import pymupdf

from mlx_lm import load, generate

from dataclasses import dataclass

from pydantic import BaseModel, schema
import json

def extract_pdf_text(filename: str) -> str:
    with pymupdf.open(filename) as document:
        return "\f".join(page.get_text() for page in document)

@dataclass(frozen=True)
class DocumentExtractionConfig:
    schema: type[BaseModel]
    instructions: tuple[str, ...] = ()


class SalarySlipFields(BaseModel):
    document_name: str
    employee_name: str | None = None
    employer_name: str | None = None
    salary_month: int | None = None
    salary_year: int | None = None
    gross_salary: float | None = None
    net_salary: float | None = None
    currency: str | None = None

schema = {
  "properties": {
    "document_name": {
      "title": "Document Name",
      "type": "string"
    },
    "employee_name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": None,
      "title": "Employee Name"
    },
    "employer_name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": None,
      "title": "Employer Name"
    },
    "salary_month": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": None,
      "title": "Salary Month"
    },
    "salary_year": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": None,
      "title": "Salary Year"
    },
    "gross_salary": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": None,
      "title": "Gross Salary"
    },
    "net_salary": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "default": None,
      "title": "Net Salary"
    },
    "currency": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": None,
      "title": "Currency"
    }
  },
  "required": [
    "document_name"
  ],
  "title": "SalarySlipFields",
  "type": "object"
}


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

document_name_type = {
    "salary_slip": "Aadhar Slip",
    "aadhar_card": "Aadhar Card"
}


def normalise_document_name(
    response: str,
    document_type: str,
) -> dict[str, object]:
    """Return a mapped document name only when the model confirmed its type.

    The model's free-form ``document_name`` is deliberately ignored.  This
    prevents labels such as "Salary Slip" from appearing when they are not a
    value in ``document_name_type``.
    """
    data = json.loads(response)
    if not isinstance(data, dict):
        raise ValueError("The model response must be a JSON object")

    is_expected_document = data.pop("_document_type_match", False) is True
    data["document_name"] = (
        document_name_type[document_type] if is_expected_document else ""
    )
    return data

def main() -> None:
    text = extract_pdf_text("Payslip_12345.pdf")
    print("text", text)
    schema = {
        "properties": {
            "document_name": {
                "title": "Document Name",
                "type": "string"
            },
            "employee_name": {
                "anyOf": [
                    {
                        "type": "string"
                    },
                    {
                        "type": "null"
                    }
                ],
                "default": None,
                "title": "Employee Name"
            },
            "employer_name": {
                "anyOf": [
                    {
                        "type": "string"
                    },
                    {
                        "type": "null"
                    }
                ],
                "default": None,
                "title": "Employer Name"
            },
            "salary_month": {
                "anyOf": [
                    {
                        "type": "integer"
                    },
                    {
                        "type": "null"
                    }
                ],
                "default": None,
                "title": "Salary Month"
            },
            "salary_year": {
                "anyOf": [
                    {
                        "type": "integer"
                    },
                    {
                        "type": "null"
                    }
                ],
                "default": None,
                "title": "Salary Year"
            },
            "gross_salary": {
                "anyOf": [
                    {
                        "type": "number"
                    },
                    {
                        "type": "null"
                    }
                ],
                "default": None,
                "title": "Gross Salary"
            },
            "net_salary": {
                "anyOf": [
                    {
                        "type": "number"
                    },
                    {
                        "type": "null"
                    }
                ],
                "default": None,
                "title": "Net Salary"
            },
            "currency": {
                "anyOf": [
                    {
                        "type": "string"
                    },
                    {
                        "type": "null"
                    }
                ],
                "default": None,
                "title": "Currency"
            }
        },
        "required": [
            "document_name"
        ],
        "title": "SalarySlipFields",
        "type": "object"
    }
    MODEL = "mlx-community/Qwen2.5-1.5B-Instruct-4bit"

    model, tokenizer = load(MODEL)
    document_type = "salary_slip"
    mapped_document_name = document_name_type[document_type]

    # This is an internal classification signal.  It is removed before the
    # final result is returned, while document_name is set in Python from the
    # mapper below.
    schema["properties"]["_document_type_match"] = {
        "title": "Document Type Match",
        "type": "boolean",
    }
    schema["required"].append("_document_type_match")
    schema = json.dumps(schema, indent=2)

    prompt = f"""
            Extract structured fields from this Sal\ary document.

            Return only one valid JSON object matching this JSON Schema:
            {schema}
            
            Rules:
            - Use only information explicitly present in the supplied document text.
            - Do not guess or hallucinate missing information.
            - Use null when a field is not present.
            - Do not return Markdown fences, commentary, or explanations.
            - First determine whether the supplied document is actually a {document_type}
              or a clearly equivalent document.
            - Set _document_type_match to true only when it is that document type;
              otherwise set it to false.
            - If _document_type_match is true, document_name must be exactly
              "{mapped_document_name}". If false, document_name must be "".
            - Never use a document category label such as "Salary Slip" for
              document_name unless it is an exact value in the mapper.
            
            
            Document text:
            ---BEGIN DOCUMENT---
            {text}
            ---END DOCUMENT---
    """

    formatted_prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=False,
        add_generation_prompt=True,
    )

    response = generate(
        model,
        tokenizer,
        prompt=formatted_prompt,
        # max_tokens=self.max_tokens,
        verbose=False,
    )

    print("response:", response)

    result = normalise_document_name(response, document_type)
    print(json.dumps(result, indent=2), "response")


if __name__ == "__main__":
    main()
