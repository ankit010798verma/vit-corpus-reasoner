"""Tier 2: Corpus-level aggregation — deterministic SQL queries, zero LLM cost."""
import re
from sqlalchemy import text
from src.knowledge.store import get_session, get_engine


def _detect_subtype(question: str) -> str:
    q = question.lower()
    # Count queries take priority over dataset/benchmark classification
    if ("how many papers" in q or "count" in q) and any(w in q for w in ["report", "use", "on", "results"]):
        return "paper_count"
    if any(w in q for w in ["metric", "evaluation metric", "measure"]):
        return "metrics"
    if any(w in q for w in ["benchmark"]):
        return "benchmarks"
    if any(w in q for w in ["parameter", "param", "model size"]):
        return "model_sizes"
    if any(w in q for w in ["venue", "conference", "journal"]):
        return "venues"
    if any(w in q for w in ["author"]):
        return "authors"
    if any(w in q for w in ["year", "time"]):
        return "years"
    if any(w in q for w in ["dataset", "data"]):
        return "datasets"
    return "datasets"  # default


def answer(question: str, budget_mode=None) -> dict:
    subtype = _detect_subtype(question)
    engine = get_engine()

    if subtype == "paper_count":
        # "How many papers report results on X?"
        q = question.lower()
        # Extract benchmark/dataset name from question
        from src.knowledge.resolver import STANDARD_VIT_BENCHMARKS, DATASET_ALIASES
        target = None
        for name in STANDARD_VIT_BENCHMARKS + list(set(DATASET_ALIASES.values())):
            if name.lower() in q:
                target = name
                break
        if target:
            sql = """
                SELECT COUNT(DISTINCT paper_id) FROM benchmark_results
                WHERE benchmark_name LIKE :name
            """
            with engine.connect() as conn:
                count = conn.execute(text(sql), {"name": f"%{target}%"}).scalar() or 0
            return {
                "answer": f"{count} papers in the corpus report results on {target}.",
                "data": {"count": count, "benchmark": target},
                "evidence": _corpus_evidence(),
            }
        # Fallback to datasets list
        subtype = "datasets"

    if subtype == "datasets":
        sql = """
            SELECT dataset_name, COUNT(DISTINCT paper_id) as paper_count
            FROM dataset_uses
            GROUP BY dataset_name
            ORDER BY paper_count DESC
        """
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
        items = [{"dataset": r[0], "papers_using": r[1]} for r in rows]
        answer_text = f"Found {len(items)} unique datasets across the corpus:\n"
        for item in items[:20]:
            answer_text += f"  • {item['dataset']}: {item['papers_using']} paper(s)\n"
        if len(items) > 20:
            answer_text += f"  ... and {len(items) - 20} more."
        return {"answer": answer_text.strip(), "data": items, "evidence": _corpus_evidence()}

    elif subtype == "model_sizes":
        sql = """
            SELECT p.year, mf.param_count_millions
            FROM model_facts mf
            JOIN papers p ON p.id = mf.paper_id
            WHERE mf.param_count_millions IS NOT NULL
        """
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
        if not rows:
            return {"answer": "No parameter count data found in the corpus.", "evidence": []}
        values = [r[1] for r in rows]
        values.sort()
        n = len(values)
        median = values[n // 2]
        mean = sum(values) / n
        answer_text = (
            f"Model size statistics across {n} reported models:\n"
            f"  Median: {median:.1f}M parameters\n"
            f"  Mean: {mean:.1f}M parameters\n"
            f"  Min: {min(values):.1f}M, Max: {max(values):.1f}M"
        )
        return {"answer": answer_text, "data": {"median": median, "mean": mean, "values": values}, "evidence": _corpus_evidence()}

    elif subtype in ("metrics", "benchmarks"):
        sql = """
            SELECT benchmark_name, metric_name, COUNT(DISTINCT paper_id) as count
            FROM benchmark_results
            GROUP BY benchmark_name, metric_name
            ORDER BY count DESC
        """
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
        items = [{"benchmark": r[0], "metric": r[1], "paper_count": r[2]} for r in rows]
        answer_text = f"Evaluation benchmarks and metrics used across the corpus:\n"
        for item in items[:20]:
            answer_text += f"  • {item['benchmark']} / {item['metric']}: {item['paper_count']} paper(s)\n"
        return {"answer": answer_text.strip(), "data": items, "evidence": _corpus_evidence()}

    elif subtype == "venues":
        sql = """
            SELECT venue, COUNT(*) as count FROM papers
            WHERE venue IS NOT NULL AND venue != ''
            GROUP BY venue ORDER BY count DESC LIMIT 20
        """
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
        items = [{"venue": r[0], "count": r[1]} for r in rows]
        answer_text = "Publication venues:\n" + "\n".join(f"  • {r['venue']}: {r['count']} papers" for r in items)
        return {"answer": answer_text, "data": items, "evidence": _corpus_evidence()}

    elif subtype == "authors":
        import json
        sql = "SELECT authors_json FROM papers WHERE authors_json IS NOT NULL AND authors_json != ''"
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
        author_counts: dict[str, int] = {}
        for (authors_json,) in rows:
            try:
                authors = json.loads(authors_json) if isinstance(authors_json, str) else authors_json
                for a in (authors if isinstance(authors, list) else []):
                    name = a.get("name", a) if isinstance(a, dict) else str(a)
                    author_counts[name] = author_counts.get(name, 0) + 1
            except Exception:
                continue
        top = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        answer_text = f"Most frequent authors across {len(rows)} corpus papers:\n"
        for name, count in top:
            answer_text += f"  • {name}: {count} paper(s)\n"
        return {"answer": answer_text.strip(), "data": [{"author": n, "count": c} for n, c in top],
                "evidence": _corpus_evidence()}

    elif subtype == "years":
        sql = """
            SELECT year, COUNT(*) as count FROM papers
            WHERE year IS NOT NULL
            GROUP BY year ORDER BY year
        """
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
        if not rows:
            return {"answer": "No year data found in the corpus.", "evidence": []}
        items = [{"year": r[0], "count": r[1]} for r in rows]
        answer_text = "Publications per year:\n" + "\n".join(f"  • {r['year']}: {r['count']} paper(s)" for r in items)
        return {"answer": answer_text, "data": items, "evidence": _corpus_evidence()}

    else:
        return {"answer": "Aggregation type not recognized.", "evidence": []}


def _corpus_evidence() -> list[dict]:
    return [{"paper_id": "corpus", "title": "Entire corpus (100 papers)", "section": "metadata", "quote": "Computed from structured database."}]
