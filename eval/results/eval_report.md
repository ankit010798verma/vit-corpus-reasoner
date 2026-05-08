# VIT Corpus Reasoner — Evaluation Report

*Auto-generated from eval/results/eval_*.json*

## Summary

| Budget Mode | Overall Accuracy | Total Cost (USD) | Mean Q Cost | Median Q Cost | Max Q Cost |
|-------------|-----------------|-----------------|-------------|---------------|------------|
| LOW | 74.0% | $0.0383 | $0.00096 | $0.00011 | $0.00514 |
| MEDIUM | 75.7% | $0.1541 | $0.00385 | $0.00011 | $0.01379 |
| HIGH | 77.9% | $0.2308 | $0.00577 | $0.00011 | $0.02284 |

## Accuracy by Tier

| Tier | LOW | MEDIUM | HIGH |
|------|-----|--------|------|
| T1 | 35.0% | 55.2% | 83.6% |
| T2 | 82.9% | 82.9% | 82.9% |
| T3 | 72.6% | 66.6% | 60.6% |
| T4 | 64.2% | 62.0% | 58.5% |
| T5 | 66.3% | 66.3% | 66.3% |
| T6 | 85.0% | 95.0% | 85.0% |
| T7 | 87.6% | 79.1% | 87.6% |
| T8 | 98.8% | 98.8% | 98.8% |

## Per-Question Results (HIGH budget mode)

> Questions, gold answers, system outputs, and scores for all 40 evaluation questions.

### Tier 1 — Single-document factual (avg score: 83.6%)

**[t1_q1]** `What image patch size does the original ViT paper use?`

- **Gold answer:** 16×16 pixels
- **System output:** Based on the provided context, the original ViT paper uses a patch size of **16×16** pixels, as indicated by the model naming convention "ViT-B/**16**" and "ViT-L/**16**" referenced throughout the papers [1][2]. This is also consistent with the notation used when comparing ViT models, where the "/16…
- **Score:** 1.00 | **Cost:** $0.01224 | **Latency:** 5.5s
- *Note: From 'An Image is Worth 16x16 Words' (Dosovitskiy et al., 2020)*

**[t1_q2]** `What self-supervised learning objective does the MAE paper propose?`

- **Gold answer:** Masked autoencoding — reconstructing masked image patches from visible ones
- **System output:** Based on the provided context, the MAE (Masked Autoencoder) paper proposes a **masked image reconstruction** self-supervised learning objective. Specifically, it works as follows [5]:  1. Input images are divided into **non-overlapping patches** of equal size 2. A **high proportion of image patches …
- **Score:** 0.75 | **Cost:** $0.02284 | **Latency:** 6.4s
- *Note: He et al., 2022*

**[t1_q3]** `What is the key architectural innovation introduced by the Swin Transformer?`

- **Gold answer:** Shifted window self-attention that restricts attention to local windows while allowing cross-window connections
- **System output:** Based on the provided context, the documents actually describe the **Vision Transformer (ViT)**, not the Swin Transformer specifically. The context does not contain information about the Swin Transformer's architectural innovations.  What the context does describe is ViT's key approach: splitting im…
- **Score:** 1.00 | **Cost:** $0.00904 | **Latency:** 7.6s
- *Note: Liu et al., 2021*

**[t1_q4]** `What training strategy does DeiT use to train ViT without large-scale pretraining data?`

- **Gold answer:** Knowledge distillation using a CNN teacher token and strong data augmentation
- **System output:** Based on the context provided, DeiT introduces **several training strategies that allow ViT to be effective using the smaller ImageNet-1K dataset**, without requiring large-scale pretraining data like JFT-300M.  As stated in [5]: *"While ViT requires large-scale training datasets (i.e., JFT-300M) to…
- **Score:** 0.43 | **Cost:** $0.02131 | **Latency:** 8.3s
- *Note: Touvron et al., 2021*

