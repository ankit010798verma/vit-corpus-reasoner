"""Build ChromaDB (semantic), BM25 (keyword), and NetworkX (citation graph) indexes."""
import pickle
from pathlib import Path

import chromadb
import networkx as nx
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from src.config import settings
from src.knowledge.models import Chunk, Paper, CitationEdge
from src.knowledge.store import get_session

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
COLLECTION_NAME = "corpus_chunks"

_chroma_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None
_embedder: SentenceTransformer | None = None
_bm25: BM25Okapi | None = None
_bm25_chunk_ids: list[str] = []
_citation_graph: nx.DiGraph | None = None
_pagerank: dict[str, float] = {}


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


def build_chroma_index() -> None:
    """Embed all chunks and store in ChromaDB."""
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.chroma_dir))

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    embedder = _get_embedder()

    with get_session() as session:
        chunks = session.query(Chunk).filter(Chunk.chunk_type != "table").all()
        chunk_data = [(c.id, c.text, c.paper_id, c.section) for c in chunks]

    batch_size = 128
    for i in tqdm(range(0, len(chunk_data), batch_size), desc="Embedding chunks"):
        batch = chunk_data[i : i + batch_size]
        ids, texts, paper_ids, sections = zip(*batch)
        embeddings = embedder.encode(list(texts), normalize_embeddings=True).tolist()
        collection.add(
            ids=list(ids),
            embeddings=embeddings,
            documents=list(texts),
            metadatas=[{"paper_id": p, "section": s} for p, s in zip(paper_ids, sections)],
        )

    print(f"ChromaDB: indexed {len(chunk_data)} chunks.")


def build_bm25_index() -> None:
    """Build BM25 index over all chunk texts."""
    settings.bm25_path.parent.mkdir(parents=True, exist_ok=True)

    with get_session() as session:
        chunks = session.query(Chunk).all()
        chunk_ids = [c.id for c in chunks]
        tokenized = [c.text.lower().split() for c in chunks]

    bm25 = BM25Okapi(tokenized)
    with open(settings.bm25_path, "wb") as f:
        pickle.dump({"bm25": bm25, "chunk_ids": chunk_ids}, f)
    print(f"BM25: indexed {len(chunk_ids)} chunks.")


def build_citation_graph() -> None:
    """Load citation edges from SQLite into a NetworkX DiGraph and compute PageRank."""
    graph_path = settings.data_dir / "citation_graph.pkl"
    graph_path.parent.mkdir(parents=True, exist_ok=True)

    with get_session() as session:
        edges = session.query(CitationEdge).all()
        edge_data = [(e.citer_id, e.cited_id) for e in edges]
        papers = session.query(Paper).all()
        paper_ids = [p.id for p in papers]

    G = nx.DiGraph()
    G.add_nodes_from(paper_ids)
    G.add_edges_from(edge_data)

    pr = nx.pagerank(G, alpha=0.85) if G.number_of_edges() > 0 else {p: 1.0 for p in paper_ids}

    with open(graph_path, "wb") as f:
        pickle.dump({"graph": G, "pagerank": pr}, f)

    print(f"Citation graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")


def load_indexes() -> None:
    """Load all pre-built indexes into memory."""
    global _chroma_client, _collection, _bm25, _bm25_chunk_ids, _citation_graph, _pagerank

    # ChromaDB
    _chroma_client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    _collection = _chroma_client.get_collection(COLLECTION_NAME)

    # BM25
    if settings.bm25_path.exists():
        with open(settings.bm25_path, "rb") as f:
            data = pickle.load(f)
        _bm25 = data["bm25"]
        _bm25_chunk_ids = data["chunk_ids"]

    # Citation graph
    graph_path = settings.data_dir / "citation_graph.pkl"
    if graph_path.exists():
        with open(graph_path, "rb") as f:
            data = pickle.load(f)
        _citation_graph = data["graph"]
        _pagerank = data["pagerank"]


def get_collection() -> chromadb.Collection:
    if _collection is None:
        raise RuntimeError("Indexes not loaded. Call load_indexes() first.")
    return _collection


def get_bm25() -> tuple[BM25Okapi, list[str]]:
    if _bm25 is None:
        raise RuntimeError("BM25 index not loaded.")
    return _bm25, _bm25_chunk_ids


def get_citation_graph() -> tuple[nx.DiGraph, dict[str, float]]:
    if _citation_graph is None:
        raise RuntimeError("Citation graph not loaded.")
    return _citation_graph, _pagerank
