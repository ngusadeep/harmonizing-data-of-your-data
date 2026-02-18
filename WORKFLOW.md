# Workflow — Harmonizing the Data of your Data

End-to-end flow from data to Kaggle submission.

---

## 1. Setup (once)

| Step | What to do |
|------|------------|
| **Data** | Competition data in `harmonizing-the-data-of-your-data/` (SampleSubmission.csv, Test PubText, BaselinePrompt.txt, Training_*). |
| **Env** | In `Submissions/my_submission/`: copy `.env.example` to `.env`, add your OpenAI key: `OPENAI_API_KEY=sk-...` |
| **Deps** | `cd Submissions/my_submission` → `pip install -r requirements.txt` |

---

## 2. Run pipeline

```text
cd Submissions/my_submission
python pipeline.py
```

- **No .env / no key** → Placeholder: all cells "Not Applicable" (fast, valid CSV).
- **With .env + key** → LLM extraction per PXD (slower, better score).

Output: `Submissions/my_submission/submission.csv` (same format as SampleSubmission).

---

## 3. Submit to Kaggle

1. Open: [competition → Submit Predictions](https://www.kaggle.com/competitions/harmonizing-the-data-of-your-data/submit).
2. Upload: `Submissions/my_submission/submission.csv`.
3. Add a short description, submit.
4. Up to **5 submissions per day**; repeat from step 2 to try new runs.

---

## 4. Improve & iterate

- Change prompt or model in `pipeline.py` → run again → new `submission.csv` → resubmit.
- Use **Training_SDRFs** + **Training_GPT_Extract** to tune; use **Scoring.py** (from [official repo](https://github.com/NCEMS/Kaggle-Harmonizing-the-data-of-your-data)) for local F1.

---

## Flow diagram

```text
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Test PubText   │     │  BaselinePrompt   │     │ SampleSubmission│
│  (PXD*.json)    │     │  (.txt)           │     │ (.csv template) │
└────────┬────────┘     └────────┬─────────┘     └────────┬────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                   ▼
                          ┌─────────────────┐
                          │  pipeline.py    │
                          │  (.env = key)   │
                          └────────┬────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
           (no key: placeholder)          (key: LLM extraction)
                    │                             │
                    └──────────────┬──────────────┘
                                   ▼
                          ┌─────────────────┐
                          │ submission.csv  │
                          └────────┬────────┘
                                   ▼
                          Kaggle Submit Predictions
```

---

## Quick reference

| Item | Location |
|------|----------|
| Pipeline | `Submissions/my_submission/pipeline.py` |
| Submission file | `Submissions/my_submission/submission.csv` |
| API key | `Submissions/my_submission/.env` (not pushed to Git) |
| Competition data | `harmonizing-the-data-of-your-data/` |