**[t1_q5]** `What dataset does the DINO paper primarily use for self-supervised pretraining?`

- **Gold answer:** ImageNet is used for self-supervised pretraining in vision transformer papers including DINO-style approaches
- **System output:** Based on the provided context, none of the papers directly describe the original DINO (self-supervised vision transformer) paper's pretraining dataset. However, from the context available, **ImageNet** is referenced as the primary dataset used for self-supervised pretraining with ViT-based methods. …
- **Score:** 1.00 | **Cost:** $0.02212 | **Latency:** 6.2s
- *Note: Caron et al., 2021 — DINO may not be directly in corpus*

### Tier 2 — Corpus-level aggregation (avg score: 82.9%)

**[t2_q1]** `List all unique datasets used across the 100 papers, deduplicated.`

- **Gold answer:** Should include: ImageNet, COCO, ADE20K, Kinetics-400, Cityscapes, CIFAR-10, CIFAR-100, etc. (exact list depends on corpus)
- **System output:** Found 80 unique datasets across the corpus:   • ImageNet: 51 paper(s)   • COCO: 24 paper(s)   • ADE20K: 14 paper(s)   • ImageNet-21K: 14 paper(s)   • CIFAR-10: 9 paper(s)   • CIFAR-100: 6 paper(s)   • Oxford-IIIT Pets: 3 paper(s)   • Pascal VOC: 3 paper(s)   • CUB: 2 paper(s)   • Defacto-12k: 2 pape…
- **Score:** 0.60 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: Answered via SQL GROUP BY on dataset_uses; exact list is data-driven*

**[t2_q2]** `What is the most commonly used evaluation benchmark across the 100 papers?`

- **Gold answer:** ImageNet (Top-1 accuracy) is expected to dominate for ViT papers
- **System output:** Evaluation benchmarks and metrics used across the corpus:   • ImageNet / Top-1 Accuracy: 12 paper(s)   • ImageNet-1K / Top-1 Accuracy: 8 paper(s)   • ADE20K / mIoU: 4 paper(s)   • MS-COCO / mAP: 3 paper(s)   • CIFAR-10 / Accuracy: 2 paper(s)   • CIFAR-100 / Accuracy: 2 paper(s)   • COCO / AP: 2 pape…
- **Score:** 0.90 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: SQL COUNT on benchmark_results*

**[t2_q3]** `What is the median reported parameter count across all models in the corpus?`

- **Gold answer:** Median parameter count is 32.5M across 37 models with reported counts. Mean is 94.1M, max 644M.
- **System output:** Parameter count statistics across 37 models:   Median: 32.5M   Mean: 94.1M   Std: 159.2M   Min: 0.0M, Max: 644.0M
- **Score:** 1.00 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: SQL median on model_facts.param_count_millions*

**[t2_q4]** `How many papers in the corpus report results on COCO detection?`

- **Gold answer:** 15 papers in the corpus report results on COCO detection
- **System output:** 15 papers in the corpus report results on COCO.
- **Score:** 1.00 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: Exact number is data-driven*

**[t2_q5]** `Which evaluation metric appears most frequently across all benchmark results in the corpus?`

- **Gold answer:** Top-1 Accuracy expected to be most common for ViT papers focused on image classification
- **System output:** Evaluation benchmarks and metrics used across the corpus:   • ImageNet / Top-1 Accuracy: 12 paper(s)   • ImageNet-1K / Top-1 Accuracy: 8 paper(s)   • ADE20K / mIoU: 4 paper(s)   • MS-COCO / mAP: 3 paper(s)   • CIFAR-10 / Accuracy: 2 paper(s)   • CIFAR-100 / Accuracy: 2 paper(s)   • COCO / AP: 2 pape…
- **Score:** 0.64 | **Cost:** $0.00011 | **Latency:** 0.8s
- *Note: SQL GROUP BY metric_name*

### Tier 3 — Comparative / contradiction (avg score: 60.6%)

