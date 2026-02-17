# My Submission — SDRF extraction pipeline

Brief description: Extract SDRF (Sample and Data Relationship Format) metadata from proteomics publication text. Pipeline loads test papers (JSON), runs a placeholder or LLM-based extractor, and produces a submission CSV in the exact competition format.

## Method

- **Data:** Test publication text from `Test_PubText/<PXD>_PubText.json` (TITLE, ABSTRACT, METHODS). Sample submission template defines row order and columns.
- **Preprocessing:** For each PXD, extract in-scope manuscript text (Title + Abstract + Methods per BaselinePrompt). Raw file list from submission template or from JSON `Raw Data Files`.
- **Extraction:**  
  - **Placeholder (default):** All prediction cells set to `"Not Applicable"` (valid baseline).  
  - **LLM (optional):** If `OPENAI_API_KEY` is set, call GPT (gpt-4o-mini) with BaselinePrompt.txt as system prompt; parse returned JSON and map keys to submission columns.
- **Post-processing:** Preserve exact row order and column order from SampleSubmission.csv; fill only prediction columns (all SDRF fields); ID, PXD, Raw Data File, Usage come from template.
- **Key details:** One API call per test PXD; response format is JSON keyed by .raw filename with SDRF headers as keys and lists of verbatim spans as values.

## Results

- **Local F1 Score:** N/A (placeholder yields all "Not Applicable"; run with `OPENAI_API_KEY` for real extraction).
- **Kaggle Score:** Submit `submission.csv` to the leaderboard to obtain.
- **Findings:** Placeholder confirms format and row count; LLM path is intended to improve recall/precision over baseline.

## Installation & Usage

```bash
pip install -r requirements.txt
python pipeline.py
```

**Data layout:** Competition data must be available from the repository root, e.g.:

- `harmonizing-the-data-of-your-data/SampleSubmission.csv`
- `harmonizing-the-data-of-your-data/Test PubText/Test PubText/<PXD>_PubText.json`
- `harmonizing-the-data-of-your-data/BaselinePrompt.txt`

If your repo uses `data/` instead of `harmonizing-the-data-of-your-data/`, the script will use `data/` when present.

**With LLM extraction:**

```bash
set OPENAI_API_KEY=sk-your-key   # Windows
export OPENAI_API_KEY=sk-your-key   # Linux/Mac
python pipeline.py
```

**Optional local scoring (if `src/Scoring.py` exists in repo):**

```bash
python src/Scoring.py --solution path/to/solution.csv --submission Submissions/my_submission/submission.csv
```

Or run `pipeline.py` from `Submissions/my_submission/`; it will attempt to call `score()` when training solution is available.

## References

- Competition: [Harmonizing the Data of your Data](https://www.kaggle.com/competitions/harmonizing-the-data-of-your-data)
- Official repo: [NCEMS/Kaggle-Harmonizing-the-data-of-your-data](https://github.com/NCEMS/Kaggle-Harmonizing-the-data-of-your-data)
- BaselinePrompt.txt (included in competition data) for SDRF categories and extraction rules.
