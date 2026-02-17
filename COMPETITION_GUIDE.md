# Harmonizing the Data of Your Data — Competition Guide

Official competition: **extract SDRF (Sample and Data Relationship Format) metadata from proteomics papers** so experimental details become structured, machine-readable data. This guide summarizes the task, data, evaluation, and how to compete.

---

## 1. Official task and goal

- **Problem:** Scientific knowledge is in natural language; SDRF describes samples and data in a standard, computable way. Many papers lack complete SDRFs, so large-scale reuse is blocked.
- **Your job:** Build a **model, prompt, or pipeline** that takes **paper text** and outputs a **complete SDRF** (rule-based, LLM, classical NLP, or fine-tuned models — anything that produces a valid SDRF).
- **Success:** Match or beat the benchmarks on a **held-out test set** of annotated SDRFs.

---

## 2. Official data (from competition page)

| Data | Path (in repo / Kaggle) | Purpose |
|------|-------------------------|--------|
| **Training – paper text** | `data/Training_PubText/` | Open-access publication text as **.json** files. |
| **Training – gold SDRF** | `data/Training_SDRFs/` | Human-annotated SDRFs (e.g. `HarmonizedFiles/`, `training.csv`). |
| **Training – GPT baseline** | `data/Training_GPT_Extract/` | GPT metadata using `BaselinePrompt.txt`. |
| **Test – paper text** | `data/Test_PubText/` | Publication text (.json) for leaderboard scoring. |
| **Submission template** | `SampleSubmission.csv` | Exact CSV format required (same columns, same row order/structure). |

In your workspace the data lives under `harmonizing-the-data-of-your-data/` (e.g. `Training_SDRFs/HarmonizedFiles/`, `Training_GPT_Extract/`, `BaselinePrompt.txt`). Map these to the official `data/` paths when using the GitHub repo or Kaggle data.

---

## 3. Official evaluation metric (critical)

Scoring is **not** row-by-row sample alignment. It is **per (PXD, column)** on **sets of unique annotation values**.

### Step 1 — Preprocessing

- Both **solution** (ground truth) and **submission** must have a **PXD** column.
- Data are **grouped by PXD**.
- For each **(PXD, column)**, take the **unique non-null values**.
- **Columns that contain only "Not Applicable"** are **excluded** from scoring.

### Step 2 — String harmonization

- All unique values (from solution and submission) are **clustered by string similarity ≥ 0.80**.
- Values in the same cluster are treated as the **same entity** (minor wording/spelling differences are tolerated).

### Step 3 — Set comparison (per (PXD, column))

- **Precision** = fraction of **predicted** entities that are correct (after harmonization).
- **Recall** = fraction of **true** entities that were recovered.
- **F1** = harmonic mean of precision and recall.
- **Duplicates don’t add weight** — comparison is **set-based**, not count-based.

### Step 4 — Final score

- **Leaderboard score** = **mean F1** over all evaluated (PXD, column) pairs.

### What this means for you

- You are scored on **recovering the right set of annotation values** per PXD and column, not on exact string match.
- Minor spelling/formatting differences are OK (similarity ≥ 0.80).
- **Extra wrong entities** → lower precision.
- **Missing true entities** → lower recall.
- **Strategy:** Focus on **correct set of values** per (PXD, column); filling every row is necessary only to produce the CSV, but the metric cares about unique values per column per PXD.

---

## 4. Submission rules

- **Non-final (leaderboard):** Up to **5 submissions per day**. CSV must follow **SampleSubmission.csv** exactly (same columns, same structure).
- **Final submission (to be eligible to win):**
  - **Option 1 — Kaggle ZIP:** Upload a ZIP containing:
    - `submission.csv` (your predicted SDRF in the sample format)
    - Minimal working example: e.g. `pipeline.py` (or notebook), `requirements.txt`, optional `README.md`
  - **Option 2 — GitHub PR:** Contribute your full pipeline to  
    **https://github.com/NCEMS/Kaggle-Harmonizing-the-data-of-your-data**  
    (folder under `Submissions/your-team-or-name/` with `pipeline.py`, `submission.csv`, `requirements.txt`, `README.md`). PRs get credited and can help with co-authorship consideration.

---

## 5. Prizes and citation

- **Total: $10,000** — 1st: $5,000 | 2nd: $3,000 | 3rd: $2,000  
- Co-authorship on resulting papers may be discussed for winning solutions.  
- **Citation:** Ian Sitarik, Iddo Friedberg, Tine Claeys, and Wout Bittremieux. *Harmonizing the Data of your Data*. https://kaggle.com/competitions/harmonizing-the-data-of-your-data, 2026. Kaggle.

---

## 6. Your local data layout (SDRF proteomics)

Your data is under `harmonizing-the-data-of-your-data/`:

