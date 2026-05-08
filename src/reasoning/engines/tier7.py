"""Tier 7: Negation/absence — SQL set subtraction + standard benchmark list."""
import re
from sqlalchemy import text
from src.config import BudgetMode
from src.knowledge.store import get_engine
from src.knowledge.resolver import STANDARD_VIT_BENCHMARKS


def answer(question: str, budget_mode: BudgetMode) -> dict:
    q = question.lower()
    engine = get_engine()

    # "Which benchmark is absent/missing from the corpus?"
    if any(w in q for w in ["absent", "missing", "conspicuously", "not covered", "not used benchmark"]):
        sql = "SELECT DISTINCT LOWER(benchmark_name) FROM benchmark_results"
        with engine.connect() as conn:
            used = {r[0] for r in conn.execute(text(sql)).fetchall()}

        absent = [b for b in STANDARD_VIT_BENCHMARKS if b.lower() not in used]
        if absent:
            answer_text = (
                f"Standard Vision Transformer benchmarks conspicuously absent from the corpus:\n"
                + "\n".join(f"  • {b}" for b in absent)
            )
        else:
            answer_text = "All standard ViT benchmarks appear to be represented in the corpus."
        return {
            "answer": answer_text,
            "data": {"absent_benchmarks": absent, "used_benchmarks": list(used)},
            "evidence": [{"paper_id": "corpus", "title": "Corpus-wide benchmark analysis",
                          "section": "benchmark_results", "quote": f"{len(used)} unique benchmarks found"}],
        }

    # "Papers that don't use X" / "papers without neural networks"
    if any(w in q for w in ["don't use", "do not use", "not use", "without using"]):
        # Extract what they're NOT using
        from src.knowledge.resolver import normalize_dataset, DATASET_SIZES_K

        # Check if it's about datasets
        target_dataset = None
        for ds in list(DATASET_SIZES_K.keys()) + ["ImageNet", "COCO"]:
            if ds.lower() in q:
                target_dataset = normalize_dataset(ds)
                break

        if target_dataset:
            sql = """
                SELECT id, title, year FROM papers
                WHERE id NOT IN (
                    SELECT DISTINCT paper_id FROM dataset_uses WHERE dataset_name = :name
                )
                ORDER BY citation_count DESC
            """
            with engine.connect() as conn:
                rows = conn.execute(text(sql), {"name": target_dataset}).fetchall()
            papers = [{"paper_id": r[0], "title": r[1], "year": r[2]} for r in rows]
            answer_text = f"Papers in the corpus that do NOT use {target_dataset} ({len(papers)} papers):\n"
            for p in papers[:10]:
                answer_text += f"  • {p['title']} ({p['year']})\n"
            if len(papers) > 10:
                answer_text += f"  ... and {len(papers) - 10} more."
            evidence = [{"paper_id": p["paper_id"], "title": p["title"], "year": p["year"],
                         "section": "dataset_facts", "quote": f"Does not use {target_dataset}"} for p in papers[:10]]
            return {"answer": answer_text.strip(), "data": papers, "evidence": evidence}

        # Neural networks check
        if "neural" in q:
            sql = """
                SELECT id, title, year FROM papers
                WHERE id NOT IN (
                    SELECT DISTINCT paper_id FROM model_facts
                    WHERE architecture_type IN ('transformer', 'cnn', 'hybrid')
                )
                ORDER BY citation_count DESC
            """
            with engine.connect() as conn:
                rows = conn.execute(text(sql)).fetchall()
            papers = [{"paper_id": r[0], "title": r[1], "year": r[2]} for r in rows]
            if not papers:
                return {"answer": "All papers in the corpus appear to use neural network architectures.", "evidence": []}
            answer_text = f"Papers possibly not using standard neural networks ({len(papers)}):\n"
            for p in papers[:10]:
                answer_text += f"  • {p['title']} ({p['year']})\n"
            return {"answer": answer_text.strip(), "evidence": []}

    # "Papers without augmentation"
    if "augmentation" in q or "augment" in q:
        sql = """
            SELECT DISTINCT p.id, p.title, p.year
            FROM papers p
            LEFT JOIN dataset_uses du ON du.paper_id = p.id AND du.uses_augmentation = 1
            WHERE du.paper_id IS NULL
            ORDER BY p.citation_count DESC
        """
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
        papers = [{"paper_id": r[0], "title": r[1], "year": r[2]} for r in rows]
        answer_text = f"Papers where data augmentation was not reported ({len(papers)}):\n"
        for p in papers[:10]:
            answer_text += f"  • {p['title']} ({p['year']})\n"
        return {"answer": answer_text.strip(), "evidence": []}

    # "Papers that do not evaluate on X benchmark"
    if any(p in q for p in ["not evaluate", "do not evaluate", "don't evaluate", "no imagenet"]):
        if "imagenet" in q:
            sql = """
                SELECT DISTINCT p.id, p.title, p.year FROM papers p
                WHERE p.id NOT IN (
                    SELECT DISTINCT paper_id FROM benchmark_results
                    WHERE LOWER(benchmark_name) LIKE '%imagenet%'
                )
                ORDER BY p.citation_count DESC
            """
            with engine.connect() as conn:
                rows = conn.execute(text(sql)).fetchall()
            papers = [{"paper_id": r[0], "title": r[1], "year": r[2]} for r in rows]
            n = len(papers)
            answer_text = f"Papers in the corpus that do NOT evaluate on ImageNet ({n} papers):\n"
            for p in papers[:15]:
                answer_text += f"  • {p['title']} ({p['year']})\n"
            if n > 15:
                answer_text += f"  ... and {n - 15} more."
            evidence = [{"paper_id": p["paper_id"], "title": p["title"], "year": p["year"],
                         "section": "benchmark_results", "quote": "Not evaluated on ImageNet"}
                        for p in papers[:10]]
            return {"answer": answer_text.strip(), "evidence": evidence}

    # "Papers that never report parameter counts"
    if any(p in q for p in ["never report", "not report", "without reporting", "no parameter count", "don't report"]):
        if any(w in q for w in ["parameter", "param"]):
            sql = """
                SELECT DISTINCT p.id, p.title, p.year FROM papers p
                WHERE p.id NOT IN (
                    SELECT DISTINCT paper_id FROM model_facts
                    WHERE param_count_millions IS NOT NULL
                )
                ORDER BY p.citation_count DESC
            """
            with engine.connect() as conn:
                rows = conn.execute(text(sql)).fetchall()
            papers = [{"paper_id": r[0], "title": r[1], "year": r[2]} for r in rows]
            n = len(papers)
            answer_text = f"Papers that never report parameter counts for their proposed models ({n} papers):\n"
            for p in papers[:15]:
                answer_text += f"  • {p['title']} ({p['year']})\n"
            if n > 15:
                answer_text += f"  ... and {n - 15} more."
            return {"answer": answer_text.strip(), "evidence": []}

    # Fallback: use T1 retrieval
    from src.reasoning.engines.tier1 import answer as t1_answer
    result = t1_answer(question, budget_mode)
    return result
