import json
import logging

from app.services.llm_service import LLMService
from app.services.skill_extractor import extract_skills_from_text, extract_experience_years

logger = logging.getLogger(__name__)


class ResumeParserAgent:
    """Agent for parsing resume text and extracting structured data."""

    def __init__(self):
        self.llm = LLMService()

    def _rule_based_parse(self, resume_text: str) -> dict:
        """
        Fallback parsing using rule-based extraction.

        Args:
            resume_text: Raw resume text

        Returns:
            Structured resume data
        """
        skills = extract_skills_from_text(resume_text)
        experience_years = extract_experience_years(resume_text)

        return {
            "skills": skills,
            "experience_years": experience_years,
            "projects": [],  # Rule-based extraction doesn't extract projects
            "source": "rule_based"
        }

    def parse(self, resume_text: str) -> dict:
        """
        Parse resume text to extract skills, experience, and projects.

        Attempts LLM-based extraction first, falls back to rule-based
        extraction if LLM fails or is unavailable.

        Args:
            resume_text: Raw text extracted from resume

        Returns:
            Dict with skills, experience_years, projects, and source
        """
        try:
            llm_output = self.llm.extract_resume_info(resume_text)

            logger.debug("LLM raw output (resume): %s", llm_output)

            data = json.loads(llm_output)

            if not data.get("skills"):
                raise ValueError("LLM returned empty skills")

            data["source"] = "LLM"
            return data

        except Exception as e:
            logger.warning("LLM failed, falling back to rule-based parsing: %s", e)

            return self._rule_based_parse(resume_text)
