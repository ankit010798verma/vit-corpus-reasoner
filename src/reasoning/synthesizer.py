"""Format raw engine output into a final cited answer for the user."""
from dataclasses import dataclass


@dataclass
class FinalAnswer:
    answer: str
    citations: list[dict]
    tier: int
    cost_usd: float
    reasoning_trace: str = ""


def format_answer(raw: dict, tier: int, cost_usd: float) -> FinalAnswer:
    """Convert tier engine output → structured final answer with citations."""
    answer_text = raw.get("answer", "No answer available.")
    evidence = raw.get("evidence", [])

    # Deduplicate evidence by paper_id
    seen, citations = set(), []
    for e in evidence:
        pid = e.get("paper_id", "")
        if pid and pid not in seen:
            seen.add(pid)
            citations.append({
                "paper_id": pid,
                "title": e.get("title", ""),
                "year": e.get("year", ""),
                "section": e.get("section", ""),
                "quote": e.get("quote", "")[:400],
            })

    # Append formatted citation block to answer text
    if citations and citations[0].get("paper_id") not in ("corpus", ""):
        citation_block = "\n\nSources:\n"
        for i, c in enumerate(citations, 1):
            title = c.get("title", c.get("paper_id", ""))
            year = f" ({c['year']})" if c.get("year") else ""
            section = f" — {c['section']}" if c.get("section") else ""
            quote = f'\n    "{c["quote"]}"' if c.get("quote") else ""
            citation_block += f"[{i}] {title}{year}{section}{quote}\n"
        answer_text = answer_text.rstrip() + citation_block.rstrip()

    return FinalAnswer(
        answer=answer_text,
        citations=citations,
        tier=tier,
        cost_usd=round(cost_usd, 5),
    )