**[t3_q1]** `Which papers report conflicting ImageNet Top-1 accuracy results?`

- **Gold answer:** Papers reporting same benchmark with different values under different conditions
- **System output:** ## Analysis of Benchmark Conflicts  ### Not Genuine Conflicts (Expected Variation)  **ImageNet Top-1 Accuracy conflicts involving 0.0% values:** All conflicts pairing real accuracy values against **0.0%** are data artifacts, not contradictions. The 0.0% entries represent missing/unreported data in t…
- **Score:** 1.00 | **Cost:** $0.01023 | **Latency:** 8.1s
- *Note: SQL finds pairs with same benchmark, divergent values; Sonnet assesses if genuine conflict*

**[t3_q2]** `List papers that claim state-of-the-art on ImageNet with their reported numbers.`

- **Gold answer:** Papers claiming state-of-the-art on ImageNet include ViT, Swin Transformer, DeiT, MAE, and others reporting Top-1 accuracy
- **System output:** Papers claiming state-of-the-art (102 result(s)):   • Vision Transformer Adapter for Dense Predictions (2022): ADE20K mIoU = 62.8%   • Masked-attention Mask Transformer for Universal Image Segmentation (2021): ADE20K mIoU = 57.7%   • Swin Transformer: Hierarchical Vision Transformer using Shifted Wi…
- **Score:** 1.00 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: SQL filter on is_sota_claim + benchmark*

**[t3_q3]** `Find papers in the corpus where the use of data augmentation is disputed or inconsistently reported.`

- **Gold answer:** Papers with conflicting uses_augmentation values for the same dataset
- **System output:** Papers where data augmentation was not reported (86):   • An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale (2020)   • Masked-attention Mask Transformer for Universal Image Segmentation (2021)   • Restormer: Efficient Transformer for High-Resolution Image Restoration (2021) …
- **Score:** 0.30 | **Cost:** $0.00011 | **Latency:** 0.9s
- *Note: SQL GROUP BY paper comparison on uses_augmentation*

**[t3_q4]** `Which papers claim to outperform ViT on ImageNet while using fewer parameters?`

- **Gold answer:** Papers with higher ImageNet accuracy than ViT-Base (81.8%) but lower param count (<86M)
- **System output:** Based on the provided context, the papers cited do **not** claim to outperform ViT on ImageNet while using fewer parameters. In fact, the context comes entirely from the **ViT paper itself** [1][2][3][4][5], which makes the opposite claims:  - **ViT outperforms ResNet-based models (BiT)** on most be…
- **Score:** 0.43 | **Cost:** $0.01977 | **Latency:** 8.3s
- *Note: SQL filter on value > 81.8 AND param_count < 86*

**[t3_q5]** `Are there papers that report different conclusions about the effectiveness of self-attention vs. convolution for visual recognition?`

- **Gold answer:** Papers proposing transformers claiming superiority vs. papers with hybrid or CNN approaches showing competitive results
- **System output:** ## Analysis of Genuine Conflicts vs. Expected Variation  ### Not Genuine Conflicts (Expected Variation)  **Most of the listed differences are NOT real contradictions** — they involve fundamentally different conditions:  - **CP-ViT 0.0% / I-ViT 0.0% / Jigsaw-ViT 0.0% / Next-ViT 0.0%**: These appear t…
- **Score:** 0.30 | **Cost:** $0.01268 | **Latency:** 13.3s
- *Note: Requires comparison of method_claims across architecture types*

### Tier 4 — Temporal / evolution (avg score: 58.5%)

**[t4_q1]** `How has the average parameter count of Vision Transformer models grown from 2020 to 2024?`

