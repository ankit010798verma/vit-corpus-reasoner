"""Hybrid BM25 + semantic retrieval with Reciprocal Rank Fusion (RRF)."""
from dataclasses import dataclass

from src.knowledge.indexer import get_collection, get_bm25
from src.knowledge.models import Chunk
from src.knowledge.store import get_session


@dataclass
class RetrievedChunk:
    chunk_id: str
    paper_id: str
    section: str
    text: str
    score: float


def _rrf_score(ranks: list[int], k: int = 60) -> float:
    return sum(1.0 / (k + r) for r in ranks)


def retrieve(
    query: str,
    top_k: int = 10,
    use_semantic: bool = True,
    use_bm25: bool = True,
    paper_id_filter: str | None = None,
) -> list[RetrievedChunk]:
    """Hybrid retrieval: BM25 + semantic, fused via RRF."""
    bm25_scores: dict[str, float] = {}
    semantic_scores: dict[str, float] = {}

    if use_bm25:
        bm25, chunk_ids = get_bm25()
        tokens = query.lower().split()
        scores = bm25.get_scores(tokens)
        indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        for rank, (idx, score) in enumerate(indexed[:top_k * 2]):
            cid = chunk_ids[idx]
            bm25_scores[cid] = rank + 1

    if use_semantic:
        from src.knowledge.indexer import _get_embedder
        embedder = _get_embedder()
        collection = get_collection()
        query_emb = embedder.encode(query, normalize_embeddings=True).tolist()
        where = {"paper_id": paper_id_filter} if paper_id_filter else None
        results = collection.query(
            query_embeddings=[query_emb],
            n_results=min(top_k * 2, collection.count()),
            where=where,
        )
        ids = results["ids"][0] if results["ids"] else []
        for rank, cid in enumerate(ids):
            semantic_scores[cid] = rank + 1

    # RRF fusion
    all_ids = set(bm25_scores) | set(semantic_scores)
    rrf: dict[str, float] = {}
    for cid in all_ids:
        ranks = []
        if cid in bm25_scores:
            ranks.append(bm25_scores[cid])
        if cid in semantic_scores:
            ranks.append(semantic_scores[cid])
        rrf[cid] = _rrf_score(ranks)

    top_ids = sorted(rrf, key=lambda c: rrf[c], reverse=True)[:top_k]

    # Fetch chunk data — extract all fields inside the session to avoid DetachedInstanceError
    with get_session() as session:
        chunks = session.query(Chunk).filter(Chunk.id.in_(top_ids)).all()
        chunk_map = {c.id: (c.paper_id, c.section, c.text) for c in chunks}

    result = []
    for cid in top_ids:
        row = chunk_map.get(cid)
        if row is None:
            continue
        paper_id, section, text = row
        if paper_id_filter and paper_id != paper_id_filter:
            continue
        result.append(RetrievedChunk(
            chunk_id=cid,
            paper_id=paper_id,
            section=section,
            text=text,
            score=rrf[cid],
        ))
    return result
