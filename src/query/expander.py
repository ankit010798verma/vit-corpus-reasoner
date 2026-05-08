"""Query expansion: generate 2-3 alternative phrasings using Haiku for better retrieval recall."""
import anthropic
from src.config import settings, BudgetMode
from src.cost.tracker import tracker

_SYSTEM = (
    "You are a query expansion assistant for academic research retrieval. "
    "Given a question about Vision Transformer research papers, return 2 alternative phrasings "
    "that mean the same thing but use different keywords. "
    "Return as a JSON array of strings. No explanation."
)


def expand(question: str, budget_mode: BudgetMode = BudgetMode.MEDIUM) -> list[str]:
    """Return [original] + expanded phrasings. In LOW mode, skip expansion."""
    if budget_mode == BudgetMode.LOW:
        return [question]

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            system=_SYSTEM,
            messages=[{"role": "user", "content": question}],
        )
        usage = resp.usage
        tracker.record("claude-haiku-4-5-20251001", usage.input_tokens, usage.output_tokens)
        import json, re
        raw = resp.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        alternatives = json.loads(raw)
        return [question] + (alternatives if isinstance(alternatives, list) else [])
    except Exception:
        return [question]
