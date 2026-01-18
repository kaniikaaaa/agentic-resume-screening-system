import os
import time
import logging
from google import genai

logger = logging.getLogger(__name__)

# Toggle to enable / disable LLM usage
# By default it is ON. You can turn it OFF using:
# Linux/Mac: export USE_LLM="false"
# PowerShell: $env:USE_LLM="false"
USE_LLM = os.getenv("USE_LLM", "true").lower() == "true"

# Model configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-flash-lite-latest")
RETRY_DELAY_SECONDS = 10


class LLMService:
    """Service for interacting with Google Gemini LLM."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if USE_LLM and not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        if USE_LLM:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

    def _clean_json(self, text: str) -> str:
        """
        Cleans the model output to extract only valid JSON.
        Handles cases where Gemini adds explanations or ```json``` blocks.
        """
        text = text.strip()

        # Remove markdown code fences if present
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]
                # Remove language identifier (e.g., "json")
                if text.startswith("json"):
                    text = text[4:]

        # Extract JSON between first { and last }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1:
            text = text[first_brace:last_brace + 1]

        return text.strip()

    def _call_with_retry(self, prompt: str) -> str:
        """
        Call the LLM with one retry on failure.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            Cleaned JSON response from the LLM
        """
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
        except Exception as e:
            logger.warning("LLM error, retrying once after %d seconds: %s", RETRY_DELAY_SECONDS, e)
            time.sleep(RETRY_DELAY_SECONDS)
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )

        raw = response.text
        cleaned = self._clean_json(raw)
        return cleaned

    def extract_resume_info(self, resume_text: str) -> str:
        """
        Extract structured data from resume text using LLM.

        Args:
            resume_text: Raw text from resume

        Returns:
            JSON string with skills, experience_years, and projects

        Raises:
            Exception: If LLM is disabled by configuration
        """
        if not USE_LLM:
            raise Exception("LLM disabled by configuration")

        prompt = f"""
You are an AI recruiter assistant.
Extract structured data from the resume below.

Return ONLY valid JSON in this format:
{{
  "skills": ["python", "fastapi"],
  "experience_years": 2,
  "projects": ["project1", "project2"]
}}

Resume:
{resume_text}
"""
        return self._call_with_retry(prompt)

    def extract_jd_info(self, jd_text: str) -> str:
        """
        Extract structured data from job description using LLM.

        Args:
            jd_text: Raw job description text

        Returns:
            JSON string with required_skills, experience_required, and jd_clarity

        Raises:
            Exception: If LLM is disabled by configuration
        """
        if not USE_LLM:
            raise Exception("LLM disabled by configuration")

        prompt = f"""
You are an AI recruiter assistant.
Extract structured data from the job description below.

Return ONLY valid JSON in this format:
{{
  "required_skills": ["python", "fastapi"],
  "experience_required": {{"min": 2, "max": 4}},
  "jd_clarity": "clear"
}}

Job Description:
{jd_text}
"""
        return self._call_with_retry(prompt)
