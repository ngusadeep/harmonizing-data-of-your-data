# SDRF submission pipeline

Minimal pipeline to produce `submission.csv` for the [Harmonizing the Data of your Data](https://www.kaggle.com/competitions/harmonizing-the-data-of-your-data) competition.

## What it does

1. Loads **SampleSubmission.csv** (template with ID, PXD, Raw Data File, Usage and all SDRF columns).
2. For each test **PXD**, loads paper text from **Test PubText** (`harmonizing-the-data-of-your-data/Test PubText/Test PubText/<PXD>_PubText.json`).
3. **Extracts** SDRF metadata (placeholder or LLM).
4. Fills the template and writes **submission.csv** in the same format.

## Run (placeholder)

Produces a valid submission with "Not Applicable" in every prediction cell:

```bash
pip install -r requirements.txt
python pipeline.py
```

Output: `submission.csv` (same columns and row order as SampleSubmission).

## Run with LLM extraction

To use GPT for extraction (better score):

1. Install: `pip install openai`
2. Set your API key: `set OPENAI_API_KEY=sk-...` (Windows) or `export OPENAI_API_KEY=sk-...` (Linux/Mac)
3. Run: `python pipeline.py`

The script uses **BaselinePrompt.txt** as the system prompt and sends each test paper + raw file list to the API, then maps the returned JSON into the submission columns.

## Project layout

- `pipeline.py` — main script
- `requirements.txt` — pandas, openai
- `submission.csv` — generated submission (after run)
- `harmonizing-the-data-of-your-data/` — competition data (SampleSubmission, Test PubText, BaselinePrompt, Training_SDRFs, etc.)

## Next steps to improve score

- Replace `extract_placeholder` / tune `extract_with_llm` (e.g. few-shot examples from training gold).
- Use **Training_SDRFs** and **Training_GPT_Extract** to validate and improve prompts.
- Run official **Scoring.py** (from the [competition GitHub](https://github.com/NCEMS/Kaggle-Harmonizing-the-data-of-your-data)) on a train/val split to approximate leaderboard F1.
