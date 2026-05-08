"""Fuzzy paper title → paper_id lookup for T1 named-paper questions."""
import re
from rapidfuzz import process, fuzz

from src.knowledge.models import Paper
from src.knowledge.store import get_session

_title_cache: dict[str, tuple[str, str]] | None = None  # title_lower → (paper_id, title)


def _load_cache() -> dict[str, tuple[str, str]]:
    global _title_cache
    if _title_cache is None:
        with get_session() as session:
            papers = session.query(Paper).all()
            _title_cache = {p.title.lower(): (p.id, p.title) for p in papers if p.title}
    return _title_cache


def find_paper_id(query: str, threshold: int = 70) -> str | None:
    """Return paper_id for a paper name mentioned in a query, or None."""
    cache = _load_cache()
    if not cache:
        return None

    # Extract a paper reference: quoted titles, "the X paper", "X et al. YYYY"
    candidates = []

    # Quoted titles
    quoted = re.findall(r'"([^"]{10,})"', query)
    candidates.extend(quoted)

    # "... paper" patterns
    paper_refs = re.findall(r'(?:the\s+)?([A-Z][A-Za-z\s-]+(?:Transformer|ViT|DeiT|DINO|MAE|BEiT|Swin|PVT|CvT))[^,]*(?:paper)?', query)
    candidates.extend(paper_refs)

    # "Author et al. YYYY" patterns
    author_refs = re.findall(r'([A-Z][a-z]+(?:\s+et\s+al\.?)?\s*(?:\d{4})?)', query)
    candidates.extend(author_refs)

    best_id = None
    best_score = threshold

    for candidate in candidates:
        match = process.extractOne(candidate.lower(), cache.keys(), scorer=fuzz.partial_ratio)
        if match and match[1] >= best_score:
            best_score = match[1]
            best_id = cache[match[0]][0]

    return best_id
