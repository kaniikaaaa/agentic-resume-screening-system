"""Runtime configuration, read once at import."""

import os


def _flag(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


# Gemini is optional. Without a key the pipeline runs in deterministic mode.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-flash-lite-latest").strip()

USE_LLM = _flag("USE_LLM") and bool(GEMINI_API_KEY)

# Serverless functions bill by wall-clock, so the LLM gets a hard ceiling and a
# single fast retry rather than the long sleep a local script could afford.
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
LLM_RETRY_DELAY_SECONDS = float(os.getenv("LLM_RETRY_DELAY_SECONDS", "1.5"))

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
MAX_JD_CHARS = int(os.getenv("MAX_JD_CHARS", "40000"))

# Only the text the model needs; resumes past this are almost always noise.
MAX_RESUME_CHARS_FOR_LLM = int(os.getenv("MAX_RESUME_CHARS_FOR_LLM", "12000"))
MAX_JD_CHARS_FOR_LLM = int(os.getenv("MAX_JD_CHARS_FOR_LLM", "8000"))
