"""Tier 6: Multi-hop/compositional — chain sub-queries via T1/T2/T5, Sonnet synthesizes."""
import anthropic
from src.config import settings, BudgetMode
from src.cost.tracker import tracker
from src.retrieval.graph import get_top_cited_paper_id
from src.knowledge.models import Paper, DatasetUse
from src.knowledge.store import get_session
from sqlalchemy import text, bindparam
from src.knowledge.store import get_engine


def _model(budget_mode: BudgetMode) -> str:
    return "claude-haiku-4-5-20251001" if budget_mode == BudgetMode.LOW else "claude-sonnet-4-6"


def _get_paper_datasets(paper_id: str) -> list[str]:
    with get_session() as session:
        rows = session.query(DatasetUse.dataset_name).filter(DatasetUse.paper_id == paper_id).all()
    return [r[0] for r in rows]


def _papers_using_dataset(dataset_name: str) -> list[dict]:
    engine = get_engine()
    sql = """
        SELECT DISTINCT p.id, p.title, p.year
        FROM dataset_uses du JOIN papers p ON p.id = du.paper_id
        WHERE du.dataset_name = :name
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql), {"name": dataset_name}).fetchall()
    return [{"paper_id": r[0], "title": r[1], "year": r[2]} for r in rows]


def _papers_using_dataset_without_augmentation(dataset_name: str) -> list[dict]:
    engine = get_engine()
    sql = """
        SELECT DISTINCT p.id, p.title, p.year
        FROM dataset_uses du JOIN papers p ON p.id = du.paper_id
        WHERE du.dataset_name = :name
          AND (du.uses_augmentation = 0 OR du.uses_augmentation IS NULL)
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql), {"name": dataset_name}).fetchall()
    return [{"paper_id": r[0], "title": r[1], "year": r[2]} for r in rows]


