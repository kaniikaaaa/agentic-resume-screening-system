from app.services.llm_service import LLMService
import json

class JDParserAgent:
    def __init__(self):
        self.llm = LLMService()

    def parse(self, jd_text: str):
        try:
            llm_output = self.llm.extract_jd_info(jd_text)

            print("\n===== LLM RAW OUTPUT (JD) =====")
            print(llm_output)

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
            print("\n⚠️ LLM FAILED, FALLING BACK TO RULE-BASED:", e)

            return {
                "required_skills": [],
                "experience_required": None,
                "jd_clarity": "vague",
                "source": "rule_based_fallback"
            }
