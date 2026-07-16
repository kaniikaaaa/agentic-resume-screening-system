"""Gemini wrapper.

Deliberately incapable of taking the process down: if the key is missing, the
SDK is absent, the quota is spent or the model returns prose instead of JSON,
this raises `LLMUnavailable` and the calling agent falls back to deterministic
parsing. The previous version raised at construction time when no key was set,
which made an unconfigured deploy fail at import rather than degrade.
"""

import json
import time

from screening import config


class LLMUnavailable(Exception):
    """The model could not be reached, or gave nothing usable."""


class LLMService:
    def __init__(self) -> None:
        self._client = None
        self._init_error: str | None = None

        if not config.USE_LLM:
            self._init_error = (
                "GEMINI_API_KEY is not set"
                if not config.GEMINI_API_KEY
                else "USE_LLM is disabled"
            )
            return

        try:
            from google import genai

            self._client = genai.Client(api_key=config.GEMINI_API_KEY)
        except ImportError:
            self._init_error = "google-genai is not installed"
        except Exception as exc:
            self._init_error = f"Gemini client failed to initialise: {exc}"

    @property
    def available(self) -> bool:
        return self._client is not None

    @property
    def status(self) -> str:
        return "ready" if self.available else (self._init_error or "unavailable")

    def _generate(self, prompt: str) -> str:
        if not self._client:
            raise LLMUnavailable(self._init_error or "LLM is not configured")

        last_error: Exception | None = None

        # One retry only. A serverless invocation is billed by wall-clock and
        # capped, so a long backoff would burn the request's whole budget and
        # still time out.
        for attempt in range(2):
            try:
                response = self._client.models.generate_content(
                    model=config.GEMINI_MODEL,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "temperature": 0.1,
                    },
                )
                text = (response.text or "").strip()
                if not text:
                    raise LLMUnavailable("The model returned an empty response")
                return text
            except Exception as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(config.LLM_RETRY_DELAY_SECONDS)

        raise LLMUnavailable(f"Gemini request failed: {last_error}")

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Parse the model's reply, tolerating fences and stray commentary."""
        text = raw.strip()

        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]
                if text.lstrip().lower().startswith("json"):
                    text = text.lstrip()[4:]

        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            text = text[start : end + 1]

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMUnavailable(f"The model did not return valid JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise LLMUnavailable("The model returned JSON, but not an object")

        return data

    def extract_resume_info(self, resume_text: str) -> dict:
        prompt = f"""You are screening a resume for a hiring team.

Extract the candidate's technical skills, total years of professional
experience, and notable projects.

Rules:
- List skills as they are conventionally written (Python, PostgreSQL, Node.js).
- Include only skills the resume actually evidences. Do not infer.
- experience_years is a number: total professional experience, internships
  excluded. Use 0 if the resume shows no professional work history.
- Return JSON only, matching this shape exactly:

{{"skills": ["Python", "FastAPI"], "experience_years": 3, "projects": ["..."]}}

Resume:
{resume_text[: config.MAX_RESUME_CHARS_FOR_LLM]}
"""
        data = self._parse_json(self._generate(prompt))

        skills = data.get("skills")
        if not isinstance(skills, list) or not skills:
            raise LLMUnavailable("No skills were found in the resume")

        return data

    def extract_jd_info(self, jd_text: str) -> dict:
        prompt = f"""You are analysing a job description for a hiring team.

Extract the required technical skills and the experience requirement.

Rules:
- required_skills: only concrete, checkable technical skills. Exclude soft
  skills ("team player", "quick learner", "good communication").
- experience_required: {{"min": n, "max": n}}. Use null for max when the JD is
  open-ended ("5+ years"). Use null for the whole field if it is unstated.
- jd_clarity: "clear" if the JD names specific technologies and an experience
  level; "vague" if it is generic enough that two recruiters would disagree on
  who qualifies.
- Return JSON only, matching this shape exactly:

{{"required_skills": ["Python"], "experience_required": {{"min": 2, "max": 4}}, "jd_clarity": "clear"}}

Job description:
{jd_text[: config.MAX_JD_CHARS_FOR_LLM]}
"""
        return self._parse_json(self._generate(prompt))