def answer(question: str, budget_mode: BudgetMode) -> dict:
    q = question.lower()
    evidence = []
    sub_results = {}

    # Pattern: "highest/most-cited paper ... datasets ... which other papers also use"
    if ("highest" in q or "most cited" in q or "most-cited" in q) and "dataset" in q:
        top_id = get_top_cited_paper_id()
        if not top_id:
            return {"answer": "Citation graph not available.", "evidence": []}

        with get_session() as session:
            top_paper = session.get(Paper, top_id)
            top_paper_title = top_paper.title if top_paper else top_id
            top_paper_year = top_paper.year if top_paper else None
        datasets = _get_paper_datasets(top_id)

        if not datasets:
            return {
                "answer": f"The most-cited corpus paper is '{top_paper_title}' but no datasets were extracted from it.",
                "evidence": [{"paper_id": top_id, "title": top_paper_title, "year": top_paper_year,
                               "section": "citation_graph", "quote": "Most cited paper"}],
            }

        sub_results["top_paper"] = top_paper_title
        sub_results["top_paper_datasets"] = datasets
        sub_results["papers_by_dataset"] = {}
        for ds in datasets:
            papers = _papers_using_dataset(ds)
            sub_results["papers_by_dataset"][ds] = [p for p in papers if p["paper_id"] != top_id]
            for p in papers:
                evidence.append({"paper_id": p["paper_id"], "title": p["title"], "year": p["year"],
                                  "section": "dataset_facts", "quote": f"Uses {ds}"})

    # Pattern: "among papers using X, which [condition]"
    elif "among papers" in q or ("papers" in q and "using" in q and "which" in q):
        from src.knowledge.resolver import DATASET_SIZES_K, normalize_dataset
        # Find dataset mentioned
        target_dataset = None
        for ds in list(DATASET_SIZES_K.keys()) + ["ImageNet", "COCO", "ADE20K"]:
            if ds.lower() in q:
                target_dataset = ds
                break

        if not target_dataset:
            # Fall back to T1-style answer
            from src.reasoning.engines.tier1 import answer as t1_answer
            return t1_answer(question, budget_mode)

        if "augmentation" in q or "augment" in q:
            papers = _papers_using_dataset_without_augmentation(target_dataset)
            sub_results["dataset"] = target_dataset
            sub_results["no_augmentation_papers"] = papers
        else:
            papers = _papers_using_dataset(target_dataset)
            sub_results["dataset"] = target_dataset
            sub_results["papers_using"] = papers
        evidence = [{"paper_id": p["paper_id"], "title": p["title"], "year": p["year"],
                     "section": "dataset_facts", "quote": f"Uses {target_dataset}"} for p in papers]

    # Pattern: "papers that cite X also evaluate on Y" / "cite X and evaluate on Y"
    elif ("cite" in q or "cites" in q) and ("evaluat" in q or "report" in q or "detect" in q):
        from src.query.paper_resolver import find_paper_id
        from src.retrieval.graph import get_citation_graph
        # Find the cited paper
        source_id = find_paper_id(question)
        if source_id:
            G, _ = get_citation_graph()
            citing_ids = list(G.predecessors(source_id)) if source_id in G else []
            # Find dataset/benchmark mentioned
            benchmark = None
            for ds in ["COCO", "ADE20K", "ImageNet", "Cityscapes", "Kinetics"]:
                if ds.lower() in q:
                    benchmark = ds
                    break
            if benchmark and citing_ids:
                engine = get_engine()
                sql = """
                    SELECT DISTINCT p.id, p.title, p.year, br.value, br.metric_name
                    FROM papers p
                    JOIN benchmark_results br ON br.paper_id = p.id
                    WHERE p.id IN :ids
                      AND br.benchmark_name LIKE :bench
                    ORDER BY br.value DESC
                """
                with engine.connect() as conn:
                    rows = conn.execute(
                        text(sql).bindparams(bindparam("ids", expanding=True)),
                        {"ids": list(citing_ids), "bench": f"%{benchmark}%"},
                    ).fetchall()
                if rows:
                    papers_list = [{"paper_id": r[0], "title": r[1], "year": r[2], "value": r[3], "metric": r[4]} for r in rows]
                    sub_results["citing_papers_with_benchmark"] = papers_list
                    sub_results["benchmark_filter"] = benchmark
                    for r in rows:
                        evidence.append({"paper_id": r[0], "title": r[1], "year": r[2],
                                         "section": "benchmark_results", "quote": f"{benchmark}: {r[3]}"})
                else:
                    return {"answer": f"No corpus papers found that both cite the referenced paper and evaluate on {benchmark}.", "evidence": []}
            elif citing_ids:
                with get_session() as session:
                    papers = session.query(Paper).filter(Paper.id.in_(citing_ids[:20])).all()
                    papers_list = [{"paper_id": p.id, "title": p.title, "year": p.year} for p in papers]
                sub_results["citing_papers"] = papers_list
                evidence = [{"paper_id": p["paper_id"], "title": p["title"], "year": p["year"],
                              "section": "citation_graph", "quote": "Cites referenced paper"} for p in papers_list]
        else:
            from src.reasoning.engines.tier1 import answer as t1_answer
            return t1_answer(question, budget_mode)

    # Pattern: "among papers with accuracy > X, what dataset / training strategy"
    elif ("accuracy" in q or "top-1" in q) and ("%" in q or re.search(r"\d+\s*%|\d+\.\d+", q)):
        import re as _re
        threshold_match = _re.search(r"(\d+(?:\.\d+)?)\s*%?", q)
        threshold = float(threshold_match.group(1)) if threshold_match else 80.0
        sql = """
            SELECT DISTINCT p.id, p.title, p.year
            FROM papers p
            JOIN benchmark_results br ON br.paper_id = p.id
            WHERE br.benchmark_name LIKE '%ImageNet%'
              AND br.metric_name LIKE '%Top-1%'
              AND br.value > :thresh
        """
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(text(sql), {"thresh": threshold}).fetchall()
        if not rows:
            return {"answer": f"No papers found with ImageNet Top-1 accuracy above {threshold}%.", "evidence": []}
        paper_ids_filter = [r[0] for r in rows]
        # Get training datasets for these papers
        sql2 = """
            SELECT dataset_name, COUNT(DISTINCT paper_id) as cnt
            FROM dataset_uses
            WHERE paper_id IN :ids AND use_type IN ('pretraining','training')
            GROUP BY dataset_name ORDER BY cnt DESC LIMIT 10
        """
        with engine.connect() as conn:
            ds_rows = conn.execute(
                text(sql2).bindparams(bindparam("ids", expanding=True)),
                {"ids": paper_ids_filter},
            ).fetchall()
        sub_results["papers_above_threshold"] = len(paper_ids_filter)
        sub_results["threshold"] = threshold
        sub_results["top_training_datasets"] = [{"dataset": r[0], "count": r[1]} for r in ds_rows]
        evidence = [{"paper_id": r[0], "title": r[1], "year": r[2], "section": "benchmark_results",
                     "quote": f"ImageNet Top-1 > {threshold}%"} for r in rows[:10]]

    else:
        # General multi-hop: use Sonnet to plan and execute
        from src.reasoning.engines.tier1 import answer as t1_answer
        return t1_answer(question, budget_mode)

    # Synthesize with LLM
    model = _model(budget_mode)
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    import json
    context = json.dumps(sub_results, indent=2, default=str)[:4000]
    prompt = (
        f"Question: {question}\n\n"
        f"Retrieved facts:\n{context}\n\n"
        "Provide a comprehensive, well-organized answer to the question based on these facts."
    )
    resp = client.messages.create(model=model, max_tokens=600,
                                   messages=[{"role": "user", "content": prompt}])
    usage = resp.usage
    cached = getattr(usage, "cache_read_input_tokens", 0) or 0
    tracker.record(model, usage.input_tokens, usage.output_tokens, cached_tokens=cached, tier=6)

    return {"answer": resp.content[0].text.strip(), "evidence": evidence[:15]}
