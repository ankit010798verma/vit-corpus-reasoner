"""Run evaluation set at 3 budget modes, compute accuracy, generate budget curve."""
import json
import random
import time
from pathlib import Path
from datetime import datetime

from src.config import BudgetMode
from src.cost.tracker import tracker
from src.evaluation.questions import EVAL_QUESTIONS
from src.query.router import ask

random.seed(42)


def _normalize(text: str) -> str:
    """Normalize text: strip markdown formatting, Unicode chars, punctuation."""
    import re
    # Strip markdown bold/italic/headers so **16×16** matches 16×16
    text = re.sub(r'\*{1,3}', '', text)
    text = re.sub(r'^#{1,3}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'`([^`]*)`', r'\1', text)
    return (text.lower()
            .replace("×", "x").replace("✕", "x")
            .replace("≈", "~").replace("≤", "<=").replace("≥", ">=")
            .replace("%", " pct ").replace("−", "-")
            .replace("–", "-").replace("—", "-"))


def _cost_stats(results: list[dict]) -> dict:
    """Compute per-question cost stats directly from results list."""
    costs = sorted(r["cost_usd"] for r in results)
    n = len(costs)
    if not n:
        return {"mean": 0.0, "median": 0.0, "max": 0.0, "count": 0}
    median = costs[n // 2] if n % 2 else (costs[n // 2 - 1] + costs[n // 2]) / 2
    return {
        "mean": round(sum(costs) / n, 5),
        "median": round(median, 5),
        "max": round(max(costs), 5),
        "count": n,
    }


def _token_set(text: str) -> set[str]:
    """Split text into words, strip punctuation, keep tokens longer than 4 chars."""
    import re as _re
    return set(
        tok for tok in (_re.sub(r'[^\w]', '', w) for w in text.split())
        if len(tok) > 4
    )


def score_answer(system_output: str, gold_answer: str, tier: int) -> float:
    """Simple scoring: check if key terms from gold answer appear in system output."""
    if not system_output or system_output.startswith("No "):
        return 0.0
    sys_lower = _normalize(system_output)
    gold_lower = _normalize(gold_answer)

    gold_words = _token_set(gold_lower)
    sys_words = _token_set(sys_lower)
    if not gold_words:
        return 0.5  # no gold to compare
    overlap = len(gold_words & sys_words) / len(gold_words)
    if len(system_output) < 20:
        return 0.0
    return min(1.0, overlap * 1.5)


def run_eval(budget_mode: BudgetMode, output_dir: Path) -> dict:
    """Run all questions at a given budget mode. Returns results dict."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tracker.reset()

    results = []
    for q in EVAL_QUESTIONS:
        start = time.monotonic()
        cost_before = tracker.total_usd()
        try:
            result = ask(q["question"], budget_mode, question_id=q["id"])
            system_output = result.answer
            cost = tracker.total_usd() - cost_before
        except Exception as e:
            system_output = f"ERROR: {e}"
            cost = 0.0
        latency = time.monotonic() - start

        accuracy = score_answer(system_output, q["gold_answer"], q["tier"])
        results.append({
            "id": q["id"],
            "tier": q["tier"],
            "question": q["question"],
            "gold_answer": q["gold_answer"],
            "system_output": system_output,
            "cost_usd": round(cost, 5),
            "latency_s": round(latency, 2),
            "accuracy": round(accuracy, 3),
            "notes": q.get("notes", ""),
        })
        print(f"  [{q['id']}] tier={q['tier']} score={accuracy:.2f} cost=${cost:.4f}")

    # Compute summary stats
    accuracy_by_tier: dict[int, list[float]] = {}
    for r in results:
        accuracy_by_tier.setdefault(r["tier"], []).append(r["accuracy"])
    tier_summary = {t: round(sum(v) / len(v), 3) for t, v in accuracy_by_tier.items()}
    overall_accuracy = round(sum(r["accuracy"] for r in results) / len(results), 3)

    summary = {
        "budget_mode": budget_mode.value,
        "total_cost_usd": round(tracker.total_usd(), 4),
        "overall_accuracy": overall_accuracy,
        "accuracy_by_tier": tier_summary,
        "cost_stats": _cost_stats(results),
        "timestamp": datetime.utcnow().isoformat(),
        "n_questions": len(results),
    }

    output = {"summary": summary, "results": results}
    out_file = output_dir / f"eval_{budget_mode.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Saved to {out_file}")
    return output


def plot_budget_curve(eval_results: dict[str, dict], out_path: Path) -> None:
    """Generate quality-vs-budget curve plot."""
    if len(eval_results) < 2:
        print(f"Need ≥2 budget modes to plot curve (got {len(eval_results)}). Skipping.")
        return
    import matplotlib.pyplot as plt

    modes = list(eval_results.keys())
    costs = [eval_results[m]["summary"]["total_cost_usd"] for m in modes]
    accs = [eval_results[m]["summary"]["overall_accuracy"] for m in modes]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(costs, accs, "o-", linewidth=2, markersize=8, color="#2563eb")
    for mode, cost, acc in zip(modes, costs, accs):
        ax.annotate(f"{mode}\n(${cost:.2f})", (cost, acc),
                    textcoords="offset points", xytext=(5, 5), fontsize=9)
    ax.set_xlabel("Total Cost (USD)")
    ax.set_ylabel("Average Accuracy Score (0–1)")
    ax.set_title("Quality vs. Budget Curve — VIT Corpus Reasoner")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Budget curve saved to {out_path}")
