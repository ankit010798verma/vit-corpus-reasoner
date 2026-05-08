"""PDF → section-aware chunks stored in SQLite."""
import re
import hashlib
from pathlib import Path

import fitz  # PyMuPDF

from src.knowledge.models import Chunk, Paper
from src.knowledge.store import get_session

MAX_CHUNK_TOKENS = 1500   # approximate — 1 token ≈ 4 chars
MAX_CHUNK_CHARS = MAX_CHUNK_TOKENS * 4

SECTION_PATTERNS = re.compile(
    r"^(?:(?:\d+\.?\s+)?(?:"
    r"abstract|introduction|related\s+work|background|"
    r"method(?:ology)?s?|approach|model|architecture|"
    r"experiment(?:al\s+setup)?s?|result(?:s\s+and\s+discussion)?|"
    r"discussion|conclusion|limitation|future\s+work|"
    r"appendix|acknowledgment|reference"
    r"))",
    re.IGNORECASE,
)

FIGURE_CAPTION = re.compile(r"^fig(?:ure)?\.?\s*\d+", re.IGNORECASE)


def _normalize_section(header: str) -> str:
    h = header.lower().strip()
    if "abstract" in h:
        return "abstract"
    if "introduction" in h:
        return "introduction"
    if "related" in h or "background" in h:
        return "related_work"
    if any(w in h for w in ["method", "approach", "model", "architecture"]):
        return "method"
    if any(w in h for w in ["experiment", "setup", "training"]):
        return "experiments"
    if "result" in h:
        return "results"
    if "discussion" in h:
        return "discussion"
    if any(w in h for w in ["conclusion", "limitation", "future"]):
        return "conclusion"
    if "appendix" in h:
        return "appendix"
    if "reference" in h or "acknowledgment" in h:
        return "references"
    return "body"


def _split_long_text(text: str) -> list[str]:
    """Split text that exceeds MAX_CHUNK_CHARS at sentence boundaries."""
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current = [], ""
    for sent in sentences:
        if len(current) + len(sent) > MAX_CHUNK_CHARS and current:
            chunks.append(current.strip())
            current = sent
        else:
            current += " " + sent
    if current.strip():
        chunks.append(current.strip())
    return chunks or [text[:MAX_CHUNK_CHARS]]


def _chunk_id(paper_id: str, section: str, chunk_idx: int) -> str:
    return f"{paper_id}__{section}__{chunk_idx}"


def _sanitize(text: str) -> str:
    """Remove surrogate characters that SQLite's UTF-8 rejects."""
    return text.encode("utf-8", "surrogatepass").decode("utf-8", "replace")


def extract_chunks(pdf_path: str, paper_id: str) -> list[dict]:
    """Extract text chunks from a PDF, segmented by section."""
    chunks = []
    chunk_idx = 0

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"  Cannot open {pdf_path}: {e}")
        return []

    current_section = "abstract"
    section_buffer = []
    section_page_start = 0

    for page_num, page in enumerate(doc):
        blocks = page.get_text("blocks", sort=True)

        for block in blocks:
            if block[6] != 0:  # skip non-text blocks
                continue
            text = block[4].strip()
            if not text or len(text) < 10:
                continue

            # Detect figure captions
            if FIGURE_CAPTION.match(text):
                split = _split_long_text(text)
                for part in split:
                    chunks.append({
                        "id": _chunk_id(paper_id, "figure_caption", chunk_idx),
                        "paper_id": paper_id,
                        "section": current_section,
                        "chunk_type": "figure_caption",
                        "text": _sanitize(part),
                        "page_start": page_num,
                        "page_end": page_num,
                        "chunk_idx": chunk_idx,
                    })
                    chunk_idx += 1
                continue

            # Detect section headers
            first_line = text.split("\n")[0].strip()
            if SECTION_PATTERNS.match(first_line) and len(first_line) < 80:
                # Flush current section
                if section_buffer:
                    combined = " ".join(section_buffer)
                    for part in _split_long_text(combined):
                        chunks.append({
                            "id": _chunk_id(paper_id, current_section, chunk_idx),
                            "paper_id": paper_id,
                            "section": current_section,
                            "chunk_type": "text",
                            "text": _sanitize(part),
                            "page_start": section_page_start,
                            "page_end": page_num,
                            "chunk_idx": chunk_idx,
                        })
                        chunk_idx += 1
                    section_buffer = []
                current_section = _normalize_section(first_line)
                section_page_start = page_num
                # Body text after the header on the same block
                rest = "\n".join(text.split("\n")[1:]).strip()
                if rest:
                    section_buffer.append(rest)
            else:
                section_buffer.append(text)

    # Flush last section
    if section_buffer:
        combined = " ".join(section_buffer)
        for part in _split_long_text(combined):
            chunks.append({
                "id": _chunk_id(paper_id, current_section, chunk_idx),
                "paper_id": paper_id,
                "section": current_section,
                "chunk_type": "text",
                "text": _sanitize(part),
                "page_start": section_page_start,
                "page_end": len(doc) - 1,
                "chunk_idx": chunk_idx,
            })
            chunk_idx += 1

    # Extract tables using PyMuPDF table finder
    for page_num, page in enumerate(doc):
        try:
            tables = page.find_tables()
            for table in tables.tables:
                rows = table.extract()
                if not rows:
                    continue
                table_text = "\n".join(
                    " | ".join(str(cell or "") for cell in row)
                    for row in rows
                )
                if len(table_text.strip()) < 20:
                    continue
                chunks.append({
                    "id": _chunk_id(paper_id, "table", chunk_idx),
                    "paper_id": paper_id,
                    "section": "results",  # tables usually in results/experiments
                    "chunk_type": "table",
                    "text": _sanitize(table_text),
                    "page_start": page_num,
                    "page_end": page_num,
                    "chunk_idx": chunk_idx,
                })
                chunk_idx += 1
        except Exception:
            pass

    doc.close()
    return chunks


def ingest_paper(paper_id: str, pdf_path: str) -> int:
    """Extract and store chunks for one paper. Returns chunk count."""
    chunks_data = extract_chunks(pdf_path, paper_id)
    if not chunks_data:
        return 0

    with get_session() as session:
        # Remove existing chunks for idempotency
        session.query(Chunk).filter(Chunk.paper_id == paper_id).delete()
        for c in chunks_data:
            session.add(Chunk(**c))

    return len(chunks_data)
