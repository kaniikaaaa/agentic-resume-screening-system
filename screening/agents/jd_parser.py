from screening.services.llm_service import LLMService
from screening.services import taxonomy


class JDParserAgent:
    """Turns a job description into {required_skills, experience_required, jd_clarity}.

    An empty skill list is treated as a vague JD, not a parse failure: some job
    descriptions genuinely name no technology, and that fact is itself the
    signal the DecisionAgent needs to route the case to a human.
    """

    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or LLMService()

    def parse(self, jd_text: str) -> dict:
        if self.llm.available:
            try:
                data = self.llm.extract_jd_info(jd_text)
                skills = taxonomy.canonical_set(data.get("required_skills", []))
                return {
                    "required_skills": skills,
                    "experience_required": _clean_requirement(
                        data.get("experience_required")
                    ),
                    "jd_clarity": _clarity(data.get("jd_clarity"), skills),
                    "source": "llm",
                    "note": None,
                }
            except Exception as exc:
                fallback = self._rule_based(jd_text)
                fallback["note"] = f"Deterministic fallback used — {exc}"
                return fallback

        result = self._rule_based(jd_text)
        result["note"] = f"Deterministic mode — {self.llm.status}"
        return result

    @staticmethod
    def _rule_based(jd_text: str) -> dict:
        skills = taxonomy.extract_required_skills(jd_text)
        return {
            "required_skills": skills,
            "experience_required": taxonomy.extract_experience_requirement(jd_text),
            "jd_clarity": _clarity(None, skills),
            "source": "rule_based",
            "note": None,
        }


def _clarity(stated, skills: list[str]) -> str:
    """A JD naming fewer than two technologies cannot be screened against."""
    if len(skills) < 2:
        return "vague"
    if isinstance(stated, str) and stated.lower() in {"clear", "vague"}:
        return stated.lower()
    return "clear"


def _clean_requirement(value) -> dict | None:
    """Normalise the experience range, tolerating the model's looser shapes."""
    if not isinstance(value, dict):
        return None

    minimum = _as_int(value.get("min"))
    maximum = _as_int(value.get("max"))

    if minimum is None and maximum is None:
        return None
    if minimum is None:
        minimum = 0
    if maximum is not None and maximum < minimum:
        maximum = None

    return {"min": minimum, "max": maximum}


def _as_int(value) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return max(0, min(int(float(value)), 60))
    except (TypeError, ValueError):
        return None
