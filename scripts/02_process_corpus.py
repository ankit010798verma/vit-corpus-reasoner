#!/usr/bin/env python3
"""Step 2: Ingest PDFs into SQLite (chunks + structured fact extraction)."""
import csv
import sys
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.knowledge.store import init_db, get_session
from src.knowledge.models import Paper
from src.corpus.ingestion import ingest_paper
from src.knowledge.extractor import extract_paper_facts


def load_manifest() -> list[dict]:
    rows = []
    with open(settings.manifest_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


if __name__ == "__main__":
    init_db(settings.db_path)

    manifest = load_manifest()
    print(f"Processing {len(manifest)} papers...")

    # Insert paper metadata
    with get_session() as session:
        for row in manifest:
            existing = session.get(Paper, row["id"])
            if not existing:
                session.add(Paper(
                    id=row["id"],
                    arxiv_id=row.get("arxiv_id", ""),
                    title=row["title"],
                    authors_json=row["authors"],
                    year=int(row["year"]) if row.get("year") else None,
                    venue=row.get("venue", ""),
                    citation_count=int(row.get("citation_count", 0) or 0),
                    source_url=row.get("source_url", ""),
                    pdf_path=row.get("pdf_path", ""),
                    abstract=row.get("abstract", ""),
                ))

    # Ingest PDFs + extract facts
    for row in tqdm(manifest, desc="Ingesting"):
        pdf_path = row.get("pdf_path", "")
        if not pdf_path or not Path(pdf_path).exists():
            print(f"  Skipping {row['title'][:50]}: no PDF")
            continue

        year = int(row["year"]) if row.get("year") else 2020
        n_chunks = ingest_paper(row["id"], pdf_path)
        if n_chunks > 0:
            extract_paper_facts(row["id"], year)

    print("\nDone. Run scripts/03_build_index.py next.")