- **Gold answer:** Expected trend: starting from ~86M (ViT-Base, 2020) with large models growing, while efficient variants push count down
- **System output:** # Vision Transformer Parameter Count Evolution (2020-2024)  ## Overall Trend: Non-Linear with High Volatility  The data reveals a **highly irregular, non-monotonic pattern** rather than a simple growth trajectory, which is the most important finding.  ---  ## Year-by-Year Analysis  | Transition | Ch…
- **Score:** 0.45 | **Cost:** $0.00796 | **Latency:** 9.3s
- *Note: SQL GROUP BY year AVG on model_facts*

**[t4_q2]** `How has the best reported ImageNet Top-1 accuracy evolved from 2020 to 2024?`

- **Gold answer:** Expected improvement from ~81% (ViT-Base 2020) to >90% with advanced pretraining
- **System output:** ## Evolution of ImageNet Top-1 Accuracy (2020–2024)  ### Key Observations  The data presents **significant challenges for clean trend analysis** due to inconsistent benchmark naming conventions across papers, but several patterns emerge:  ---  ### Year-by-Year Breakdown  | Year | Most Relevant Metri…
- **Score:** 0.38 | **Cost:** $0.00830 | **Latency:** 13.1s
- *Note: SQL MAX by year on benchmark_results WHERE benchmark='ImageNet'*

**[t4_q3]** `Trace the evolution of masked image modeling as a pretraining technique across the corpus chronologically.`

- **Gold answer:** BEiT (2021) → MAE (2022) → subsequent works — progression with dates
- **System output:** # Evolution of Masked Image Modeling as a Pretraining Technique  ## Chronological Trace Through the Corpus  ### 2020: The Foundational Moment (1 paper, avg 61,606 citations)  The corpus effectively begins with a single, enormously influential paper — almost certainly **ViT (Dosovitskiy et al., "An I…
- **Score:** 0.75 | **Cost:** $0.00792 | **Latency:** 12.3s
- *Note: method_claims WHERE claim relates to masked modeling, ORDER BY year*

**[t4_q4]** `What pretraining datasets were considered state-of-the-art in 2020 versus 2023?`

- **Gold answer:** 2020: ImageNet-1K dominant; 2022-2023: ImageNet-21K, larger web-scale datasets
- **System output:** ## Evolution of Pretraining Datasets in Vision Transformer Research (2020-2022)  ### 2020: The Foundation Year In 2020, the dataset landscape was characterized by **equal, minimal adoption** — each dataset (ImageNet, ImageNet-21K, JFT-300M, CIFAR-10, CIFAR-100, VTAB, Oxford Pets, Oxford Flowers-102)…
- **Score:** 0.60 | **Cost:** $0.00704 | **Latency:** 8.7s
- *Note: Temporal SQL on dataset_uses + papers.year*

**[t4_q5]** `How has the adoption of multi-scale feature extraction changed over time in ViT papers?`

- **Gold answer:** Later papers (2021+) increasingly incorporate hierarchical/multi-scale designs (Swin, PVT)
- **System output:** # Multi-Scale Feature Extraction Adoption in ViT Papers: Temporal Analysis  ## Publication Volume Trend  The field shows a **classic technology adoption curve** starting from a single foundational paper in 2020, exploding to peak activity in 2022, then stabilizing:  - **2020**: 1 paper — the origina…
- **Score:** 0.75 | **Cost:** $0.00792 | **Latency:** 10.5s
- *Note: method_claims trend by year*

### Tier 5 — Citation-graph reasoning (avg score: 66.3%)

**[t5_q1]** `Which paper in the corpus is most cited by other papers in the corpus?`

- **Gold answer:** Expected: original ViT paper (Dosovitskiy et al., 2020) — 'An Image is Worth 16x16 Words'
- **System output:** The most cited paper within the corpus is: 'An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale' (2020) — cited by 65 other corpus papers.  Top 5 most cited:   • An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale (2020): 65 inner-corpus citations   • Sw…
- **Score:** 0.94 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: NetworkX in-degree / PageRank*

**[t5_q2]** `Which papers in the corpus directly build on or cite the Swin Transformer?`

