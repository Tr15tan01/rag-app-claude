import re
from io import BytesIO
from pypdf import PdfReader
from fastapi import HTTPException, status

from app.config import settings


def extract_pages(file_bytes: bytes) -> list[str]:
    """Returns a list of page texts, index 0 == page 1."""
    try:
        reader = PdfReader(BytesIO(file_bytes))
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not read PDF -- file may be corrupted.")

    if reader.is_encrypted:
        # Try an empty password (common for "restricted" but not truly
        # protected PDFs); otherwise reject rather than silently failing.
        try:
            reader.decrypt("")
        except Exception:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Encrypted/password-protected PDFs are not supported.")

    if len(reader.pages) > settings.MAX_PAGES_PER_PDF:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"PDF exceeds the {settings.MAX_PAGES_PER_PDF}-page limit.",
        )

    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")  # skip unreadable pages rather than failing the whole doc
    return pages


def _split_sentences(text: str) -> list[str]:
    text = " ".join(text.split())
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def chunk_pages(pages: list[str], max_words: int = 220, overlap_sentences: int = 2):
    """Sentence-aware chunking with overlap, tagged with page numbers so
    answers can cite the exact page they came from."""
    chunks = []
    for page_num, page_text in enumerate(pages, start=1):
        sentences = _split_sentences(page_text)
        current, word_count, idx = [], 0, 0

        for sent in sentences:
            w = len(sent.split())
            if current and word_count + w > max_words:
                chunks.append({"page": page_num, "chunk_index": idx, "text": " ".join(current)})
                idx += 1
                current = current[-overlap_sentences:]
                word_count = sum(len(s.split()) for s in current)
            current.append(sent)
            word_count += w

        if current:
            chunks.append({"page": page_num, "chunk_index": idx, "text": " ".join(current)})

    return [c for c in chunks if len(c["text"].strip()) > 0]
