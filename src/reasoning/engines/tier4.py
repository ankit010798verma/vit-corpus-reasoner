"""Tier 4: Temporal/evolution — SQL time series + Sonnet trend analysis."""
import re
import anthropic
from sqlalchemy import text
from src.config import settings, BudgetMode
from src.cost.tracker import tracker
from src.knowledge.store import get_engine


def _model(budget_mode: BudgetMode) -> str:
    return "claude-haiku-4-5-20251001" if budget_mode == BudgetMode.LOW else "claude-sonnet-4-6"


def answer(question: str, budget_mode: BudgetMode) -> dict:
    engine = get_engine()
    q = question.lower()

    # Detect year range from question
    years = re.findall(r"\b(20\d{2})\b", question)

    if any(w in q for w in ["parameter", "param", "model size"]):
        sql = """
            SELECT p.year, AVG(mf.param_count_millions) as avg_params, COUNT(*) as n
            FROM model_facts mf JOIN papers p ON p.id = mf.paper_id
            WHERE mf.param_count_millions IS NOT NULL
            GROUP BY p.year ORDER BY p.year
        """
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
        if not rows:
            return {"answer": "No parameter count data found across years.", "evidence": []}
        data_text = "Year | Avg Parameters (M) | Count\n"
        data_text += "\n".join(f"{r[0]} | {r[1]:.1f}M | {r[2]} papers" for r in rows)
        evidence_type = "parameter evolution"

    elif any(w in q for w in ["benchmark", "performance", "accuracy", "sota"]):
        benchmark_hint = ""
        for bench in ["imagenet", "coco", "ade20k"]:
            if bench in q:
                benchmark_hint = bench.capitalize()
                break
        sql_params = {}
        if benchmark_hint:
            sql = """
                SELECT r.year, r.benchmark_name, AVG(r.value) as avg_val, COUNT(*) as n
                FROM benchmark_results r
                WHERE LOWER(r.benchmark_name) LIKE :bench
                GROUP BY r.year, r.benchmark_name ORDER BY r.year
            """
            sql_params["bench"] = f"%{benchmark_hint.lower()}%"
        else:
            sql = """
                SELECT r.year, r.benchmark_name, AVG(r.value) as avg_val, COUNT(*) as n
                FROM benchmark_results r
                GROUP BY r.year, r.benchmark_name ORDER BY r.year, r.benchmark_name
            """
        with engine.connect() as conn:
            rows = conn.execute(text(sql), sql_params).fetchall()
        if not rows:
            return {"answer": "No benchmark result data found across years.", "evidence": []}
        data_text = "Year | Benchmark | Avg Value | Count\n"
        data_text += "\n".join(f"{r[0]} | {r[1]} | {r[2]:.2f} | {r[3]} papers" for r in rows[:30])
        evidence_type = "benchmark evolution"

    elif any(w in q for w in ["dataset", "data"]):
        sql = """
            SELECT p.year, du.dataset_name, COUNT(DISTINCT du.paper_id) as n
            FROM dataset_uses du JOIN papers p ON p.id = du.paper_id
            GROUP BY p.year, du.dataset_name ORDER BY p.year, n DESC
        """
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
        if not rows:
            return {"answer": "No dataset usage data found across years.", "evidence": []}
        data_text = "Year | Dataset | Papers Using\n"
        data_text += "\n".join(f"{r[0]} | {r[1]} | {r[2]}" for r in rows[:30])
        evidence_type = "dataset usage evolution"

    else:
        sql = """
            SELECT year, COUNT(*) as n, AVG(citation_count) as avg_citations
            FROM papers GROUP BY year ORDER BY year
        """
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
        if not rows:
            return {"answer": "No publication data found across years.", "evidence": []}
        data_text = "Year | Papers | Avg Citations\n"
        data_text += "\n".join(f"{r[0]} | {r[1]} | {r[2]:.0f}" for r in rows)
        evidence_type = "publication trend"

    model = _model(budget_mode)
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    prompt = (
        f"Question: {question}\n\n"
        f"Temporal data ({evidence_type}) from 100 Vision Transformer papers:\n{data_text}\n\n"
        "Describe the trend or evolution shown in the data. Be specific with numbers and years."
    )
    resp = client.messages.create(model=model, max_tokens=500,
                                   messages=[{"role": "user", "content": prompt}])
    usage = resp.usage
    cached = getattr(usage, "cache_read_input_tokens", 0) or 0
    tracker.record(model, usage.input_tokens, usage.output_tokens, cached_tokens=cached, tier=4)

    return {
        "answer": resp.content[0].text.strip(),
        "data": data_text,
        "evidence": [{"paper_id": "corpus", "title": "Corpus-wide temporal analysis", "section": "metadata",
                      "quote": f"Aggregated {evidence_type} data"}],
    }