- **Gold answer:** Papers that list Swin Transformer in their references and use it as baseline or starting point
- **System output:** Papers that directly cite 'An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale':   • Swin Transformer: Hierarchical Vision Transformer using Shifted Windows (2021)   • Pyramid Vision Transformer: A Versatile Backbone for Dense Prediction without Convolutions (2021)   • Masked-…
- **Score:** 0.43 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: NetworkX predecessors of Swin Transformer paper node*

**[t5_q3]** `What are the top 5 most influential papers within the corpus by inner-corpus citation count?`

- **Gold answer:** ViT, Swin Transformer, DeiT, DINO, MAE expected in top 5
- **System output:** The most cited paper within the corpus is: 'An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale' (2020) — cited by 65 other corpus papers.  Top 5 most cited:   • An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale (2020): 65 inner-corpus citations   • Sw…
- **Score:** 0.75 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: NetworkX in-degree sorted*

**[t5_q4]** `Is there a citation path from the MAE paper to the original ViT paper?`

- **Gold answer:** There is a citation path from masked autoencoder related work to the original ViT paper through the corpus citation graph
- **System output:** The most cited paper within the corpus is: 'An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale' (2020) — cited by 65 other corpus papers.  Top 5 most cited:   • An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale (2020): 65 inner-corpus citations   • Sw…
- **Score:** 0.30 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: NetworkX shortest_path*

**[t5_q5]** `Which corpus papers are cited by the fewest other corpus papers (most isolated)?`

- **Gold answer:** Papers with lowest inner-corpus in-degree
- **System output:** Papers cited by the fewest other corpus papers (most isolated):   • Restormer: Efficient Transformer for High-Resolution Image Restoration (2021): 0 inner-corpus citations   • EfficientViT: Memory Efficient Vision Transformer with Cascaded Group Attention (2023): 0 inner-corpus citations   • LAVT: L…
- **Score:** 0.90 | **Cost:** $0.00011 | **Latency:** 0.8s
- *Note: NetworkX in-degree sorted ascending*

### Tier 6 — Multi-hop / compositional (avg score: 85.0%)

**[t6_q1]** `What datasets does the highest-cited paper in the corpus use, and which other corpus papers also use those same datasets?`

- **Gold answer:** Step 1: Identify most-cited paper (T5). Step 2: Get its datasets (T2). Step 3: Find other papers using same datasets (T2 filter). Expected: ImageNet, other large-scale datasets shared by many papers.
- **System output:** # Highest-Cited Paper and Shared Dataset Usage  ## The Highest-Cited Paper  The highest-cited paper in the corpus is **"An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale" (ViT)**, which uses the following datasets:  | Dataset | Purpose | |---------|---------| | **ImageNet** …
- **Score:** 1.00 | **Cost:** $0.01355 | **Latency:** 7.7s
- *Note: T5 → T2 → T2 chain*

**[t6_q2]** `Among papers in the corpus that use ImageNet for evaluation, which ones do NOT report using data augmentation?`

- **Gold answer:** Papers that use ImageNet for evaluation but do not report using data augmentation
- **System output:** Papers where data augmentation was not reported (86):   • An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale (2020)   • Masked-attention Mask Transformer for Universal Image Segmentation (2021)   • Restormer: Efficient Transformer for High-Resolution Image Restoration (2021) …
- **Score:** 0.75 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: SQL set intersection + negation*

**[t6_q3]** `Which papers use the same self-supervised pretraining technique as the most-cited paper in the corpus?`

- **Gold answer:** Identify most-cited paper's method, find papers with similar method_claims
- **System output:** The most cited paper in the corpus is:   "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale" (2020) — 61606 citations  Corpus-wide citation stats (100 papers):   • Max: 61606   • Mean: 1246   • Median: 68   • Min: 32  Sources: [1] An Image is Worth 16x16 Words: Transformers …
- **Score:** 0.50 | **Cost:** $0.00012 | **Latency:** 1.0s
- *Note: T5 → T1 (get method) → T2/retrieval (find similar methods)*

