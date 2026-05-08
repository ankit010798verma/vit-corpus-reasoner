"""Tier 5: Citation-graph reasoning — NetworkX algorithms, zero LLM cost."""
import re
from src.retrieval.graph import most_cited_in_corpus, citation_chain, papers_building_on, get_top_cited_paper_id
from src.query.paper_resolver import find_paper_id
from src.knowledge.models import Paper
from src.knowledge.store import get_session

# Short abbreviation → title fragment for fuzzy lookup (3-char names fail regex in paper_resolver)
_ABBREV_TITLE = {
    "mae": "Masked Autoencoders Are Scalable",
    "vit": "An Image is Worth 16x16",
    "deit": "Training data-efficient image transformers",
    "dino": "Emerging Properties in Self-Supervised",
    "beit": "BERT Pre-Training of Image",
    "swin": "Swin Transformer",
    "clip": "Learning Transferable Visual",
    "detr": "End-to-End Object Detection",
}


def _resolve_paper(mention: str) -> str | None:
    """Resolve paper mention to paper_id, trying abbreviation map first."""
    title_frag = _ABBREV_TITLE.get(mention.lower())
    pid = find_paper_id(title_frag) if title_frag else None
    return pid or find_paper_id(mention)


def answer(question: str, budget_mode=None) -> dict:
    q = question.lower()

    if any(p in q for p in ["most cited", "most influential", "highest cited"]):
        results = most_cited_in_corpus(top_n=5)
        if not results:
            return {"answer": "Citation graph data not available.", "evidence": []}
        top = results[0]
        answer_text = (
            f"The most cited paper within the corpus is:\n"
            f"'{top['title']}' ({top['year']}) — cited by {top['in_corpus_citations']} other corpus papers.\n\n"
            f"Top 5 most cited:\n"
        )
        for r in results:
            answer_text += f"  • {r['title']} ({r['year']}): {r['in_corpus_citations']} inner-corpus citations\n"
        evidence = [{"paper_id": r["paper_id"], "title": r["title"], "year": r["year"],
                     "section": "citation_graph", "quote": f"{r['in_corpus_citations']} inner-corpus citations"} for r in results]
        return {"answer": answer_text.strip(), "evidence": evidence}

    if any(p in q for p in ["citation chain", "citation path", "path from", "path between"]) or \
       ("from" in q and "to" in q and any(p in q for p in ["path", "chain", "route"])):
        # Extract known paper abbreviations and full names
        known = ["MAE", "ViT", "DeiT", "DINO", "BEiT", "Swin", "CLIP", "MoCo", "DETR",
                 "Masked Autoencoders", "Image is Worth", "Swin Transformer"]
        candidates = []
        for name in known:
            if name.lower() in q:
                candidates.append(name)
        ids = []
        for mention in candidates[:2]:
            pid = _resolve_paper(mention)
            if pid and pid not in ids:
                ids.append(pid)
        # Also try generic paper mention extraction
        if len(ids) < 2:
            paper_mentions = re.findall(r'(?:the\s+)?([A-Z][A-Za-z0-9\s-]{2,40}?)\s+paper', question)
            for mention in paper_mentions:
                pid = _resolve_paper(mention.strip())
                if pid and pid not in ids:
                    ids.append(pid)
        if len(ids) >= 2:
            chain = citation_chain(ids[0], ids[1])
            if chain:
                chain_str = " → ".join(f"'{p['title']}'" for p in chain)
                return {
                    "answer": f"Citation chain: {chain_str}",
                    "evidence": [{"paper_id": p["paper_id"], "title": p["title"], "year": "", "section": "citation_graph", "quote": ""} for p in chain],
                }
            else:
                with get_session() as session:
                    p1 = session.get(Paper, ids[0])
                    p2 = session.get(Paper, ids[1])
                    t1 = p1.title if p1 else ids[0]
                    t2 = p2.title if p2 else ids[1]
                return {"answer": f"No direct citation path found from '{t1}' to '{t2}' within the corpus.", "evidence": []}

    if "builds" in q or "build on" in q or "based on" in q:
        pid = find_paper_id(question)
        if pid:
            builders = papers_building_on(pid)
            with get_session() as session:
                src = session.get(Paper, pid)
                src_title = src.title if src else pid
            if builders:
                answer_text = f"Papers that directly cite '{src_title}':\n"
                for b in builders:
                    answer_text += f"  • {b['title']} ({b['year']})\n"
                return {"answer": answer_text.strip(), "evidence": builders}
            else:
                return {"answer": f"No corpus papers were found to directly cite '{src_title}'.", "evidence": []}

    if any(p in q for p in ["most isolated", "fewest citations", "least cited", "lowest cited",
                             "cited by the fewest", "fewest other", "not cited"]):
        results = most_cited_in_corpus(top_n=200)
        if not results:
            return {"answer": "Citation graph data not available.", "evidence": []}
        bottom = sorted(results, key=lambda r: r["in_corpus_citations"])[:10]
        zero = [r for r in bottom if r["in_corpus_citations"] == 0]
        display = zero if zero else bottom
        answer_text = "Papers cited by the fewest other corpus papers (most isolated):\n"
        for r in display:
            answer_text += f"  • {r['title']} ({r['year']}): {r['in_corpus_citations']} inner-corpus citations\n"
        evidence = [{"paper_id": r["paper_id"], "title": r["title"], "year": r["year"],
                     "section": "citation_graph", "quote": f"{r['in_corpus_citations']} inner-corpus citations"}
                    for r in display]
        return {"answer": answer_text.strip(), "evidence": evidence}

    # Default: return top cited papers (call directly to avoid recursion)
    results = most_cited_in_corpus(top_n=5)
    if not results:
        return {"answer": "Citation graph data not available.", "evidence": []}
    top = results[0]
    answer_text = (
        f"The most cited paper within the corpus is:\n"
        f"'{top['title']}' ({top['year']}) — cited by {top['in_corpus_citations']} other corpus papers.\n\n"
        f"Top 5 most cited:\n"
    )
    for r in results:
        answer_text += f"  • {r['title']} ({r['year']}): {r['in_corpus_citations']} inner-corpus citations\n"
    evidence = [{"paper_id": r["paper_id"], "title": r["title"], "year": r["year"],
                 "section": "citation_graph", "quote": f"{r['in_corpus_citations']} inner-corpus citations"} for r in results]
    return {"answer": answer_text.strip(), "evidence": evidence}
