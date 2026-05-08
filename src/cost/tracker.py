"""Singleton cost tracker: record every LLM call → compute total USD spend."""
from dataclasses import dataclass, field
from threading import Lock

# Prices in USD per 1M tokens (as of 2025)
MODEL_PRICES: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "claude-haiku-4-5": {"input": 0.80, "output": 4.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-opus-4-7": {"input": 15.00, "output": 75.00},
}

_FALLBACK_PRICE = {"input": 3.00, "output": 15.00}


@dataclass
class CallRecord:
    model: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int = 0
    tier: int | None = None
    question_id: str | None = None
    cost_usd: float = 0.0


class CostTracker:
    _instance: "CostTracker | None" = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    inst._records: list[CallRecord] = []
                    inst._lock = Lock()
                    cls._instance = inst
        return cls._instance

    def record(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
        tier: int | None = None,
        question_id: str | None = None,
    ) -> float:
        prices = MODEL_PRICES.get(model, _FALLBACK_PRICE)
        # Cached tokens cost 10% of input price (Anthropic prompt caching)
        billable_input = input_tokens - cached_tokens
        cost = (billable_input * prices["input"] + cached_tokens * prices["input"] * 0.1 + output_tokens * prices["output"]) / 1_000_000
        rec = CallRecord(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
            tier=tier,
            question_id=question_id,
            cost_usd=cost,
        )
        with self._lock:
            self._records.append(rec)
        return cost

    def total_usd(self) -> float:
        return sum(r.cost_usd for r in self._records)

    def by_model(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for r in self._records:
            result[r.model] = result.get(r.model, 0.0) + r.cost_usd
        return result

    def by_tier(self) -> dict[int, float]:
        result: dict[int, float] = {}
        for r in self._records:
            if r.tier is not None:
                result[r.tier] = result.get(r.tier, 0.0) + r.cost_usd
        return result

    def per_question_stats(self) -> dict:
        per_q: dict[str, float] = {}
        for r in self._records:
            if r.question_id:
                per_q[r.question_id] = per_q.get(r.question_id, 0.0) + r.cost_usd
        if not per_q:
            return {"mean": 0.0, "median": 0.0, "max": 0.0, "count": 0}
        costs = list(per_q.values())
        costs.sort()
        n = len(costs)
        median = costs[n // 2] if n % 2 else (costs[n // 2 - 1] + costs[n // 2]) / 2
        return {
            "mean": sum(costs) / n,
            "median": median,
            "max": max(costs),
            "count": n,
        }

    def report(self) -> dict:
        return {
            "total_usd": round(self.total_usd(), 4),
            "by_model": {k: round(v, 4) for k, v in self.by_model().items()},
            "by_tier": {k: round(v, 4) for k, v in self.by_tier().items()},
            "per_question": self.per_question_stats(),
            "call_count": len(self._records),
        }

    def reset(self) -> None:
        with self._lock:
            self._records.clear()


tracker = CostTracker()
