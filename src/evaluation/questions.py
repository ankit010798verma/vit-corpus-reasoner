"""40+ evaluation questions across all 8 tiers with gold answers."""

EVAL_QUESTIONS: list[dict] = [
    # ── Tier 1: Single-document factual ──────────────────────────────────────
    {
        "id": "t1_q1",
        "tier": 1,
        "question": "What image patch size does the original ViT paper use?",
        "gold_answer": "16×16 pixels",
        "notes": "From 'An Image is Worth 16x16 Words' (Dosovitskiy et al., 2020)",
    },
    {
        "id": "t1_q2",
        "tier": 1,
        "question": "What self-supervised learning objective does the MAE paper propose?",
        "gold_answer": "Masked autoencoding — reconstructing masked image patches from visible ones",
        "notes": "He et al., 2022",
    },
    {
        "id": "t1_q3",
        "tier": 1,
        "question": "What is the key architectural innovation introduced by the Swin Transformer?",
        "gold_answer": "Shifted window self-attention that restricts attention to local windows while allowing cross-window connections",
        "notes": "Liu et al., 2021",
    },
    {
        "id": "t1_q4",
        "tier": 1,
        "question": "What training strategy does DeiT use to train ViT without large-scale pretraining data?",
        "gold_answer": "Knowledge distillation using a CNN teacher token and strong data augmentation",
        "notes": "Touvron et al., 2021",
    },
    {
        "id": "t1_q5",
        "tier": 1,
        "question": "What dataset does the DINO paper primarily use for self-supervised pretraining?",
        "gold_answer": "ImageNet",
        "notes": "Caron et al., 2021",
    },

    # ── Tier 2: Corpus-level aggregation ─────────────────────────────────────
    {
        "id": "t2_q1",
        "tier": 2,
        "question": "List all unique datasets used across the 100 papers, deduplicated.",
        "gold_answer": "Should include: ImageNet, COCO, ADE20K, Kinetics-400, Cityscapes, CIFAR-10, CIFAR-100, etc. (exact list depends on corpus)",
        "notes": "Answered via SQL GROUP BY on dataset_uses; exact list is data-driven",
    },
    {
        "id": "t2_q2",
        "tier": 2,
        "question": "What is the most commonly used evaluation benchmark across the 100 papers?",
        "gold_answer": "ImageNet (Top-1 accuracy) is expected to dominate for ViT papers",
        "notes": "SQL COUNT on benchmark_results",
    },
    {
        "id": "t2_q3",
        "tier": 2,
        "question": "What is the median reported parameter count across all models in the corpus?",
        "gold_answer": "Expected ~80-300M based on typical ViT model sizes",
        "notes": "SQL median on model_facts.param_count_millions",
    },
    {
        "id": "t2_q4",
        "tier": 2,
        "question": "How many papers in the corpus report results on COCO detection?",
        "gold_answer": "Count from benchmark_results WHERE benchmark_name LIKE '%COCO%'",
        "notes": "Exact number is data-driven",
    },
    {
        "id": "t2_q5",
        "tier": 2,
        "question": "Which evaluation metric appears most frequently across all benchmark results in the corpus?",
        "gold_answer": "Top-1 Accuracy expected to be most common for ViT papers focused on image classification",
        "notes": "SQL GROUP BY metric_name",
    },

    # ── Tier 3: Comparative / contradiction ──────────────────────────────────
    {
        "id": "t3_q1",
        "tier": 3,
        "question": "Which papers report conflicting ImageNet Top-1 accuracy results?",
        "gold_answer": "Papers reporting same benchmark with different values under different conditions",
        "notes": "SQL finds pairs with same benchmark, divergent values; Sonnet assesses if genuine conflict",
    },
    {
        "id": "t3_q2",
        "tier": 3,
        "question": "List papers that claim state-of-the-art on ImageNet with their reported numbers.",
        "gold_answer": "Papers where is_sota_claim=True with benchmark='ImageNet' and metric='Top-1 Accuracy'",
        "notes": "SQL filter on is_sota_claim + benchmark",
    },
    {
        "id": "t3_q3",
        "tier": 3,
        "question": "Find papers in the corpus where the use of data augmentation is disputed or inconsistently reported.",
        "gold_answer": "Papers with conflicting uses_augmentation values for the same dataset",
        "notes": "SQL GROUP BY paper comparison on uses_augmentation",
    },
    {
        "id": "t3_q4",
        "tier": 3,
        "question": "Which papers claim to outperform ViT on ImageNet while using fewer parameters?",
        "gold_answer": "Papers with higher ImageNet accuracy than ViT-Base (81.8%) but lower param count (<86M)",
        "notes": "SQL filter on value > 81.8 AND param_count < 86",
    },
    {
        "id": "t3_q5",
        "tier": 3,
        "question": "Are there papers that report different conclusions about the effectiveness of self-attention vs. convolution for visual recognition?",
        "gold_answer": "Papers proposing transformers claiming superiority vs. papers with hybrid or CNN approaches showing competitive results",
        "notes": "Requires comparison of method_claims across architecture types",
    },

    # ── Tier 4: Temporal / evolution ─────────────────────────────────────────
    {
        "id": "t4_q1",
        "tier": 4,
        "question": "How has the average parameter count of Vision Transformer models grown from 2020 to 2024?",
        "gold_answer": "Expected trend: starting from ~86M (ViT-Base, 2020) with large models growing, while efficient variants push count down",
        "notes": "SQL GROUP BY year AVG on model_facts",
    },
    {
        "id": "t4_q2",
        "tier": 4,
        "question": "How has the best reported ImageNet Top-1 accuracy evolved from 2020 to 2024?",
        "gold_answer": "Expected improvement from ~81% (ViT-Base 2020) to >90% with advanced pretraining",
        "notes": "SQL MAX by year on benchmark_results WHERE benchmark='ImageNet'",
    },
    {
        "id": "t4_q3",
        "tier": 4,
        "question": "Trace the evolution of masked image modeling as a pretraining technique across the corpus chronologically.",
        "gold_answer": "BEiT (2021) → MAE (2022) → subsequent works — progression with dates",
        "notes": "method_claims WHERE claim relates to masked modeling, ORDER BY year",
    },
    {
        "id": "t4_q4",
        "tier": 4,
        "question": "What pretraining datasets were considered state-of-the-art in 2020 versus 2023?",
        "gold_answer": "2020: ImageNet-1K dominant; 2022-2023: ImageNet-21K, larger web-scale datasets",
        "notes": "Temporal SQL on dataset_uses + papers.year",
    },
    {
        "id": "t4_q5",
        "tier": 4,
        "question": "How has the adoption of multi-scale feature extraction changed over time in ViT papers?",
        "gold_answer": "Later papers (2021+) increasingly incorporate hierarchical/multi-scale designs (Swin, PVT)",
        "notes": "method_claims trend by year",
    },

    # ── Tier 5: Citation-graph reasoning ─────────────────────────────────────
    {
        "id": "t5_q1",
        "tier": 5,
        "question": "Which paper in the corpus is most cited by other papers in the corpus?",
        "gold_answer": "Expected: original ViT paper (Dosovitskiy et al., 2020) — 'An Image is Worth 16x16 Words'",
        "notes": "NetworkX in-degree / PageRank",
    },
    {
        "id": "t5_q2",
        "tier": 5,
        "question": "Which papers in the corpus directly build on or cite the Swin Transformer?",
        "gold_answer": "Papers that list Swin Transformer in their references and use it as baseline or starting point",
        "notes": "NetworkX predecessors of Swin Transformer paper node",
    },
    {
        "id": "t5_q3",
        "tier": 5,
        "question": "What are the top 5 most influential papers within the corpus by inner-corpus citation count?",
        "gold_answer": "ViT, Swin Transformer, DeiT, DINO, MAE expected in top 5",
        "notes": "NetworkX in-degree sorted",
    },
    {
        "id": "t5_q4",
        "tier": 5,
        "question": "Is there a citation path from the MAE paper to the original ViT paper?",
        "gold_answer": "Yes — MAE builds on ViT and cites it directly",
        "notes": "NetworkX shortest_path",
    },
    {
        "id": "t5_q5",
        "tier": 5,
        "question": "Which corpus papers are cited by the fewest other corpus papers (most isolated)?",
        "gold_answer": "Papers with lowest inner-corpus in-degree",
        "notes": "NetworkX in-degree sorted ascending",
    },

    # ── Tier 6: Multi-hop / compositional ────────────────────────────────────
    {
        "id": "t6_q1",
        "tier": 6,
        "question": "What datasets does the highest-cited paper in the corpus use, and which other corpus papers also use those same datasets?",
        "gold_answer": "Step 1: Identify most-cited paper (T5). Step 2: Get its datasets (T2). Step 3: Find other papers using same datasets (T2 filter). Expected: ImageNet, other large-scale datasets shared by many papers.",
        "notes": "T5 → T2 → T2 chain",
    },
    {
        "id": "t6_q2",
        "tier": 6,
        "question": "Among papers in the corpus that use ImageNet for evaluation, which ones do NOT report using data augmentation?",
        "gold_answer": "SQL: papers where dataset_uses has ImageNet AND uses_augmentation=0 or NULL",
        "notes": "SQL set intersection + negation",
    },
    {
        "id": "t6_q3",
        "tier": 6,
        "question": "Which papers use the same self-supervised pretraining technique as the most-cited paper in the corpus?",
        "gold_answer": "Identify most-cited paper's method, find papers with similar method_claims",
        "notes": "T5 → T1 (get method) → T2/retrieval (find similar methods)",
    },
    {
        "id": "t6_q4",
        "tier": 6,
        "question": "Among papers reporting over 85% ImageNet Top-1 accuracy, what is the most common pretraining strategy?",
        "gold_answer": "SQL: papers WHERE benchmark_results.value > 85 on ImageNet, then aggregate dataset_uses.use_type",
        "notes": "SQL composition",
    },
    {
        "id": "t6_q5",
        "tier": 6,
        "question": "Which papers that cite the original ViT also evaluate on COCO object detection?",
        "gold_answer": "Intersection of: papers citing ViT (T5) AND papers with COCO in benchmark_results",
        "notes": "T5 neighborhood + SQL filter",
    },

    # ── Tier 7: Negation / absence ────────────────────────────────────────────
    {
        "id": "t7_q1",
        "tier": 7,
        "question": "Which standard Vision Transformer benchmarks are conspicuously absent from the 100 papers?",
        "gold_answer": "Benchmarks in STANDARD_VIT_BENCHMARKS not appearing in benchmark_results",
        "notes": "Set subtraction against known benchmark list",
    },
    {
        "id": "t7_q2",
        "tier": 7,
        "question": "Are there any papers in the corpus that do not use neural networks?",
        "gold_answer": "Papers without any entries in model_facts with neural architecture types — likely very few or none",
        "notes": "SQL: papers NOT IN model_facts neural types",
    },
    {
        "id": "t7_q3",
        "tier": 7,
        "question": "Which papers in the corpus do not evaluate on ImageNet?",
        "gold_answer": "Papers where paper_id NOT IN (SELECT paper_id FROM benchmark_results WHERE benchmark LIKE '%ImageNet%')",
        "notes": "SQL NOT IN",
    },
    {
        "id": "t7_q4",
        "tier": 7,
        "question": "Which papers never report parameter counts for their proposed models?",
        "gold_answer": "Papers where paper_id NOT IN (SELECT DISTINCT paper_id FROM model_facts WHERE param_count_millions IS NOT NULL)",
        "notes": "SQL NOT IN on model_facts",
    },
    {
        "id": "t7_q5",
        "tier": 7,
        "question": "Which dense prediction tasks (segmentation, detection) are underrepresented in the corpus compared to image classification?",
        "gold_answer": "Compare count of papers with COCO/ADE20K benchmarks vs ImageNet — expected: classification dominates",
        "notes": "SQL COUNT comparison by benchmark type",
    },

    # ── Tier 8: Quantitative computation ─────────────────────────────────────
    {
        "id": "t8_q1",
        "tier": 8,
        "question": "What is the sum of all reported parameter counts for transformer-based models across the 100 papers?",
        "gold_answer": "SQL SUM(param_count_millions) WHERE architecture_type='transformer' — exact number depends on corpus",
        "notes": "pandas sum over model_facts",
    },
    {
        "id": "t8_q2",
        "tier": 8,
        "question": "What is the correlation between training dataset size and reported ImageNet Top-1 accuracy?",
        "gold_answer": "Expected positive correlation (r ≈ 0.3-0.6): larger pretraining datasets generally yield higher accuracy",
        "notes": "pandas corr between dataset_size_k_samples and benchmark value",
    },
    {
        "id": "t8_q3",
        "tier": 8,
        "question": "What is the median reported parameter count across all Vision Transformer models in the corpus?",
        "gold_answer": "Expected ~86-307M based on ViT-Base (86M) to ViT-Huge (632M) range",
        "notes": "pandas median on model_facts.param_count_millions",
    },
    {
        "id": "t8_q4",
        "tier": 8,
        "question": "How many total parameters have been proposed across all models in the corpus if you sum all reported counts?",
        "gold_answer": "Total sum across ALL model_facts (any architecture) — data-driven",
        "notes": "pandas SUM on all param_count_millions",
    },
    {
        "id": "t8_q5",
        "tier": 8,
        "question": "What is the average ImageNet Top-1 accuracy claimed by papers that use self-supervised pretraining?",
        "gold_answer": "SQL/pandas: AVG(benchmark_results.value) WHERE paper uses self-supervised dataset_use_type",
        "notes": "SQL JOIN filter + pandas mean",
    },
]
