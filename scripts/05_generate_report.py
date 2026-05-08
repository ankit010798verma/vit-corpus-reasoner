"""Generate a human-readable Markdown evaluation report from the latest eval JSON files."""
import json
from pathlib import Path

RESULTS_DIR = Path("eval/results")
REPORT_PATH = RESULTS_DIR / "eval_report.md"


def latest_json(mode: str) -> Path | None:
    files = sorted(RESULTS_DIR.glob(f"eval_{mode}_*.json"))
    return files[-1] if files else None


def truncate(text: str, n: int = 300) -> str:
    text = text.strip().replace("\n", " ")
    return text[:n] + "…" if len(text) > n else text


def main():
    modes = ["low", "medium", "high"]
    loaded: dict[str, dict] = {}
    for m in modes:
        p = latest_json(m)
        if p:
            with open(p) as f:
                loaded[m] = json.load(f)
            print(f"Loaded {p.name}")
        else:
            print(f"Warning: no eval_{m}_*.json found")

    lines: list[str] = []
    lines.append("# VIT Corpus Reasoner — Evaluation Report\n")
    lines.append("*Auto-generated from eval/results/eval_*.json*\n")

    # ── Summary table ──
    lines.append("## Summary\n")
    lines.append("| Budget Mode | Overall Accuracy | Total Cost (USD) | Mean Q Cost | Median Q Cost | Max Q Cost |")
    lines.append("|-------------|-----------------|-----------------|-------------|---------------|------------|")
    for m in modes:
        if m not in loaded:
            continue
        s = loaded[m]["summary"]
        # Compute cost stats from results (pre-computed summary.cost_stats is broken in old runs)
        q_costs = sorted(r["cost_usd"] for r in loaded[m]["results"])
        n = len(q_costs)
        mean_c = sum(q_costs) / n if n else 0
        med_c = q_costs[n // 2] if n % 2 else (q_costs[n//2-1] + q_costs[n//2]) / 2 if n else 0
        max_c = max(q_costs) if n else 0
        lines.append(
            f"| {m.upper()} | {s['overall_accuracy']:.1%} | ${s['total_cost_usd']:.4f} "
            f"| ${mean_c:.5f} | ${med_c:.5f} | ${max_c:.5f} |"
        )
    lines.append("")

    # ── Accuracy by tier ──
    lines.append("## Accuracy by Tier\n")
    lines.append("| Tier | LOW | MEDIUM | HIGH |")
    lines.append("|------|-----|--------|------|")
    for t in range(1, 9):
        row = [f"T{t}"]
        for m in modes:
            if m in loaded:
                acc = loaded[m]["summary"].get("accuracy_by_tier", {}).get(str(t), "—")
                row.append(f"{acc:.1%}" if isinstance(acc, float) else str(acc))
            else:
                row.append("—")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    # ── Per-question results (HIGH mode) ──
    if "high" not in loaded:
        print("No HIGH mode results found — skipping per-question section")
    else:
        lines.append("## Per-Question Results (HIGH budget mode)\n")
        lines.append("> Questions, gold answers, system outputs, and scores for all 40 evaluation questions.\n")
        tier_results: dict[int, list] = {}
        for r in loaded["high"]["results"]:
            tier_results.setdefault(r["tier"], []).append(r)

        tier_names = {
            1: "Single-document factual",
            2: "Corpus-level aggregation",
            3: "Comparative / contradiction",
            4: "Temporal / evolution",
            5: "Citation-graph reasoning",
            6: "Multi-hop / compositional",
            7: "Negation / absence",
            8: "Quantitative computation",
        }
        for t in range(1, 9):
            results = tier_results.get(t, [])
            avg_acc = sum(r["accuracy"] for r in results) / len(results) if results else 0
            lines.append(f"### Tier {t} — {tier_names.get(t, '')} (avg score: {avg_acc:.1%})\n")
            for r in results:
                lines.append(f"**[{r['id']}]** `{r['question']}`\n")
                lines.append(f"- **Gold answer:** {truncate(r['gold_answer'], 200)}")
                lines.append(f"- **System output:** {truncate(r['system_output'], 300)}")
                lines.append(f"- **Score:** {r['accuracy']:.2f} | **Cost:** ${r['cost_usd']:.5f} | **Latency:** {r['latency_s']:.1f}s")
                if r.get("notes"):
                    lines.append(f"- *Note: {r['notes']}*")
                lines.append("")

    # ── Budget curve reference ──
    lines.append("## Budget Curve\n")
    lines.append("See `eval/results/budget_curve.png` for the quality-vs-budget plot.\n")
    lines.append("| Budget Mode | Approx. USD | Accuracy |")
    lines.append("|-------------|-------------|----------|")
    for m in modes:
        if m in loaded:
            s = loaded[m]["summary"]
            lines.append(f"| {m.upper()} | ${s['total_cost_usd']:.4f} | {s['overall_accuracy']:.1%} |")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines))
    print(f"\nReport written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
