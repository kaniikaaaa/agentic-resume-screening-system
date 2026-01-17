import os
import time
from google import genai

# Toggle to enable / disable LLM usage
# By default it is ON. You can turn it OFF using:
# PowerShell:
#   $env:USE_LLM="false"
USE_LLM = os.getenv("USE_LLM", "true").lower() == "true"


class LLMService:
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

        # Extract JSON between first { and last }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1:
            text = text[first_brace:last_brace + 1]

        return text.strip()

    def extract_resume_info(self, resume_text: str):
        # If LLM is disabled, force fallback
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

        try:
            response = self.client.models.generate_content(
                model="models/gemini-flash-lite-latest",
                contents=prompt
            )
        except Exception as e:
            print("⚠️ LLM error, retrying once after 10 seconds...")
            print(e)
            time.sleep(10)
            response = self.client.models.generate_content(
                model="models/gemini-flash-lite-latest",
                contents=prompt
            )

        raw = response.text
        cleaned = self._clean_json(raw)
        return cleaned

    def extract_jd_info(self, jd_text: str):
        # If LLM is disabled, force fallback
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

        try:
            response = self.client.models.generate_content(
                model="models/gemini-flash-lite-latest",
                contents=prompt
            )
        except Exception as e:
            print("⚠️ LLM error, retrying once after 10 seconds...")
            print(e)
            time.sleep(10)
            response = self.client.models.generate_content(
                model="models/gemini-flash-lite-latest",
                contents=prompt
            )

        raw = response.text
        cleaned = self._clean_json(raw)
        return cleaned
