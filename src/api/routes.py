import csv
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from src.api.schemas import QueryRequest, QueryResponse, EvalRequest, CostReport, Citation
from src.config import settings
from src.cost.tracker import tracker
from src.knowledge.store import get_session, get_engine
from src.knowledge.models import Paper, Chunk
from src.query.router import ask

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest):
    try:
        result = ask(req.question, req.budget_mode)
        citations = [Citation(**c) for c in result.citations]
        return QueryResponse(
            answer=result.answer,
            citations=citations,
            tier=result.tier,
            cost_usd=result.cost_usd,
            reasoning_trace=result.reasoning_trace,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers")
def list_papers():
    with get_session() as session:
        papers = session.query(Paper).order_by(Paper.citation_count.desc()).all()
        return [
            {
                "id": p.id,
                "title": p.title,
                "authors": p.authors_json,
                "year": p.year,
                "venue": p.venue,
                "citation_count": p.citation_count,
                "source_url": p.source_url,
            }
            for p in papers
        ]


@router.get("/papers/{paper_id}")
def get_paper(paper_id: str):
    with get_session() as session:
        p = session.get(Paper, paper_id)
        if not p:
            raise HTTPException(status_code=404, detail="Paper not found")
        chunks = session.query(Chunk).filter(Chunk.paper_id == paper_id).limit(50).all()
        return {
            "id": p.id,
            "title": p.title,
            "authors": p.authors_json,
            "year": p.year,
            "venue": p.venue,
            "citation_count": p.citation_count,
            "source_url": p.source_url,
            "abstract": p.abstract,
            "chunks": [{"section": c.section, "text": c.text[:500]} for c in chunks],
        }


@router.post("/evaluate")
def run_evaluation(req: EvalRequest):
    from src.evaluation.runner import run_eval
    from pathlib import Path
    try:
        result = run_eval(req.budget_mode, Path("./eval/results"))
        return result["summary"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs", response_model=CostReport)
def get_costs():
    report = tracker.report()
    return CostReport(
        total_usd=report["total_usd"],
        by_model=report["by_model"],
        by_tier={str(k): v for k, v in report["by_tier"].items()},
        per_question=report["per_question"],
        call_count=report["call_count"],
    )


@router.get("/corpus/stats")
def corpus_stats():
    engine = get_engine()
    if engine is None:
        return {"error": "Database not initialized"}
    with engine.connect() as conn:
        n_papers = conn.execute(text("SELECT COUNT(*) FROM papers")).scalar()
        n_chunks = conn.execute(text("SELECT COUNT(*) FROM chunks")).scalar()
        n_model_facts = conn.execute(text("SELECT COUNT(*) FROM model_facts")).scalar()
        n_dataset_uses = conn.execute(text("SELECT COUNT(*) FROM dataset_uses")).scalar()
        n_benchmarks = conn.execute(text("SELECT COUNT(*) FROM benchmark_results")).scalar()
        n_citations = conn.execute(text("SELECT COUNT(*) FROM citation_edges")).scalar()
    return {
        "papers": n_papers,
        "chunks": n_chunks,
        "model_facts": n_model_facts,
        "dataset_uses": n_dataset_uses,
        "benchmark_results": n_benchmarks,
        "citation_edges": n_citations,
    }


@router.get("/health")
def health():
    from src.knowledge.indexer import _collection, _bm25, _citation_graph
    return {
        "status": "ok",
        "chroma_loaded": _collection is not None,
        "bm25_loaded": _bm25 is not None,
        "graph_loaded": _citation_graph is not None,
    }
