"""
SDRF extraction pipeline — Harmonizing the Data of your Data.
Loads test papers, extracts metadata via placeholder, OpenAI, or Ollama; writes submission.csv.
Configure in .env: LLM_PROVIDER (openai | ollama | empty), model names, API key.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Protocol

import pandas as pd
import requests
from dotenv import load_dotenv
from openai import OpenAI

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent
ENV_FILE = BASE_DIR / ".env"
MANUSCRIPT_MAX_CHARS = 120_000
PREDICTION_COLUMNS_EXCLUDE = ("ID", "PXD", "Raw Data File", "Usage")
MANUSCRIPT_KEYS = ("TITLE", "ABSTRACT", "METHODS")

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# Optional: local scoring (repo must have src.Scoring)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
try:
    from src.Scoring import score as score_submission
except ImportError:
    score_submission = None


# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
class Config:
    """Environment-derived configuration. .env is loaded at module load."""

    def __init__(self) -> None:
        self.llm_provider = (os.environ.get("LLM_PROVIDER") or "").strip().lower()
        self.openai_api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
        self.openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2").strip()
        self.ollama_base_url = (
            os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
            .strip()
            .rstrip("/")
        )

        for name in ("harmonizing-the-data-of-your-data", "data"):
            d = REPO_ROOT / name
            if d.exists():
                self.data_dir = d
                break
        else:
            self.data_dir = REPO_ROOT / "harmonizing-the-data-of-your-data"

        self.sample_submission_path = self.data_dir / "SampleSubmission.csv"
        self.test_pubtext_dir = self.data_dir / "Test PubText" / "Test PubText"
        if not self.test_pubtext_dir.exists():
            self.test_pubtext_dir = self.data_dir / "Test_PubText" / "Test_PubText"
        self.baseline_prompt_path = self.data_dir / "BaselinePrompt.txt"
        self.submission_output_path = BASE_DIR / "submission.csv"

    @property
    def effective_provider(self) -> str:
        """Provider to use (empty if no prompt file)."""
        return self.llm_provider

    def mode_label(self, prompt_spec: str) -> str:
        """Human-readable mode for logging."""
        provider = self.effective_provider if prompt_spec else ""
        if provider == "openai":
            return f"OpenAI ({self.openai_model})"
        if provider == "ollama":
            return f"Ollama ({self.ollama_model})"
        return "placeholder"


# -----------------------------------------------------------------------------
# Extractors (Strategy pattern)
# -----------------------------------------------------------------------------
class SDRFExtractor(Protocol):
    """Protocol for SDRF extraction: manuscript + raw files -> per-file metadata."""

    def extract(
        self,
        manuscript_text: str,
        raw_files: list[str],
        prompt_spec: str,
    ) -> dict[str, dict]:
        """Return mapping raw_filename -> { SDRF_column -> [values] }."""
        ...


class PlaceholderExtractor:
    """No LLM; every cell becomes Not Applicable."""

    def extract(
        self,
        manuscript_text: str,
        raw_files: list[str],
        prompt_spec: str,
    ) -> dict[str, dict]:
        return {raw: {} for raw in raw_files}


class OpenAIExtractor:
    """Extract SDRF via OpenAI API."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._client: OpenAI | None = (
            OpenAI(api_key=config.openai_api_key) if config.openai_api_key else None
        )

    def extract(
        self,
        manuscript_text: str,
        raw_files: list[str],
        prompt_spec: str,
    ) -> dict[str, dict]:
        if not self._client or not self._config.openai_api_key:
            return {raw: {} for raw in raw_files}
        text = manuscript_text[:MANUSCRIPT_MAX_CHARS]
        user_content = f"MANUSCRIPT_TEXT:\n{text}\n\nRAW_FILES:\n" + "\n".join(
            raw_files
        )
        response = self._client.chat.completions.create(
            model=self._config.openai_model,
            messages=[
                {"role": "system", "content": prompt_spec},
                {"role": "user", "content": user_content},
            ],
            temperature=0,
        )
        raw_response = (response.choices[0].message.content or "").strip()
        return self._parse_response(raw_response, raw_files)

    @staticmethod
    def _parse_response(raw_response: str, raw_files: list[str]) -> dict[str, dict]:
        return _parse_llm_json_response(raw_response, raw_files)


