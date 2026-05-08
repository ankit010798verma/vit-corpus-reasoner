#!/usr/bin/env python3
"""Step 3: Build ChromaDB (semantic), BM25 (keyword), and citation graph indexes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.knowledge.store import init_db
from src.knowledge.indexer import build_chroma_index, build_bm25_index, build_citation_graph
from src.corpus.assembler import fetch_inner_corpus_citations
from src.knowledge.models import Paper, CitationEdge
from src.knowledge.store import get_session


def store_citation_edges(edges: list[tuple]) -> None:
    """Store (citer_id, cited_id, context) tuples in SQLite."""
    with get_session() as session:
        # Get valid paper IDs
        paper_ids = {p.id for p in session.query(Paper.id).all()}
        existing = {(e.citer_id, e.cited_id) for e in session.query(CitationEdge).all()}
        added = 0
        for citer_id, cited_id, context in edges:
            if citer_id in paper_ids and cited_id in paper_ids and (citer_id, cited_id) not in existing:
                session.add(CitationEdge(citer_id=citer_id, cited_id=cited_id, context_text=context))
                existing.add((citer_id, cited_id))
                added += 1
    print(f"Stored {added} new citation edges.")


if __name__ == "__main__":
    init_db(settings.db_path)

    # Fetch inner-corpus citation graph from Semantic Scholar
    print("Fetching inner-corpus citation edges from Semantic Scholar...")
    with get_session() as session:
        paper_ids = [p.id for p in session.query(Paper).all()]
    edges = fetch_inner_corpus_citations(paper_ids)
    store_citation_edges(edges)

    print("\nBuilding ChromaDB semantic index...")
    build_chroma_index()

    print("\nBuilding BM25 keyword index...")
    build_bm25_index()

    print("\nBuilding citation graph...")
    build_citation_graph()

    print("\nAll indexes built. Run the API with: uvicorn src.api.main:app --reload")
