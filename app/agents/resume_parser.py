from app.services.llm_service import LLMService
import json

class ResumeParserAgent:
    def __init__(self):
        self.llm = LLMService()

    def parse(self, resume_text: str):
        try:
            llm_output = self.llm.extract_resume_info(resume_text)

            print("\n===== LLM RAW OUTPUT (RESUME) =====")
            print(llm_output)

            data = json.loads(llm_output)

            if not data.get("skills"):
                raise ValueError("LLM returned empty skills")

            data["source"] = "LLM"
            return data

        except Exception as e:
            print("\n⚠️ LLM FAILED, FALLING BACK TO RULE-BASED:", e)

            return {
                "skills": [],
                "experience_years": 0,
                "projects": [],
                "source": "rule_based_fallback"
            }
