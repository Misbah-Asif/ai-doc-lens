# AI Doc Lens

FastAPI service, Python SDK, and CLI for validating document inputs. The initial
supported document type is `salary_slip`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn ai_doc_lens.api:app --reload
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## API

```bash
curl -X POST http://127.0.0.1:8000/v1/documents/validate \
  -F 'file=@/path/to/salary-slip.pdf;type=application/pdf' \
  -F 'document_type=salary_slip'
```

Both `file` and `document_type` are required multipart form fields. Uploaded
files are validated in a temporary location and deleted after the request.

## Python SDK

```python
from ai_doc_lens import validate_pdf

result = validate_pdf("/path/to/salary-slip.pdf", "salary_slip")
print(result)
```

## CLI

```bash
ai-doc-lens /path/to/salary-slip.pdf --document-type salary_slip
```

Validation checks that the path exists, is a readable file with a `.pdf`
extension, and can be opened by a PDF parser.
