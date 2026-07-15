"""Development entry point for the AI Doc Lens API."""

from ai_doc_lens.api import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
