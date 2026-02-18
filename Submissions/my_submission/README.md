# My Submission — SDRF Extraction

## What I Did

- **Task:** Extract SDRF metadata from proteomics paper text (title, abstract, methods) and produce one row per (PXD, raw file) in the competition CSV format.
- **Approach:** Use the competition’s **BaselinePrompt.txt** as the system prompt and call an LLM once per PXD (or in a **single batch** for all PXDs) to get JSON: for each raw filename, a map of SDRF column names to verbatim values. Only verbatim text from the manuscript is used; anything not extracted is filled as `"Not Applicable"`.
- **Modes:**  
  - **Placeholder** (no API key): all cells `"Not Applicable"`; good for checking format.  
  - **OpenAI:** `LLM_PROVIDER=openai` + `OPENAI_API_KEY`; supports **batch mode** (one request, baseline sent once) when total input fits.  
  - **Ollama:** `LLM_PROVIDER=ollama`; same batch option for local runs.
- **Output:** `submission.csv` with the same columns and row order as SampleSubmission; only the prediction columns are filled (values or `"Not Applicable"`).

## How to Run

1. **Install**
   ```bash
   pip install -r requirements.txt
   ```

2. **Data**  
   From the repo root, the script expects competition data under `harmonizing-the-data-of-your-data/` (or `data/`):  
   `SampleSubmission.csv`, `BaselinePrompt.txt`, `Test PubText/Test PubText/<PXD>_PubText.json`.

3. **Create `.env` (optional)**  
   Copy the example and edit only what you need:
   ```bash
   cd Submissions/my_submission
   copy .env.example .env    # Windows
   # cp .env.example .env   # Linux / macOS
   ```
   **What to include:**

   | Mode       | In `.env` |
   |------------|-----------|
   | Placeholder | No `.env`, or `LLM_PROVIDER=` (empty). No key needed. |
   | **OpenAI**  | `LLM_PROVIDER=openai`<br>`OPENAI_API_KEY=sk-your-key-here`<br>`OPENAI_MODEL=gpt-4o-mini` (or `gpt-4o`, `gpt-4o-nano`, etc.) |
   | **Ollama**  | `LLM_PROVIDER=ollama`<br>`OLLAMA_MODEL=llama3.2` (or `llama3.1`, `mistral`, `qwen2.5`, etc.)<br>`OLLAMA_BASE_URL=http://localhost:11434` (default; change if Ollama runs elsewhere) |

   **Example `.env` for OpenAI:**
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-...
   OPENAI_MODEL=gpt-4o-mini
   ```

   **Example `.env` for Ollama:**
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama3.2
   OLLAMA_BASE_URL=http://localhost:11434
   ```

   (Omit `OPENAI_*` when using Ollama; omit `OLLAMA_*` when using OpenAI. Do not commit `.env`.)

4. **Run**
   ```bash
   python pipeline.py
   ```
   - **Placeholder:** No `.env` or `LLM_PROVIDER=` → fast run, all cells `"Not Applicable"`.
   - **OpenAI:** `.env` with `LLM_PROVIDER=openai` and `OPENAI_API_KEY` → uses `OPENAI_MODEL` (default `gpt-4o-mini`).
   - **Ollama:** `.env` with `LLM_PROVIDER=ollama` → uses `OLLAMA_MODEL`; ensure [Ollama](https://ollama.com) is installed and running (`ollama serve` or start the app).

5. **Output**  
   `submission.csv` is written in the same folder. Upload it (or this ZIP) to the Kaggle competition.

## Kaggle Notebook

A notebook **`kaggle_notebook.ipynb`** runs the same pipeline on Kaggle (no local data or `.env`). It uses the competition dataset and writes `submission.csv` to the notebook output.

1. **Upload** the notebook to the competition (or copy it into a new Kaggle notebook and add the competition dataset as input).
2. **Secrets:** In the notebook’s right panel: **Add-ons → Secrets**. Add:
   - **`OPENAI_API_KEY`** — your OpenAI API key (required for extraction; omit for placeholder).
   - **`OPENAI_MODEL`** (optional) — e.g. `gpt-4o-mini` or `gpt-4o` (default: `gpt-4o-mini`).
   - **`USE_BATCH`** (optional) — `1` or `0` (notebook currently runs per-PXD only; reserved for future use).
3. **Run All**, then **Submit** the notebook to the competition. The generated `submission.csv` will be in the output.

## References

- [Competition](https://www.kaggle.com/competitions/harmonizing-the-data-of-your-data)
- [Official repo](https://github.com/NCEMS/Kaggle-Harmonizing-the-data-of-your-data) — BaselinePrompt and scoring.
