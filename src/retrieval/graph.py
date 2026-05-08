"""Citation graph queries using NetworkX: PageRank, BFS, neighborhood."""
import networkx as nx
from src.knowledge.indexer import get_citation_graph
from src.knowledge.models import Paper
from src.knowledge.store import get_session


def _paper_title(paper_id: str) -> str:
    with get_session() as session:
        p = session.get(Paper, paper_id)
        return p.title if p else paper_id


def most_cited_in_corpus(top_n: int = 10) -> list[dict]:
    """Return papers sorted by inner-corpus PageRank (proxy for most cited within corpus)."""
    G, pr = get_citation_graph()
    # Also count in-degree (direct citation count within corpus)
    in_degree = dict(G.in_degree())
    ranked = sorted(pr.keys(), key=lambda pid: (in_degree.get(pid, 0), pr.get(pid, 0)), reverse=True)

    with get_session() as session:
        result = []
        for pid in ranked[:top_n]:
            p = session.get(Paper, pid)
            if p:
                result.append({
                    "paper_id": pid,
                    "title": p.title,
                    "year": p.year,
                    "in_corpus_citations": in_degree.get(pid, 0),
                    "pagerank": round(pr.get(pid, 0), 6),
                    "global_citation_count": p.citation_count,
                })
    return result


def citation_chain(from_id: str, to_id: str) -> list[dict] | None:
    """Find shortest citation chain from from_id to to_id. Returns None if no path."""
    G, _ = get_citation_graph()
    try:
        path = nx.shortest_path(G, source=from_id, target=to_id)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None

    with get_session() as session:
        result = []
        for pid in path:
            p = session.get(Paper, pid)
            result.append({
                "paper_id": pid,
                "title": p.title if p else pid,
                "year": p.year if (p and p.year is not None) else "",
            })
        return result


def papers_building_on(paper_id: str) -> list[dict]:
    """Return corpus papers that directly cite paper_id."""
    G, _ = get_citation_graph()
    citers = list(G.predecessors(paper_id))

    with get_session() as session:
        result = []
        for pid in citers:
            p = session.get(Paper, pid)
            if p:
                result.append({"paper_id": pid, "title": p.title, "year": p.year})
    return result


def get_top_cited_paper_id() -> str | None:
    """Return paper_id of the most in-corpus-cited paper."""
    top = most_cited_in_corpus(top_n=1)
    return top[0]["paper_id"] if top else None