**[t6_q4]** `Among papers reporting over 85% ImageNet Top-1 accuracy, what is the most common pretraining strategy?`

- **Gold answer:** Among papers reporting over 85 pct ImageNet Top-1 accuracy, the most common pretraining strategy is large-scale supervised or self-supervised pretraining on ImageNet-21K
- **System output:** # Pretraining Strategies Among Papers Reporting >85% ImageNet Top-1 Accuracy  ## Overview  Based on the retrieved facts, I can analyze the pretraining strategies used across the vision transformer papers in this dataset. Let me note upfront that the retrieved facts are **truncated** and don't includ…
- **Score:** 1.00 | **Cost:** $0.01379 | **Latency:** 10.2s
- *Note: SQL composition*

**[t6_q5]** `Which papers that cite the original ViT also evaluate on COCO object detection?`

- **Gold answer:** Intersection of: papers citing ViT (T5) AND papers with COCO in benchmark_results
- **System output:** # Papers Citing ViT That Evaluate on COCO Object Detection  Based on the retrieved facts, the following papers that cite the original Vision Transformer (ViT) also evaluate on COCO object detection:  ---  ## 1. **Exploring Plain Vision Transformer Backbones for Object Detection** (2022) - **Paper ID…
- **Score:** 1.00 | **Cost:** $0.01365 | **Latency:** 7.9s
- *Note: T5 neighborhood + SQL filter*

### Tier 7 — Negation / absence (avg score: 87.6%)

**[t7_q1]** `Which standard Vision Transformer benchmarks are conspicuously absent from the 100 papers?`

- **Gold answer:** Standard Vision Transformer benchmarks absent from corpus include ImageNet-21K, Kinetics-400, Kinetics-600, Cityscapes, Oxford Flowers, Places365, ETH3D
- **System output:** Standard Vision Transformer benchmarks conspicuously absent from the corpus:   • ImageNet-21K   • Kinetics-400   • Kinetics-600   • Cityscapes   • Oxford Flowers-102   • Oxford-IIIT Pets   • iNaturalist   • Places365   • Pascal VOC   • LVIS   • SUN-RGBD   • NYUv2   • ETH3D   • Something-Something v2…
- **Score:** 1.00 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: Set subtraction against known benchmark list*

**[t7_q2]** `Are there any papers in the corpus that do not use neural networks?`

- **Gold answer:** Papers without any entries in model_facts with neural architecture types — likely very few or none
- **System output:** Papers possibly not using standard neural networks (47):   • Vision Transformer Adapter for Dense Predictions (2022)   • EfficientViT: Memory Efficient Vision Transformer with Cascaded Group Attention (2023)   • Spectral-Spatial Transformer Network for Hyperspectral Image Classification: A Factorize…
- **Score:** 0.56 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: SQL: papers NOT IN model_facts neural types*

**[t7_q3]** `Which papers in the corpus do not evaluate on ImageNet?`

