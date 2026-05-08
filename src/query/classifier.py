"""Tier classification: rule-based first (zero cost), Haiku fallback for ambiguous queries."""
import re
import json

TIER_PATTERNS: dict[int, list[str]] = {
    1: [
        r"\bwhat\s+(architecture|method|dataset|approach|model|loss|training|technique|does\s+paper)\b",
        r"\bin\s+paper\b.{0,50}\bwhat\b",
        r"\bwhat\s+does\s+\w+\s+(?:paper|et\s+al|propose|use)\b",
        r"\bhow\s+does\s+.{0,30}work\b",
        r"\bdescribe\s+the\s+(architecture|method|approach)\b",
    ],
    2: [
        r"\blist\s+(all|every|each)\b",
        r"\bacross\s+(all|the)\s+(?:100\s+)?papers\b",
        r"\bhow\s+many\s+papers\b",
        r"\bmost\s+(common|frequent|used|popular)\b",
        r"\bdeduplic\b|\bunique\s+dataset\b",
        r"\bwhich\s+(metric|benchmark|dataset)\s+is\s+most\b",
    ],
    3: [
        r"\bconflict(ing|s)?\b|\bcontradict(ing|s|ion|ions)?\b|\bdiverge\b",
        r"\b(vs\.?|versus)\b.{0,50}\b(paper|result)\b",
        r"\bcompare\b.{0,60}\bpaper\b",
        r"\bclaim\s+s(ota|tate.of.the.art)\b|\breport\s+s(ota|tate.of.the.art)\b",
        r"\bstate.of.the.art\b.{0,60}\bpaper\b",
        r"\bdisagree\b|\binconsistent\b",
        r"\blist\s+papers?.{0,40}\bclaim\b",
    ],
    4: [
        r"\bover\s+(time|the\s+years?)\b",
        r"\bfrom\s+\d{4}\s+to\s+\d{4}\b",
        r"\btrend\b|\bevolution\b|\bgrow\b|\bchange\b.{0,30}\byear\b",
        r"\bchronolog\b",
        r"\bhow\s+has\b.{0,60}\b(changed|grown|evolved)\b",
        r"\b\d{4}\s+versus\s+\d{4}\b",
    ],
    5: [
        r"\bmost\s+cited\s+(by|within|in)\b",
        r"\bmost\s+influential.{0,40}\bcorpus\b",
        r"\bcitation\s+(chain|path)\b",
        r"\bpath\s+from\b.{0,40}\bto\b",
        r"\bbuilds?\s+(directly\s+)?on\b",
        r"\bcites\b.{0,40}\bpaper\b",
        r"\bwhich\s+paper.{0,30}\bcited\s+by\s+other\b",
        r"\btop\s+\d+\s+(most\s+)?(cited|influential)\b",
    ],
    6: [
        r"\bwhich\s+papers?.{0,80}\balso\b",
        r"\bamong\s+papers?\s+(using|that\s+use|reporting|that\s+report|with)\b",
        r"\bhighest[- ]cited.{0,40}\buse\b",
        r"\bpapers?\s+that\s+(cite|use).{0,60}\balso\b",
        r"\bwhat\s+datasets?\s+does.{0,40}\band\s+which\b",
        r"\bpapers?\s+that\s+(cite|use).{0,40}\band.{0,40}(evaluat|use|report)\b",
    ],
    7: [
        r"\bnot\s+use[sd]?\b|\bdon.t\s+use\b|\bwithout\s+using\b",
        r"\babsent\b|\bconspicuously\s+absent\b|\bmissing\s+(from|across)\b",
        r"\bnever\s+use[sd]?\b|\bdo\s+not\s+use\b",
        r"\bwhich\s+(benchmark|dataset).{0,50}\b(absent|not|never)\b",
        r"\bpapers?\s+that\s+don.t\b|\bpapers?\s+without\b",
        r"\b(benchmark|dataset).{0,40}\bnot\s+(used|appear)\b",
        r"\bnever\s+report\b|\bnot\s+report\b",
    ],
    8: [
        r"\bsum\b.{0,50}\b(parameter|param)\b",
        r"\btotal\s+(parameter|param)\b",
        r"\bcorrelation\s+between\b",
        r"\bhow\s+many\s+(?:total\s+)?parameters\b",
        r"\bmedian\b.{0,50}\b(parameter|param|accuracy|top-1)\b",
        r"\baverage\b.{0,50}\b(accuracy|top-1|imagenet).{0,30}\b(paper|model|claim)\b",
        r"\bmean\b.{0,50}\b(accuracy|parameter|param)\b",
        r"\bsum\s+(?:all|the)\s+\w+\s+(count|size)\b",
    ],
}


def classify_tier_rules(question: str) -> int | None:
    """Fast rule-based classification. Returns tier 1-8 or None if ambiguous."""
    q = question.lower()
    # Score each tier
    scores: dict[int, int] = {}
    for tier, patterns in TIER_PATTERNS.items():
        hits = sum(1 for p in patterns if re.search(p, q))
        if hits > 0:
            scores[tier] = hits

    if not scores:
        return None
    # Resolve ties by preferring higher tiers (harder questions)
    best_tier = max(scores, key=lambda t: (scores[t], t))
    return best_tier


def classify_tier_llm(question: str) -> int:
    """Haiku fallback: classify tier when rules are ambiguous. ~$0.001/call."""
    import anthropic
    from src.config import settings
    from src.cost.tracker import tracker

    if not settings.anthropic_api_key:
        return 1  # default to single-doc factual when no key

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    system = (
        "Classify this research QA question into one of 8 tiers:\n"
        "1=single-doc factual, 2=corpus aggregation, 3=comparative/contradiction, "
        "4=temporal/evolution, 5=citation-graph, 6=multi-hop/compositional, "
        "7=negation/absence, 8=quantitative computation.\n"
        "Reply with ONLY the tier number (1-8)."
    )
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    usage = resp.usage
    tracker.record("claude-haiku-4-5-20251001", usage.input_tokens, usage.output_tokens)
    try:
        return int(resp.content[0].text.strip()[0])
    except (ValueError, IndexError):
        return 1  # default to T1


def classify(question: str) -> int:
    tier = classify_tier_rules(question)
    if tier is None:
        tier = classify_tier_llm(question)
    return tier
