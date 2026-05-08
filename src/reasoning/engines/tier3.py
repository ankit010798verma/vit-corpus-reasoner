"""Tier 3: Comparative/contradiction — SQL finds divergent benchmark results, Sonnet narrates."""
import anthropic
from sqlalchemy import text
from src.config import settings, BudgetMode
from src.cost.tracker import tracker
from src.knowledge.store import get_engine
from src.knowledge.models import Paper
from src.knowledge.store import get_session


def _model(budget_mode: BudgetMode) -> str:
    return "claude-haiku-4-5-20251001" if budget_mode == BudgetMode.LOW else "claude-sonnet-4-6"


def answer(question: str, budget_mode: BudgetMode) -> dict:
    q = question.lower()
    engine = get_engine()

    # SOTA listing: "list papers that claim state-of-the-art" / "which papers claim sota"
    if any(p in q for p in ["state of the art", "state-of-the-art", "sota", "claim sota", "claims sota"]) \
            and any(p in q for p in ["list", "which", "papers", "report", "claim"]):
        sql = """
            SELECT DISTINCT p.id, p.title, p.year, br.benchmark_name, br.metric_name, br.value
            FROM benchmark_results br
            JOIN papers p ON p.id = br.paper_id
            WHERE br.is_sota_claim = 1
              AND br.value IS NOT NULL
            ORDER BY br.benchmark_name, br.value DESC
        """
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
        if not rows:
            return {
                "answer": "No papers with explicit SOTA claims were found in the structured database.",
                "evidence": [],
            }
        answer_lines = [f"Papers claiming state-of-the-art ({len(rows)} result(s)):"]
        evidence = []
        seen = set()
        for r in rows:
            paper_id, title, year, bench, metric, val = r
            year_str = str(year) if year else "n.d."
            answer_lines.append(f"  • {title} ({year_str}): {bench} {metric} = {val:.1f}%")
            if paper_id not in seen:
                seen.add(paper_id)
                evidence.append({"paper_id": paper_id, "title": title, "year": year or "",
                                  "section": "results", "quote": f"{bench} {metric}: {val:.1f}% (SOTA claim)"})
        return {"answer": "\n".join(answer_lines), "evidence": evidence[:15]}

    # Find pairs of papers with same benchmark but notably different values
    sql = """
        SELECT
            r1.paper_id AS p1_id,
            r2.paper_id AS p2_id,
            r1.benchmark_name,
            r1.metric_name,
            r1.value AS v1,
            r2.value AS v2,
            r1.training_conditions AS tc1,
            r2.training_conditions AS tc2,
            r1.year AS y1,
            r2.year AS y2
        FROM benchmark_results r1
        JOIN benchmark_results r2
            ON r1.benchmark_name = r2.benchmark_name
            AND r1.metric_name = r2.metric_name
            AND r1.paper_id < r2.paper_id
        WHERE r1.value IS NOT NULL AND r2.value IS NOT NULL
          AND ABS(r1.value - r2.value) > 1.0
        ORDER BY ABS(r1.value - r2.value) DESC
        LIMIT 30
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()

    if not rows:
        return {
            "answer": "No conflicting benchmark results found in the structured database. "
                      "The papers may use different benchmarks that aren't directly comparable.",
            "evidence": [],
        }

    # Fetch titles
    with get_session() as session:
        comparisons = []
        evidence = []
        seen_pairs = set()
        for r in rows[:15]:
            pair_key = (r[0], r[1], r[2])
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            p1 = session.get(Paper, r[0])
            p2 = session.get(Paper, r[1])
            if not p1 or not p2:
                continue
            comparisons.append(
                f"- {p1.title} ({r[8]}): {r[2]} {r[3]} = {r[4]:.1f}% [{r[6]}]\n"
                f"  vs {p2.title} ({r[9]}): {r[2]} {r[3]} = {r[5]:.1f}% [{r[7]}]"
            )
            evidence.append({"paper_id": p1.id, "title": p1.title, "year": p1.year, "section": "results",
                              "quote": f"{r[2]} {r[3]}: {r[4]:.1f}%"})
            evidence.append({"paper_id": p2.id, "title": p2.title, "year": p2.year, "section": "results",
                              "quote": f"{r[2]} {r[3]}: {r[5]:.1f}%"})

    if not comparisons:
        return {"answer": "Could not retrieve paper details for comparison.", "evidence": []}

    comparison_text = "\n".join(comparisons[:10])
    model = _model(budget_mode)
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = (
        f"Question: {question}\n\n"
        f"Benchmark result differences found in corpus:\n{comparison_text}\n\n"
        "Identify genuine conflicts (same benchmark, different conditions or contradictory claims). "
        "Explain which differences represent real contradictions vs. expected variation (different training conditions, model variants). "
        "Be concise and cite specific papers."
    )
    resp = client.messages.create(model=model, max_tokens=600,
                                   messages=[{"role": "user", "content": prompt}])
    usage = resp.usage
    cached = getattr(usage, "cache_read_input_tokens", 0) or 0
    tracker.record(model, usage.input_tokens, usage.output_tokens, cached_tokens=cached, tier=3)

    return {"answer": resp.content[0].text.strip(), "evidence": evidence[:10]}
