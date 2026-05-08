#!/usr/bin/env python3
"""Step 4: Run evaluation at 3 budget levels and generate budget curve."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings, BudgetMode
from src.knowledge.store import init_db
from src.knowledge.indexer import load_indexes
from src.evaluation.runner import run_eval, plot_budget_curve

OUTPUT_DIR = Path("./eval/results")


if __name__ == "__main__":
    init_db(settings.db_path)
    load_indexes()

    all_results = {}
    for mode in [BudgetMode.LOW, BudgetMode.MEDIUM, BudgetMode.HIGH]:
        print(f"\n{'='*50}")
        print(f"Running evaluation: {mode.value.upper()} budget mode")
        print("=" * 50)
        result = run_eval(mode, OUTPUT_DIR)
        all_results[mode.value] = result
        summary = result["summary"]
        print(f"\nSummary: accuracy={summary['overall_accuracy']} cost=${summary['total_cost_usd']:.4f}")
        print(f"By tier: {summary['accuracy_by_tier']}")

    plot_budget_curve(all_results, OUTPUT_DIR / "budget_curve.png")

    print("\n" + "=" * 50)
    print("TOTAL COST REPORT")
    print("=" * 50)
    for mode, result in all_results.items():
        s = result["summary"]
        print(f"  {mode}: accuracy={s['overall_accuracy']}, cost=${s['total_cost_usd']:.4f}")
