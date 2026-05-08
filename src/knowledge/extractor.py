"""Two-pass LLM extraction of structured facts from each paper using Haiku with prompt caching."""
import json
import re
from typing import Any

import anthropic

from src.config import settings
from src.cost.tracker import tracker
from src.knowledge.models import ModelFact, DatasetUse, BenchmarkResult, MethodClaim, Chunk
from src.knowledge.store import get_session
from src.knowledge.resolver import normalize_dataset, normalize_benchmark, get_dataset_size_k

MODEL = "claude-haiku-4-5-20251001"

PASS1_SYSTEM = """You extract structured facts from Vision Transformer research paper sections.
Return ONLY valid JSON with these keys:
{
  "benchmark_results": [
    {"benchmark": str, "metric": str, "value": float, "is_sota_claim": bool, "training_conditions": str}
  ],
  "datasets_used": [
    {"name": str, "use_type": str, "uses_augmentation": bool|null, "dataset_size_k_samples": float|null}
  ]
}
- benchmark: e.g. "ImageNet", "COCO", "ADE20K"
- metric: e.g. "Top-1 Accuracy", "mAP", "mIoU"
- value: numeric, e.g. 81.3 (for 81.3%)
- training_conditions: brief string, e.g. "pretrained ImageNet-21K, finetuned 1K" or ""
- use_type: one of pretraining|training|finetuning|evaluation
- dataset_size_k_samples: thousands of samples if stated, else null
If nothing found, return empty lists. No extra text."""

PASS2_SYSTEM = """You extract structured facts from Vision Transformer research paper sections.
Return ONLY valid JSON with these keys:
{
  "model_facts": [
    {"model_name": str, "param_count_millions": float|null, "architecture_type": str, "training_dataset": str}
  ],
  "method_claims": [
    {"method_name": str, "claim_type": str, "description": str}
  ]
}
- architecture_type: one of transformer|cnn|hybrid|other
- claim_type: one of novel|improvement|sota|ablation|negative
- param_count_millions: total parameters in millions if stated, else null
If nothing found, return empty lists. No extra text."""


def _call_haiku(system: str, text: str, paper_id: str, tier: int | None = None) -> dict:
    """Call Haiku with prompt caching on the system prompt."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    try:
        resp = client.beta.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},  # cache system prompt
                }
            ],
            messages=[{"role": "user", "content": text[:12000]}],  # safety truncation
            betas=["prompt-caching-2024-07-31"],
        )
        usage = resp.usage
        cached = getattr(usage, "cache_read_input_tokens", 0) or 0
        tracker.record(
            model=MODEL,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cached_tokens=cached,
            tier=tier,
            question_id=paper_id,
        )
        raw = resp.content[0].text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except (json.JSONDecodeError, Exception) as e:
        return {}


def _get_section_text(chunks: list, sections: list[str]) -> str:
    matching = [c for c in chunks if c.section in sections and c.chunk_type == "text"]
    return " ".join(c.text for c in matching)[:8000]


def _regex_fallback_datasets(chunks: list, paper_id: str) -> list[dict]:
    """Regex scan for known dataset names to catch LLM misses."""
    from src.knowledge.resolver import DATASET_ALIASES, DATASET_SIZES_K
    all_text = " ".join(c.text for c in chunks).lower()

    found = {}
    known_names = set(DATASET_ALIASES.values()) | set(DATASET_SIZES_K.keys())
    for name in known_names:
        if name.lower() in all_text:
            normalized = normalize_dataset(name)
            if normalized not in found:
                found[normalized] = {
                    "name": normalized,
                    "use_type": "evaluation",
                    "uses_augmentation": None,
                    "dataset_size_k_samples": get_dataset_size_k(normalized),
                }
    return list(found.values())


def extract_paper_facts(paper_id: str, year: int) -> None:
    """Run two-pass extraction and persist results to SQLite."""
    with get_session() as session:
        chunks = session.query(Chunk).filter(Chunk.paper_id == paper_id).all()
        if not chunks:
            return

        # Pass 1: abstract + results → benchmarks + datasets
        pass1_text = _get_section_text(chunks, ["abstract", "results", "experiments"])
        pass1_result = _call_haiku(PASS1_SYSTEM, pass1_text, paper_id) if pass1_text else {}

        # Pass 2: method + introduction → models + claims
        pass2_text = _get_section_text(chunks, ["introduction", "method", "related_work"])
        pass2_result = _call_haiku(PASS2_SYSTEM, pass2_text, paper_id) if pass2_text else {}

        # Clear existing facts for idempotency
        for model in [ModelFact, DatasetUse, BenchmarkResult, MethodClaim]:
            session.query(model).filter(model.paper_id == paper_id).delete()

        # Persist benchmark results
        for br in pass1_result.get("benchmark_results", []):
            try:
                val = float(br.get("value", 0) or 0)
            except (ValueError, TypeError):
                continue
            session.add(BenchmarkResult(
                paper_id=paper_id,
                benchmark_name=normalize_benchmark(str(br.get("benchmark", ""))),
                metric_name=str(br.get("metric", "")),
                value=val,
                is_sota_claim=bool(br.get("is_sota_claim", False)),
                training_conditions=str(br.get("training_conditions", "")),
                year=year,
                raw_text=str(br.get("benchmark", "")) + " " + str(br.get("metric", "")),
            ))

        # Persist dataset uses (LLM + regex union)
        llm_datasets = pass1_result.get("datasets_used", [])
        regex_datasets = _regex_fallback_datasets(chunks, paper_id)

        seen_datasets: set[str] = set()
        for du in llm_datasets + regex_datasets:
            raw_name = str(du.get("name", "")).strip()
            if not raw_name:
                continue
            normalized = normalize_dataset(raw_name)
            if normalized in seen_datasets:
                continue
            seen_datasets.add(normalized)
            # Use known size if LLM didn't provide one
            size = du.get("dataset_size_k_samples")
            if size is None:
                size = get_dataset_size_k(normalized)
            try:
                size_f = float(size) if size is not None else None
            except (ValueError, TypeError):
                size_f = None

            session.add(DatasetUse(
                paper_id=paper_id,
                dataset_name=normalized,
                use_type=str(du.get("use_type", "evaluation")),
                uses_augmentation=du.get("uses_augmentation"),
                dataset_size_k_samples=size_f,
                raw_text=raw_name,
            ))

        # Persist model facts
        for mf in pass2_result.get("model_facts", []):
            param = mf.get("param_count_millions")
            try:
                param_f = float(param) if param is not None else None
            except (ValueError, TypeError):
                param_f = None
            session.add(ModelFact(
                paper_id=paper_id,
                model_name=str(mf.get("model_name", "")),
                param_count_millions=param_f,
                architecture_type=str(mf.get("architecture_type", "transformer")),
                training_dataset=str(mf.get("training_dataset", "")),
                raw_text=str(mf.get("model_name", "")),
            ))

        # Persist method claims
        for mc in pass2_result.get("method_claims", []):
            session.add(MethodClaim(
                paper_id=paper_id,
                method_name=str(mc.get("method_name", "")),
                claim_type=str(mc.get("claim_type", "novel")),
                description=str(mc.get("description", "")),
                raw_text=str(mc.get("method_name", "")),
            ))
