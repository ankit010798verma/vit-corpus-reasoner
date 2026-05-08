"""Tier 1: Single-document factual — hybrid retrieval + LLM extract."""
import anthropic
from src.config import settings, BudgetMode
from src.cost.tracker import tracker
from src.query.paper_resolver import find_paper_id
from src.query.expander import expand
from src.retrieval.hybrid import retrieve


def _model(budget_mode: BudgetMode) -> str:
    return "claude-haiku-4-5-20251001" if budget_mode in (BudgetMode.LOW, BudgetMode.MEDIUM) else "claude-sonnet-4-6"


def answer(question: str, budget_mode: BudgetMode) -> dict:
    top_k = 3 if budget_mode == BudgetMode.LOW else 5
    use_semantic = budget_mode != BudgetMode.LOW

    # Try to narrow search to a specific paper
    paper_id_filter = find_paper_id(question)

    # Expand query
    queries = expand(question, budget_mode)

    # Retrieve with union
    seen, chunks = set(), []
    for q in queries:
        for c in retrieve(q, top_k=top_k, use_semantic=use_semantic, paper_id_filter=paper_id_filter):
            if c.chunk_id not in seen:
                seen.add(c.chunk_id)
                chunks.append(c)
    chunks = chunks[:top_k]

    if not chunks:
        return {"answer": "No relevant information found.", "evidence": []}

    context = "\n\n".join(f"[{i+1}] Paper {c.paper_id} | Section: {c.section}\n{c.text}" for i, c in enumerate(chunks))
    prompt = f"Question: {question}\n\nContext from papers:\n{context}\n\nAnswer the question directly using the context. Cite sources by their [N] number."

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    model = _model(budget_mode)
    resp = client.messages.create(
        model=model,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    usage = resp.usage
    cached = getattr(usage, "cache_read_input_tokens", 0) or 0
    tracker.record(model, usage.input_tokens, usage.output_tokens, cached_tokens=cached, tier=1)

    # Build evidence with paper titles
    from src.knowledge.models import Paper
    from src.knowledge.store import get_session
    with get_session() as session:
        evidence = []
        for i, c in enumerate(chunks):
            p = session.get(Paper, c.paper_id)
            title = p.title if p else c.paper_id
            year = p.year if (p and p.year is not None) else ""
            evidence.append({
                "ref": i + 1,
                "paper_id": c.paper_id,
                "title": title,
                "year": year,
                "section": c.section,
                "quote": c.text[:300],
            })

    return {"answer": resp.content[0].text.strip(), "evidence": evidence}
