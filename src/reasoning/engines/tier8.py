"""Tier 8: Quantitative computation — SQL → pandas, exact math. Zero LLM cost for pure computation."""
import pandas as pd
from sqlalchemy import text
from src.knowledge.store import get_engine


def answer(question: str, budget_mode=None) -> dict:
    q = question.lower()
    engine = get_engine()

    # Sum of parameter counts
    if any(w in q for w in ["sum", "total"]) and any(w in q for w in ["parameter", "param"]):
        arch_filter = ""
        if "transformer" in q:
            arch_filter = "WHERE architecture_type = 'transformer'"
        elif "cnn" in q:
            arch_filter = "WHERE architecture_type = 'cnn'"

        where_clause = arch_filter if arch_filter else "WHERE param_count_millions IS NOT NULL"
        extra = "AND param_count_millions IS NOT NULL" if arch_filter else ""
        sql = f"""
            SELECT param_count_millions, architecture_type FROM model_facts
            {where_clause}
            {extra}
        """
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()

        if not rows:
            return {"answer": "No parameter count data found.", "evidence": []}

        df = pd.DataFrame(rows, columns=["params", "arch"])
        total = df["params"].sum()
        count = len(df)
        breakdown = df.groupby("arch")["params"].agg(["sum", "mean", "count"]).round(1)

        breakdown_lines = "\n".join(
            f"  • {arch}: {row['sum']:.1f}M total, {row['mean']:.1f}M avg, {int(row['count'])} models"
            for arch, row in breakdown.iterrows()
        )
        answer_text = (
            f"Total parameter count: {total:.1f}M parameters across {count} reported models.\n\n"
            f"Breakdown by architecture:\n{breakdown_lines}"
        )
        return {
            "answer": answer_text,
            "data": {"total_params_millions": round(total, 1), "model_count": count},
            "evidence": [{"paper_id": "corpus", "title": "Corpus-wide parameter sum",
                          "section": "model_facts", "quote": f"{count} models with reported parameter counts"}],
        }

    # Correlation between dataset size and accuracy
    if "correlation" in q and any(w in q for w in ["dataset size", "size", "accuracy", "performance"]):
        sql = """
            SELECT du.dataset_size_k_samples, br.value, p.title
            FROM dataset_uses du
            JOIN papers p ON p.id = du.paper_id
            JOIN benchmark_results br ON br.paper_id = du.paper_id
                AND br.benchmark_name LIKE '%ImageNet%'
            WHERE du.dataset_size_k_samples IS NOT NULL
              AND br.value IS NOT NULL
              AND du.use_type IN ('training', 'pretraining')
        """
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()

        if len(rows) < 3:
            return {
                "answer": "Insufficient data for correlation analysis (need ≥3 data points with both dataset size and accuracy).",
                "evidence": [],
            }

        df = pd.DataFrame(rows, columns=["dataset_size_k", "accuracy", "title"])
        corr = df["dataset_size_k"].corr(df["accuracy"])
        n = len(df)

        answer_text = (
            f"Correlation between training dataset size and ImageNet accuracy:\n"
            f"  Pearson r = {corr:.3f} (n={n} paper-dataset pairs)\n"
            f"  {'Positive' if corr > 0 else 'Negative'} correlation: "
            f"{'larger datasets tend to yield higher accuracy' if corr > 0.3 else 'weak or no clear linear relationship'}."
        )
        return {
            "answer": answer_text,
            "data": {"pearson_r": round(corr, 4), "n": n},
            "evidence": [{"paper_id": "corpus", "title": "Corpus-wide correlation",
                          "section": "computation", "quote": f"r={corr:.3f}"}],
        }

    # Median/mean model size
    if any(w in q for w in ["median", "average", "mean"]) and any(w in q for w in ["parameter", "model size"]):
        sql = "SELECT param_count_millions FROM model_facts WHERE param_count_millions IS NOT NULL"
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
        if not rows:
            return {"answer": "No parameter count data.", "evidence": []}
        df = pd.DataFrame(rows, columns=["params"])
        answer_text = (
            f"Parameter count statistics across {len(df)} models:\n"
            f"  Median: {df['params'].median():.1f}M\n"
            f"  Mean: {df['params'].mean():.1f}M\n"
            f"  Std: {df['params'].std():.1f}M\n"
            f"  Min: {df['params'].min():.1f}M, Max: {df['params'].max():.1f}M"
        )
        return {"answer": answer_text,
                "data": df["params"].describe().round(1).to_dict(),
                "evidence": [{"paper_id": "corpus", "title": "Parameter statistics",
                               "section": "model_facts", "quote": ""}]}

    # Average accuracy for papers using a specific training method
    if any(w in q for w in ["average", "mean"]) and any(w in q for w in ["accuracy", "top-1", "imagenet"]):
        # Determine use_type filter if mentioned
        use_type_filter = ""
        if "self-supervised" in q or "self supervised" in q:
            use_type_filter = "AND du.use_type = 'pretraining'"
        elif "supervised" in q:
            use_type_filter = "AND du.use_type IN ('training', 'finetuning')"

        sql = f"""
            SELECT AVG(br.value), COUNT(DISTINCT br.paper_id)
            FROM benchmark_results br
            {'JOIN dataset_uses du ON du.paper_id = br.paper_id ' + use_type_filter if use_type_filter else ''}
            WHERE br.benchmark_name LIKE '%ImageNet%'
              AND br.metric_name LIKE '%Top-1%'
              AND br.value IS NOT NULL AND br.value > 0
        """
        with engine.connect() as conn:
            row = conn.execute(text(sql)).fetchone()
        if row and row[0]:
            label = "self-supervised" if "self-supervised" in q or "self supervised" in q else "all"
            return {
                "answer": f"Average ImageNet Top-1 accuracy for {label} papers: {row[0]:.1f}% (across {row[1]} papers).",
                "data": {"avg_accuracy": round(row[0], 2), "paper_count": row[1]},
                "evidence": [{"paper_id": "corpus", "title": "Corpus-wide accuracy average",
                               "section": "benchmark_results", "quote": f"avg={row[0]:.1f}%"}],
            }

    # Citation count queries
    if any(w in q for w in ["citation", "cited", "cite"]):
        sql = "SELECT id, title, citation_count, year FROM papers WHERE citation_count IS NOT NULL ORDER BY citation_count DESC"
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
        if rows:
            df = pd.DataFrame(rows, columns=["id", "title", "citations", "year"])
            top = df.iloc[0]
            desc = df["citations"].describe().round(0)
            if any(w in q for w in ["max", "most", "highest", "top"]):
                answer_text = (
                    f"The most cited paper in the corpus is:\n"
                    f"  \"{top['title']}\" ({int(top['year']) if pd.notna(top['year']) else 'N/A'}) — {int(top['citations'])} citations\n\n"
                    f"Corpus-wide citation stats ({len(df)} papers):\n"
                    f"  • Max: {int(desc['max'])}\n"
                    f"  • Mean: {desc['mean']:.0f}\n"
                    f"  • Median: {desc['50%']:.0f}\n"
                    f"  • Min: {int(desc['min'])}"
                )
                evidence_paper = top
                rank_label = "highest in the corpus"
            elif any(w in q for w in ["min", "least", "lowest", "fewest"]):
                bottom = df.iloc[-1]
                answer_text = (
                    f"The least cited paper in the corpus is:\n"
                    f"  \"{bottom['title']}\" ({int(bottom['year']) if pd.notna(bottom['year']) else 'N/A'}) — {int(bottom['citations'])} citations\n\n"
                    f"Corpus-wide citation stats ({len(df)} papers):\n"
                    f"  • Min: {int(desc['min'])}\n"
                    f"  • Mean: {desc['mean']:.0f}\n"
                    f"  • Max: {int(desc['max'])}"
                )
                evidence_paper = bottom
                rank_label = "lowest in the corpus"
            else:
                answer_text = (
                    f"Citation count statistics across {len(df)} papers:\n"
                    f"  • Mean: {desc['mean']:.0f}\n"
                    f"  • Median: {desc['50%']:.0f}\n"
                    f"  • Min: {int(desc['min'])}\n"
                    f"  • Max: {int(desc['max'])}\n"
                    f"  • Top paper: \"{top['title']}\" — {int(top['citations'])} citations"
                )
                evidence_paper = top
                rank_label = "highest in the corpus"
            return {
                "answer": answer_text,
                "data": {"max_citations": int(desc["max"]), "paper_count": len(df)},
                "evidence": [{
                    "paper_id": evidence_paper["id"],
                    "title": evidence_paper["title"],
                    "year": int(evidence_paper["year"]) if pd.notna(evidence_paper["year"]) else "",
                    "section": "papers",
                    "quote": f"{int(evidence_paper['citations'])} citations — {rank_label}",
                }],
            }

    # Generic: describe all numeric data
    sql = "SELECT param_count_millions FROM model_facts WHERE param_count_millions IS NOT NULL"
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=["params"])
        desc = df.describe().round(1)
        summary = (
            f"Quantitative summary of model parameters ({int(desc.loc['count', 'params'])} models):\n"
            f"  • Mean: {desc.loc['mean', 'params']:.1f}M\n"
            f"  • Median: {desc.loc['50%', 'params']:.1f}M\n"
            f"  • Min: {desc.loc['min', 'params']:.1f}M\n"
            f"  • Max: {desc.loc['max', 'params']:.1f}M\n"
            f"  • Std dev: {desc.loc['std', 'params']:.1f}M"
        )
        return {"answer": summary, "evidence": []}

    return {"answer": "Could not identify the specific computation requested.", "evidence": []}
