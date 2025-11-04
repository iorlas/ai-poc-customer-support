from pathlib import Path

from pypdf import PdfReader


def load_document(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    if path.suffix == ".pdf":
        reader = PdfReader(path)
        return "\n\n".join(page.extract_text() for page in reader.pages)
    elif path.suffix in [".txt", ".md"]:
        return path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")
