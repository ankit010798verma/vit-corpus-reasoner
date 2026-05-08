#!/usr/bin/env python3
"""Step 1: Fetch top-100 ViT papers and download PDFs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.corpus.assembler import assemble

if __name__ == "__main__":
    papers = assemble(n=100)
    print(f"\nDone. {len(papers)} papers in manifest.")
