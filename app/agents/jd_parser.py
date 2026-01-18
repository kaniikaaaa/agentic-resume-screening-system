import json
import logging

from app.services.llm_service import LLMService
from app.services.skill_extractor import extract_skills_from_text, extract_experience_requirement

logger = logging.getLogger(__name__)


class JDParserAgent:
    """Agent for parsing job description text and extracting requirements."""

    def __init__(self):
        self.llm = LLMService()

    def _rule_based_parse(self, jd_text: str) -> dict:
        """
        Fallback parsing using rule-based extraction.

        Args:
            jd_text: Raw job description text

        Returns:
            Structured JD data
        """
        skills = extract_skills_from_text(jd_text)
        experience_req = extract_experience_requirement(jd_text)

        # If no skills found, mark as vague
        jd_clarity = "clear" if skills else "vague"

        return {
            "required_skills": skills,
            "experience_required": experience_req,
            "jd_clarity": jd_clarity,
            "source": "rule_based"
        }

    def parse(self, jd_text: str) -> dict:
        """
        Parse job description to extract required skills and experience.

        Attempts LLM-based extraction first, falls back to rule-based
        extraction if LLM fails or is unavailable.

        Args:
            jd_text: Raw job description text

        Returns:
            Dict with required_skills, experience_required, jd_clarity, and source
        """
        try:
            llm_output = self.llm.extract_jd_info(jd_text)

            logger.debug("LLM raw output (JD): %s", llm_output)

            data = json.loads(llm_output)

            # If required_skills empty, treat JD as vague, NOT as failure
            if not data.get("required_skills"):
                data["jd_clarity"] = "vague"
                data["source"] = "LLM"
                return data

            # Normal case
            data["source"] = "LLM"
            return data

        except Exception as e:
            logger.warning("LLM failed, falling back to rule-based parsing: %s", e)

            return self._rule_based_parse(jd_text)
