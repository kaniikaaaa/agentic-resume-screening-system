import logging

from screening.services.llm_service import LLMService
from screening.services import taxonomy

logger = logging.getLogger(__name__)


class ResumeParserAgent:
    """Turns resume text into {skills, experience_years, projects}.

    Tries the LLM first for semantic reach, then falls back to vocabulary
    matching. The fallback returns real data rather than empty lists, so an
    unconfigured or rate-limited deploy still screens candidates instead of
    scoring everyone zero.
    """

    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or LLMService()

    def parse(self, resume_text: str) -> dict:
        if self.llm.available:
            try:
                data = self.llm.extract_resume_info(resume_text)
                return {
                    "skills": taxonomy.canonical_set(data.get("skills", [])),
                    "experience_years": _coerce_years(data.get("experience_years")),
                    "projects": [str(p) for p in (data.get("projects") or [])][:8],
                    "source": "llm",
                    "note": None,
                }
            except Exception as exc:
                logger.warning("Resume LLM parse failed, falling back to rules: %s", exc)
                fallback = self._rule_based(resume_text)
                fallback["note"] = f"Deterministic fallback used — {exc}"
                return fallback

        result = self._rule_based(resume_text)
        result["note"] = f"Deterministic mode — {self.llm.status}"
        return result

    @staticmethod
    def _rule_based(resume_text: str) -> dict:
        return {
            "skills": taxonomy.extract_skills(resume_text),
            "experience_years": taxonomy.extract_experience_years(resume_text),
            "projects": [],
            "source": "rule_based",
            "note": None,
        }


def _coerce_years(value) -> float:
    """The model occasionally answers "3 years" or null instead of 3."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return max(0.0, min(float(value), 60.0))
    try:
        return max(0.0, min(float(str(value).split()[0]), 60.0))
    except (ValueError, IndexError):
        return 0.0