| What | Purpose |
|------|--------|
| **SampleSubmission.csv** | Template: 1660 rows × SDRF columns. Fill with **actual values** (verbatim spans or "Not Applicable") — not type labels. |
| **BaselinePrompt.txt** | Full SDRF spec: categories, manuscript vs filename rules, verbatim extraction, FactorValue vs Characteristics. Use as spec for your pipeline. |
| **Training_SDRFs/HarmonizedFiles/** | Gold SDRFs: `training.csv` and `Harmonized_PXD*.csv`. Cell values = strings (e.g. "Not Applicable", "plasmodium falciparum", "20 ppm"). |
| **Training_GPT_Extract/.../PXD*_Metadata.json** | GPT baseline output per PXD. Use to compare with gold and improve prompts or training. |

**Cell values in submission:** Each cell is the **actual annotation value** (verbatim from paper/filename or "Not Applicable"). The sample’s "TextSpan" is a placeholder; your CSV must contain real values in the same shape.

---

## 7. Key rules from BaselinePrompt.txt

- Extract **only** from Title, Abstract, Methods/Materials (no Intro/Results/Discussion).
- Use **only** the listed Characteristics, Comment, and FactorValue categories.
- **Verbatim** spans from manuscript; filename tokens only when self-descriptive.
- FactorValue only for **experimental factors** (e.g. treatment, time); otherwise Characteristics.
- You can output JSON keyed by .raw filename then convert to the submission CSV format.

---

## 8. Data and code (official sources)

- **Kaggle competition:** [Harmonizing the Data of your Data](https://www.kaggle.com/competitions/harmonizing-the-data-of-your-data) — Data tab. **Official GitHub:** [NCEMS/Kaggle-Harmonizing-the-data-of-your-data](https://github.com/NCEMS/Kaggle-Harmonizing-the-data-of-your-data) — `src/Scoring.py` for local mean F1.

---

## 9. How to compete and aim for a win (SDRF-specific)

### 9.1 Pipeline shape

- **Input:** Paper text (from Training_PubText or Test_PubText JSON). You may also need the list of .raw filenames per PXD (from gold SDRF or sample submission).
- **Output:** One row per sample in the exact SampleSubmission.csv format; each cell = **value** (verbatim span or "Not Applicable").
- **Metric:** Mean F1 over (PXD, column), so **correct set of values per column per PXD** matters; avoid wrong entities (precision) and missing entities (recall).

### 9.2 Baseline

- Run **BaselinePrompt.txt** with an LLM (e.g. GPT) on training papers; convert output JSON to CSV. Compare to Training_SDRFs with the official **Scoring.py** to get a local F1.
- Use **Training_GPT_Extract** as a reference: compare GPT output to gold to see systematic errors (missing columns, wrong categories, paraphrasing).

### 9.3 Ways to improve

- **Prompting:** Few-shot examples from gold SDRFs, clearer category definitions, strict "verbatim only" and "Not Applicable when unsure" instructions.
- **Post-processing:** Map predicted phrases to gold-like values via string similarity (>= 0.80) to reduce penalty for minor wording differences.
- **Coverage:** Ensure every (PXD, column) that has at least one non-"Not Applicable" value in gold gets at least one predicted value (recall). Avoid inventing entities (precision).
- **Data:** If you have (paper, gold SDRF) pairs, fine-tune a model to predict SDRF from text, or use silver labels from GPT + validation against gold.

### 9.4 Practical tips

- **Reproducibility:** Fix seeds; document prompt/model version in README for final submission.
- **Local scoring:** Run **Scoring.py** on a train/val split (same format as submission) to tune without burning leaderboard submissions (5/day limit).
- **Final package:** ZIP = submission.csv + minimal pipeline.py + requirements.txt (+ optional README); or contribute the same via GitHub PR under Submissions/your-name/.

---

## 10. Checklist before submitting

- [ ] Submission CSV has **exactly** the same columns and row structure as **SampleSubmission.csv** (no extra index column).
- [ ] Each cell contains an **actual value** (verbatim or "Not Applicable"), not a type label like "TextSpan".
- [ ] You have run the **official evaluation** (notebook or Scoring.py) locally if possible to sanity-check score.
- [ ] For final submission: ZIP includes submission.csv + minimal working pipeline + requirements.txt; or PR to GitHub with the same under Submissions/your-name/.

---

## 11. Quick links and next steps

- [Kaggle competition](https://www.kaggle.com/competitions/harmonizing-the-data-of-your-data)
- [Official GitHub (NCEMS)](https://github.com/NCEMS/Kaggle-Harmonizing-the-data-of-your-data) — Scoring, repo layout, PR guide
- [Data harmonization primer (Nature)](https://www.nature.com/articles/s41597-024-02956-3)

**Next steps:** (1) Load Test_PubText and build a pipeline: paper JSON -> SDRF CSV. (2) Score it locally with Scoring.py against training gold (hold out some PXDs) to approximate leaderboard. (3) Iterate on prompts or models to maximize mean F1. (4) Submit CSV for leaderboard; for final, upload ZIP or open a PR with your pipeline.
