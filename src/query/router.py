"""Route (question, budget_mode) → appropriate tier engine → synthesized answer."""
import time
from src.config import BudgetMode
from src.cost.tracker import tracker
from src.query.classifier import classify
from src.reasoning.synthesizer import FinalAnswer, format_answer


def ask(question: str, budget_mode: BudgetMode = BudgetMode.MEDIUM, question_id: str | None = None) -> FinalAnswer:
    """Main entry point: classify → route → synthesize."""
    cost_before = tracker.total_usd()
    start = time.monotonic()

    tier = classify(question)

    raw = _dispatch(tier, question, budget_mode)

    cost_usd = tracker.total_usd() - cost_before
    latency_ms = int((time.monotonic() - start) * 1000)

    result = format_answer(raw, tier, cost_usd)
    result.reasoning_trace = f"Tier {tier} | {budget_mode.value} | {latency_ms}ms | ${cost_usd:.5f}"
    return result


def _dispatch(tier: int, question: str, budget_mode: BudgetMode) -> dict:
    from src.reasoning.engines import tier1, tier2, tier3, tier4, tier5, tier6, tier7, tier8

    handlers = {
        1: lambda: tier1.answer(question, budget_mode),
        2: lambda: tier2.answer(question, budget_mode),
        3: lambda: tier3.answer(question, budget_mode),
        4: lambda: tier4.answer(question, budget_mode),
        5: lambda: tier5.answer(question, budget_mode),
        6: lambda: tier6.answer(question, budget_mode),
        7: lambda: tier7.answer(question, budget_mode),
        8: lambda: tier8.answer(question, budget_mode),
    }
    handler = handlers.get(tier, handlers[1])
    return handler()