class OllamaExtractor:
    """Extract SDRF via local Ollama API."""

    def __init__(self, config: Config) -> None:
        self._config = config

    def extract(
        self,
        manuscript_text: str,
        raw_files: list[str],
        prompt_spec: str,
    ) -> dict[str, dict]:
        text = manuscript_text[:MANUSCRIPT_MAX_CHARS]
        user_content = f"MANUSCRIPT_TEXT:\n{text}\n\nRAW_FILES:\n" + "\n".join(
            raw_files
        )
        payload = {
            "model": self._config.ollama_model,
            "messages": [
                {"role": "system", "content": prompt_spec},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
        }
        try:
            r = requests.post(
                f"{self._config.ollama_base_url}/api/chat",
                json=payload,
                timeout=300,
            )
            r.raise_for_status()
            raw_response = (r.json().get("message", {}).get("content") or "").strip()
        except Exception:
            return {raw: {} for raw in raw_files}
        return _parse_llm_json_response(raw_response, raw_files)


def _parse_llm_json_response(
    raw_response: str, raw_files: list[str]
) -> dict[str, dict]:
    """Parse JSON from LLM; strip markdown code block; normalize values to lists."""
    text = raw_response
    if "```" in text:
        for p in text.split("```"):
            p = p.strip()
            if p.lower().startswith("json"):
                p = p[4:].strip()
            if p.startswith("{"):
                text = p
                break
    try:
        out = json.loads(text)
    except json.JSONDecodeError:
        return {raw: {} for raw in raw_files}
    for raw in out:
        for k, v in list(out[raw].items()):
            if isinstance(v, str):
                out[raw][k] = [v]
    return out


def get_extractor(config: Config, prompt_spec: str) -> SDRFExtractor:
    """Factory: return the extractor for the configured provider."""
    provider = config.effective_provider if prompt_spec else ""
    if provider == "openai":
        return OpenAIExtractor(config)
    if provider == "ollama":
        return OllamaExtractor(config)
    return PlaceholderExtractor()


# -----------------------------------------------------------------------------
# Pipeline
# -----------------------------------------------------------------------------
class SDRFPipeline:
    """Orchestrates loading data, running extractor, and writing submission.csv."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._prompt_spec = self._load_baseline_prompt()
        self._extractor = get_extractor(config, self._prompt_spec)

    def _load_baseline_prompt(self) -> str:
        if self._config.baseline_prompt_path.exists():
            return self._config.baseline_prompt_path.read_text(encoding="utf-8")
        return ""

    def _load_pubtext(self, pxd: str) -> dict | None:
        path = self._config.test_pubtext_dir / f"{pxd}_PubText.json"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _get_manuscript_text(doc: dict) -> str:
        parts = [doc[k].strip() for k in MANUSCRIPT_KEYS if doc.get(k)]
        return "\n\n".join(parts)

    @staticmethod
    def _sdrf_to_row(
        raw_file: str,
        sdrf_per_file: dict[str, dict],
        pred_columns: list[str],
    ) -> dict[str, str]:
        meta = sdrf_per_file.get(raw_file, {})
        row = {}
        for col in pred_columns:
            vals = meta.get(col)
            if vals and len(vals) > 0:
                row[col] = vals[0] if isinstance(vals, list) else str(vals)
            else:
                row[col] = "Not Applicable"
        return row

    def run(self) -> Path:
        """Load template, extract per PXD, fill submission, write CSV. Returns output path."""
        if not self._config.sample_submission_path.exists():
            raise FileNotFoundError(
                f"Sample submission not found: {self._config.sample_submission_path}"
            )

        sub = pd.read_csv(self._config.sample_submission_path, index_col=0)
        template_columns = list(sub.columns)
        pred_columns = [
            c for c in template_columns if c not in PREDICTION_COLUMNS_EXCLUDE
        ]

        print(f"Data dir: {self._config.data_dir}")
        print(f"Mode: {self._config.mode_label(self._prompt_spec)}")

        out_df = sub.copy()
        for pxd, group in sub.groupby("PXD"):
            raw_files = group["Raw Data File"].unique().tolist()
            doc = self._load_pubtext(pxd)
            if doc is None:
                manuscript_text = ""
                print(f"Warning: no PubText for {pxd}")
            else:
                manuscript_text = self._get_manuscript_text(doc)
                if "Raw Data Files" in doc:
                    raw_files = doc["Raw Data Files"]

            sdrf_per_file = self._extractor.extract(
                manuscript_text, raw_files, self._prompt_spec
            )
            for idx, r in group.iterrows():
                row_vals = self._sdrf_to_row(
                    r["Raw Data File"], sdrf_per_file, pred_columns
                )
                for col in pred_columns:
                    out_df.at[idx, col] = row_vals[col]

        out_df.to_csv(self._config.submission_output_path, index=True)
        print(f"Wrote {self._config.submission_output_path} ({len(out_df)} rows)")

        self._maybe_run_local_scoring(out_df)
        return self._config.submission_output_path

    def _maybe_run_local_scoring(self, out_df: pd.DataFrame) -> None:
        """If src.Scoring exists in repo, compute and print local F1."""
        if score_submission is None:
            return
        try:
            solution_path = (
                self._config.data_dir
                / "Training_SDRFs"
                / "HarmonizedFiles"
                / "training.csv"
            )
            if solution_path.exists():
                solution_df = pd.read_csv(solution_path, index_col=0)
                _, f1 = score_submission(solution_df, out_df, "ID")
                print(f"Local F1 (vs training): {f1:.6f}")
        except Exception as e:
            print(f"(Optional scoring skipped: {e})")


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
def main() -> Path:
    config = Config()
    pipeline = SDRFPipeline(config)
    return pipeline.run()


if __name__ == "__main__":
    main()
