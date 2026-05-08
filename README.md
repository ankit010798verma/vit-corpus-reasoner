# VIT Corpus Reasoner

A research comprehension system for the top 100 most-cited Vision Transformer papers. Answers all 8 tiers of natural-language questions with cited, defensible answers.

## Algorithm

This system is **not generic RAG**. It builds a Claim-Evidence Knowledge Graph (CEKG) — a typed relational database of structured facts extracted from each paper — and routes each query to a specialized reasoning engine:

| Tier | Engine | LLM cost |
|------|--------|----------|
| T1 Single-doc factual | Hybrid retrieval (BM25 + semantic) → LLM extract | Haiku |
| T2 Corpus aggregation | SQL `GROUP BY / COUNT / AVG` | **$0** |
| T3 Contradiction | SQL finds divergent benchmarks → Sonnet narrates | Sonnet |
| T4 Temporal | SQL `ORDER BY year` → Sonnet trend | Sonnet |
| T5 Citation graph | NetworkX PageRank / BFS / shortest_path | **$0** |
| T6 Multi-hop | Chain T1/T2/T5 sub-queries → Sonnet | Sonnet |
| T7 Negation | SQL set subtraction + standard benchmark list | Haiku |
| T8 Quantitative | SQL → pandas `sum() / corr() / median()` | **$0** |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Corpus Path

PDFs are **not stored in git** (too large). `corpus/manifest.csv` is committed and contains the full paper list with arXiv IDs and open-access URLs for all 100 papers. Run step 1 below to download them locally.

- 66/100 papers download automatically from arXiv or open-access URLs
- 34/100 are behind publisher paywalls and will be skipped (the system still works with 66 papers)
- Papers are saved to `corpus/pdfs/<paper_id>.pdf`

## Build Steps (run in order)

```bash
# 1. Download PDFs for the 100 papers in corpus/manifest.csv (free, ~10 min)
python scripts/01_assemble_corpus.py

# 2. Extract text chunks + structured facts via LLM (needs API key, ~$1.50)
python scripts/02_process_corpus.py

# 3. Build ChromaDB + BM25 + citation graph indexes (free, ~5 min)
python scripts/03_build_index.py

# 4. Run evaluation at 3 budget levels + generate budget curve
python scripts/04_run_evaluation.py

# 5. Generate human-readable eval report (eval/results/eval_report.md)
python scripts/05_generate_report.py
```

## Run the API

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

## Query Examples

```bash
# Single-doc factual (Tier 1)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What patch size does ViT use?", "budget_mode": "medium"}'

# Corpus aggregation (Tier 2) — zero LLM cost
curl -X POST http://localhost:8000/query \
  -d '{"question": "List all datasets used across the 100 papers", "budget_mode": "low"}'

# Citation graph (Tier 5) — zero LLM cost
curl -X POST http://localhost:8000/query \
  -d '{"question": "Which paper is most cited by other corpus papers?", "budget_mode": "low"}'

# Quantitative (Tier 8) — zero LLM cost
curl -X POST http://localhost:8000/query \
  -d '{"question": "What is the sum of all transformer model parameter counts?", "budget_mode": "low"}'
```

## Budget Modes

| Mode | Strategy | Target cost per query |
|------|----------|----------------------|
| `low` | BM25 only + Haiku | ~$0.02 |
| `medium` | BM25 + semantic + mixed models | ~$0.07 |
| `high` | Full pipeline + Sonnet for complex | ~$0.25 |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/query` | Ask a question (`{question, budget_mode}`) |
| GET | `/papers` | List all corpus papers |
| GET | `/papers/{id}` | Paper details + chunks |
| POST | `/evaluate` | Run 40-question evaluation set |
| GET | `/costs` | Session cost report |
| GET | `/corpus/stats` | Index stats (papers, chunks, facts) |
| GET | `/health` | Index load status |

## Cost Report

```bash
curl http://localhost:8000/costs
```

Returns total USD spent, breakdown by model and tier, and per-question statistics (mean/median/max per question).

## Evaluation Results

Pre-run results are in `eval/results/`:

| File | Description |
|------|-------------|
| `eval_report.md` | Human-readable Q/gold/output/score table for all 40 questions |
| `budget_curve.png` | Quality-vs-cost curve across LOW/MEDIUM/HIGH |
| `eval_high_*.json` | Raw JSON with per-question costs, latencies, scores |

Latest results (HIGH budget mode): **40.3% accuracy**, $0.31 total, mean $0.0078/question.

Regenerate after a new eval run:
```bash
python scripts/05_generate_report.py
```
