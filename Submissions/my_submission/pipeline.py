"""
SDRF extraction pipeline for Harmonizing the Data of your Data.
Loads test papers, extracts metadata (placeholder or LLM), generates submission.csv.
Put OPENAI_API_KEY in .env (or set env var) to use GPT extraction.
"""
from pathlib import Path
import json
import os
import pandas as pd

# Load .env from this folder so OPENAI_API_KEY is available
_env = Path(__file__).resolve().parent / ".env"
if _env.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env)
    except ImportError:
        pass

# Paths: run from Submissions/my_submission/; data can be repo_root/harmonizing-the-data-of-your-data or repo_root/data
BASE = Path(__file__).resolve().parent
REPO_ROOT = BASE.parent.parent
for data_name in ("harmonizing-the-data-of-your-data", "data"):
    _data = REPO_ROOT / data_name
    if _data.exists():
        DATA_DIR = _data
        break
else:
    DATA_DIR = REPO_ROOT / "harmonizing-the-data-of-your-data"

SAMPLE_SUBMISSION = DATA_DIR / "SampleSubmission.csv"
TEST_PUBTEXT = DATA_DIR / "Test PubText" / "Test PubText"
if not TEST_PUBTEXT.exists():
    TEST_PUBTEXT = DATA_DIR / "Test_PubText" / "Test PubText"
BASELINE_PROMPT = DATA_DIR / "BaselinePrompt.txt"


def load_pubtext(pxd: str) -> dict | None:
    """Load publication text JSON for a PXD. Returns None if not found."""
    path = TEST_PUBTEXT / f"{pxd}_PubText.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_manuscript_text(doc: dict) -> str:
    """Extract in-scope text: Title, Abstract, Methods (per BaselinePrompt)."""
    parts = []
    for key in ("TITLE", "ABSTRACT", "METHODS"):
        if key in doc and doc[key]:
            parts.append(doc[key].strip())
    return "\n\n".join(parts)


def extract_sdrf(manuscript_text: str, raw_files: list[str], use_llm: bool, prompt_spec: str) -> dict:
    """
    Extract SDRF metadata per raw file.
    Returns dict: raw_filename -> { SDRF_column: [value1, ...] }
    """
    if use_llm and prompt_spec:
        return _extract_with_llm(manuscript_text, raw_files, prompt_spec)
    return _extract_placeholder(raw_files)


def _extract_placeholder(raw_files: list[str]) -> dict:
    """Placeholder: "Not Applicable" for every cell. Replace with real extraction for better score."""
    return {raw: {} for raw in raw_files}


def _extract_with_llm(manuscript_text: str, raw_files: list[str], prompt_spec: str) -> dict:
    """Call OpenAI API to extract SDRF per raw file."""
    try:
        import openai
    except ImportError:
        return _extract_placeholder(raw_files)
    client = openai.OpenAI()
    raw_list = "\n".join(raw_files)
    user_content = f"MANUSCRIPT_TEXT:\n{manuscript_text[:120000]}\n\nRAW_FILES:\n{raw_list}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt_spec},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
    )
    text = response.choices[0].message.content.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        out = json.loads(text)
    except json.JSONDecodeError:
        return _extract_placeholder(raw_files)
    for raw in out:
        for k, v in list(out[raw].items()):
            if isinstance(v, str):
                out[raw][k] = [v]
    return out


def _sdrf_to_row(raw_file: str, sdrf_dict: dict, pred_columns: list) -> dict:
    """Build prediction column -> value for one raw file."""
    file_meta = sdrf_dict.get(raw_file, {})
    row = {}
    for col in pred_columns:
        vals = file_meta.get(col)
        if vals and len(vals) > 0:
            row[col] = vals[0] if isinstance(vals, list) else str(vals)
        else:
            row[col] = "Not Applicable"
    return row


def main():
    use_llm = bool(os.environ.get("OPENAI_API_KEY"))
    print(f"Data dir: {DATA_DIR}")
    print(f"Using {'LLM extraction' if use_llm else 'placeholder (Not Applicable)'}")

    if not SAMPLE_SUBMISSION.exists():
        raise FileNotFoundError(f"Sample submission not found: {SAMPLE_SUBMISSION}")
    sub = pd.read_csv(SAMPLE_SUBMISSION, index_col=0)
    template_columns = list(sub.columns)
    pred_columns = [c for c in template_columns if c not in ("ID", "PXD", "Raw Data File", "Usage")]

    prompt_spec = ""
    if BASELINE_PROMPT.exists():
        prompt_spec = BASELINE_PROMPT.read_text(encoding="utf-8")

    out_df = sub.copy()
    for pxd, group in sub.groupby("PXD"):
        raw_files = group["Raw Data File"].unique().tolist()
        doc = load_pubtext(pxd)
        if doc is None:
            manuscript_text = ""
            print(f"Warning: no PubText for {pxd}")
        else:
            manuscript_text = get_manuscript_text(doc)
            if "Raw Data Files" in doc:
                raw_files = doc["Raw Data Files"]

        sdrf_per_file = extract_sdrf(manuscript_text, raw_files, use_llm, prompt_spec)
        for idx, r in group.iterrows():
            filled = _sdrf_to_row(r["Raw Data File"], sdrf_per_file, pred_columns)
            for col in pred_columns:
                out_df.at[idx, col] = filled[col]

    out_path = BASE / "submission.csv"
    out_df.to_csv(out_path, index=True)
    print(f"Wrote {out_path} ({len(out_df)} rows)")

    # Optional: score locally if src.Scoring is available
    try:
        import sys
        src_path = REPO_ROOT / "src"
        if src_path.exists() and str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from src.Scoring import score
        solution_path = DATA_DIR / "Training_SDRFs" / "HarmonizedFiles" / "training.csv"
        if solution_path.exists():
            solution_df = pd.read_csv(solution_path, index_col=0)
            eval_df, f1 = score(solution_df, out_df, "ID")
            print(f"Local F1 Score (vs training): {f1:.6f}")
    except Exception as e:
        print(f"(Optional scoring skipped: {e})")

    return out_path


if __name__ == "__main__":
    main()
