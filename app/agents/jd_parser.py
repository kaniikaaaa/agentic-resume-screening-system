import re

class JDParserAgent:
    def parse(self, jd_path: str):
        with open(jd_path, "r", encoding="utf-8") as f:
            text = f.read().lower()

        skills = self.extract_skills(text)
        experience = self.extract_experience(text)

        return {
            "required_skills": skills,
            "experience_required": experience,
            "raw_text": text[:500]
        }

    def extract_skills(self, text: str):
        skill_keywords = [
            "python", "django", "fastapi", "postgresql", "sql", "git",
            "docker", "aws", "redis", "kafka", "microservices"
        ]

        found = []
        for skill in skill_keywords:
            if skill in text:
                found.append(skill)

        return list(set(found))

    def extract_experience(self, text: str):
        match = re.search(r"(\d+)\s*-\s*(\d+)\s*years", text)
        if match:
            return {
                "min": int(match.group(1)),
                "max": int(match.group(2))
            }

        match = re.search(r"(\d+)\+\s*years", text)
        if match:
            return {
                "min": int(match.group(1)),
                "max": None
            }

        return None
