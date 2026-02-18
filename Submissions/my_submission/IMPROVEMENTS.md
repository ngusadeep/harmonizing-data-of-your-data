# Improving Your Score

The leaderboard uses **mean F1** over (PXD, column): set-based comparison with string similarity ≥ 0.80. Columns that are all "Not Applicable" are **excluded** from scoring.

## Quick wins (no code change)

1. **Use full manuscript per PXD**  
   In `.env` set:
   ```env
   USE_BATCH=0
   ```
   Batch mode truncates each paper (~6k chars) to fit one request. Per-PXD sends up to 120k chars per paper, so the model sees more text and can extract more.

2. **Stronger model (OpenAI)**  
   In `.env` set:
   ```env
   OPENAI_MODEL=gpt-4o
   ```
   or `gpt-4o-nano` for a balance of cost and quality. Better models usually improve recall and exact column names.

3. **Exact column names**  
   The pipeline now passes the list of expected SDRF columns into every prompt so the model uses the exact keys we need. No extra config.

## .env for higher score (example)

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
USE_BATCH=0
```

Then run `python pipeline.py`. Expect more API calls and higher cost, but better coverage.

## Further ideas

- **Few-shot:** Add 1–2 (paper, SDRF) examples from training data to the system or user prompt.
- **Training data:** Inspect `Training_SDRFs/HarmonizedFiles/` and `Training_GPT_Extract/` to see which columns and phrasings appear often; tune the prompt or add hints.
- **Local scoring:** Use the repo’s `src/Scoring` (if available) to compare your submission to `training.csv` and iterate without burning Kaggle submissions.