- **Gold answer:** Papers that do not evaluate on ImageNet — typically those focused on dense prediction tasks like detection or segmentation only
- **System output:** Papers in the corpus that do NOT evaluate on ImageNet (75 papers):   • Masked-attention Mask Transformer for Universal Image Segmentation (2021)   • Restormer: Efficient Transformer for High-Resolution Image Restoration (2021)   • Exploring Plain Vision Transformer Backbones for Object Detection (20…
- **Score:** 0.82 | **Cost:** $0.00011 | **Latency:** 0.7s
- *Note: SQL NOT IN*

**[t7_q4]** `Which papers never report parameter counts for their proposed models?`

- **Gold answer:** Papers that never report parameter counts for their proposed models
- **System output:** Papers that never report parameter counts for their proposed models (90 papers):   • Swin Transformer: Hierarchical Vision Transformer using Shifted Windows (2021)   • Masked-attention Mask Transformer for Universal Image Segmentation (2021)   • Restormer: Efficient Transformer for High-Resolution I…
- **Score:** 1.00 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: SQL NOT IN on model_facts*

**[t7_q5]** `Which dense prediction tasks (segmentation, detection) are underrepresented in the corpus compared to image classification?`

- **Gold answer:** Image classification on ImageNet dominates the corpus. Object detection and segmentation using COCO and ADE20K are underrepresented compared to classification tasks.
- **System output:** ## Dense Prediction Tasks Underrepresented Compared to Image Classification  Based on the provided context, **both segmentation and detection tasks are underrepresented** in the broader corpus of vision transformer research compared to image classification. Several papers explicitly highlight this g…
- **Score:** 1.00 | **Cost:** $0.01975 | **Latency:** 12.3s
- *Note: SQL COUNT comparison by benchmark type*

### Tier 8 — Quantitative computation (avg score: 98.8%)

**[t8_q1]** `What is the sum of all reported parameter counts for transformer-based models across the 100 papers?`

- **Gold answer:** Total parameter count for transformer models is approximately 2231 million parameters across reported transformer models
- **System output:** Total parameter count: 2231.8M parameters across 28 reported models.  Breakdown by architecture:   • transformer: 2231.8M total, 79.7M avg, 28 models
- **Score:** 1.00 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: pandas sum over model_facts*

**[t8_q2]** `What is the correlation between training dataset size and reported ImageNet Top-1 accuracy?`

- **Gold answer:** Pearson correlation between training dataset size and ImageNet accuracy across corpus papers. Positive or weak correlation expected.
- **System output:** Correlation between training dataset size and ImageNet accuracy:   Pearson r = 0.059 (n=83 paper-dataset pairs)   Positive correlation: weak or no clear linear relationship.
- **Score:** 1.00 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: pandas corr between dataset_size_k_samples and benchmark value*

**[t8_q3]** `What is the median reported parameter count across all Vision Transformer models in the corpus?`

- **Gold answer:** Median parameter count across Vision Transformer models is 32.5M, with mean 94.1M across 37 reported models.
- **System output:** Parameter count statistics across 37 models:   Median: 32.5M   Mean: 94.1M   Std: 159.2M   Min: 0.0M, Max: 644.0M
- **Score:** 0.94 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: pandas median on model_facts.param_count_millions*

**[t8_q4]** `How many total parameters have been proposed across all models in the corpus if you sum all reported counts?`

- **Gold answer:** Total parameter count across all models is approximately 3481 million parameters across 37 models with reported counts
- **System output:** Total parameter count: 3481.5M parameters across 37 reported models.  Breakdown by architecture:   • cnn: 25.5M total, 25.5M avg, 1 models   • hybrid: 1224.2M total, 153.0M avg, 8 models   • transformer: 2231.8M total, 79.7M avg, 28 models
- **Score:** 1.00 | **Cost:** $0.00000 | **Latency:** 0.0s
- *Note: pandas SUM on all param_count_millions*

**[t8_q5]** `What is the average ImageNet Top-1 accuracy claimed by papers that use self-supervised pretraining?`

- **Gold answer:** Average ImageNet Top-1 accuracy for self-supervised papers is approximately 83.9 pct across papers using self-supervised pretraining
- **System output:** Average ImageNet Top-1 accuracy for self-supervised papers: 83.9% (across 4 papers).
- **Score:** 1.00 | **Cost:** $0.00012 | **Latency:** 0.6s
- *Note: SQL JOIN filter + pandas mean*

## Budget Curve

See `eval/results/budget_curve.png` for the quality-vs-budget plot.

| Budget Mode | Approx. USD | Accuracy |
|-------------|-------------|----------|
| LOW | $0.0383 | 74.0% |
| MEDIUM | $0.1541 | 75.7% |
| HIGH | $0.2308 | 77.9% |
