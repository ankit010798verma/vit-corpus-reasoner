"""Fetch top-100 most-cited Vision Transformer papers from Semantic Scholar and download PDFs."""
import csv
import json
import time
import random
from pathlib import Path

import httpx
from tqdm import tqdm

from src.config import settings

SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"
ARXIV_PDF_URL = "https://arxiv.org/pdf/{arxiv_id}.pdf"

FIELDS = "title,authors,year,venue,citationCount,externalIds,openAccessPdf,abstract"


def _headers() -> dict:
    h = {"User-Agent": "vit-corpus-reasoner/0.1 (research project)"}
    if settings.semantic_scholar_api_key:
        h["x-api-key"] = settings.semantic_scholar_api_key
    return h


def _get_with_retry(client: httpx.Client, url: str, params: dict, max_retries: int = 5) -> dict:
    """GET with exponential backoff on 429/5xx."""
    for attempt in range(max_retries):
        try:
            resp = client.get(url, params=params)
            if resp.status_code == 429:
                wait = 2 ** attempt * 10  # 10s, 20s, 40s...
                print(f"  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt * 5)
    return {}


def fetch_top_papers(query: str = "vision transformer", n: int = 100) -> list[dict]:
    """Query Semantic Scholar for top-cited papers. Fetches 3× candidates, sorts by citation count."""
    papers = []
    # Semantic Scholar search doesn't support sort by citations — fetch more and sort client-side
    fetch_queries = [
        "vision transformer image recognition",
        "ViT vision transformer",
        "transformer architecture image classification",
    ]
    offset = 0
    limit = 100

    with httpx.Client(timeout=60, headers=_headers()) as client:
        for q in fetch_queries:
            for page in range(3):  # up to 3 pages per query
                data = _get_with_retry(
                    client,
                    f"{SEMANTIC_SCHOLAR_BASE}/paper/search",
                    {
                        "query": q,
                        "limit": limit,
                        "offset": page * limit,
                        "fields": FIELDS,
                    },
                )
                batch = data.get("data", [])
                if not batch:
                    break
                papers.extend(batch)
                time.sleep(3)  # conservative rate limiting for unauthenticated access
                if len(papers) >= n * 3:
                    break
            if len(papers) >= n * 3:
                break

    # Deduplicate by arxiv_id, then by title
    seen_arxiv, seen_titles, unique = set(), set(), []
    for p in papers:
        arxiv_id = (p.get("externalIds") or {}).get("ArXiv", "")
        title_key = p.get("title", "").lower().strip()
        if not title_key:
            continue
        if arxiv_id and arxiv_id in seen_arxiv:
            continue
        if title_key in seen_titles:
            continue
        if arxiv_id:
            seen_arxiv.add(arxiv_id)
        seen_titles.add(title_key)
        unique.append(p)

    # Sort by citation count descending and take top n
    unique.sort(key=lambda p: p.get("citationCount", 0) or 0, reverse=True)
    return unique[:n]


def fetch_inner_corpus_citations(paper_ids: list[str]) -> list[tuple[str, str, str]]:
    """Return (citer_id, cited_id, context) for citations between corpus papers."""
    corpus_set = set(paper_ids)
    edges = []
    with httpx.Client(timeout=60, headers=_headers()) as client:
        for paper_id in tqdm(paper_ids, desc="Fetching citation edges"):
            try:
                data = _get_with_retry(
                    client,
                    f"{SEMANTIC_SCHOLAR_BASE}/paper/{paper_id}/references",
                    {"fields": "paperId,title,contexts", "limit": 500},
                )
                refs = data.get("data") or []
                for ref in refs:
                    cited = ref.get("citedPaper", {})
                    cited_id = cited.get("paperId", "")
                    if cited_id and cited_id in corpus_set:
                        context = ref.get("contexts", [""])[0] if ref.get("contexts") else ""
                        edges.append((paper_id, cited_id, context))
                time.sleep(2)  # conservative rate limiting
            except Exception as e:
                print(f"  Warning: citation fetch failed for {paper_id}: {e}")
    return edges


def download_pdf(paper: dict, out_dir: Path) -> str | None:
    """Download paper PDF; returns local path or None if unavailable."""
    paper_id = paper["paperId"]
    arxiv_id = (paper.get("externalIds") or {}).get("ArXiv", "")
    open_access = paper.get("openAccessPdf") or {}
    oa_url = open_access.get("url", "")

    dest = out_dir / f"{paper_id}.pdf"
    if dest.exists() and dest.stat().st_size > 10_000:
        return str(dest)

    urls_to_try = []
    if arxiv_id:
        urls_to_try.append(ARXIV_PDF_URL.format(arxiv_id=arxiv_id))
    if oa_url:
        urls_to_try.append(oa_url)

    for url in urls_to_try:
        try:
            with httpx.Client(timeout=60, follow_redirects=True) as client:
                resp = client.get(url, headers={"User-Agent": "vit-corpus-reasoner/0.1"})
                if resp.status_code == 200 and len(resp.content) > 10_000:
                    dest.write_bytes(resp.content)
                    return str(dest)
        except Exception:
            pass
        time.sleep(random.uniform(0.5, 1.5))

    return None


def build_manifest(papers: list[dict], pdf_paths: dict[str, str | None]) -> None:
    """Write manifest.csv to corpus directory."""
    settings.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["id", "title", "authors", "year", "venue", "citation_count", "source_url", "arxiv_id", "pdf_path", "abstract"]
    with open(settings.manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in papers:
            authors = [a.get("name", "") for a in (p.get("authors") or [])]
            arxiv_id = (p.get("externalIds") or {}).get("ArXiv", "")
            oa = p.get("openAccessPdf") or {}
            writer.writerow({
                "id": p["paperId"],
                "title": p.get("title", ""),
                "authors": "; ".join(authors),
                "year": p.get("year", ""),
                "venue": p.get("venue", ""),
                "citation_count": p.get("citationCount", 0) or 0,
                "source_url": oa.get("url", "") or (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""),
                "arxiv_id": arxiv_id,
                "pdf_path": pdf_paths.get(p["paperId"], "") or "",
                "abstract": (p.get("abstract") or "").replace("\n", " "),
            })


def assemble(n: int = 100) -> list[dict]:
    """Full pipeline: fetch → download PDFs → write manifest. Returns paper list."""
    settings.pdfs_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching top {n} Vision Transformer papers from Semantic Scholar...")
    papers = fetch_top_papers(n=n)
    print(f"Found {len(papers)} unique papers.")

    print("Downloading PDFs...")
    pdf_paths = {}
    for paper in tqdm(papers, desc="Downloading"):
        path = download_pdf(paper, settings.pdfs_dir)
        pdf_paths[paper["paperId"]] = path
        time.sleep(0.3)

    downloaded = sum(1 for v in pdf_paths.values() if v)
    print(f"Downloaded {downloaded}/{len(papers)} PDFs.")

    build_manifest(papers, pdf_paths)
    print(f"Manifest written to {settings.manifest_path}")

    return papers
