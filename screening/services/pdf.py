"""PDF text extraction.

Uses pypdf rather than pdfplumber: it is pure Python and roughly two orders of
magnitude smaller once installed, which keeps the serverless bundle under
Vercel's size limit and the cold start short. Resumes are text-based PDFs, so
the layout analysis pdfplumber adds buys nothing here.
"""

import io

from pypdf import PdfReader


class PDFExtractionError(Exception):
    """Raised when a PDF cannot be read or carries no extractable text."""


def extract_text_from_bytes(data: bytes) -> str:
    if not data:
        raise PDFExtractionError("The uploaded file is empty.")

    if not data.lstrip()[:5].startswith(b"%PDF-"):
        raise PDFExtractionError("That file is not a PDF.")

    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:  # pypdf raises a wide range of parse errors
        raise PDFExtractionError(f"This PDF could not be read: {exc}") from exc

    text = "\n".join(p for p in pages if p.strip())

    if not text.strip():
        raise PDFExtractionError(
            "No text could be extracted. This looks like a scanned or "
            "image-only PDF, which needs OCR."
        )

    return text
