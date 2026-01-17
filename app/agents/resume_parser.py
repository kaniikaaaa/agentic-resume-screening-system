import pdfplumber
import re

class ResumeParserAgent:
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.lower()

    def extract_skills(self, text: str):
        skill_keywords = [
            "python", "django", "fastapi", "flask", "postgresql", "mysql",
            "redis", "docker", "aws", "git", "ci/cd", "rest", "microservices",
            "kafka", "rabbitmq"
        ]

        found = []
        for skill in skill_keywords:
            if skill in text:
                found.append(skill)

        return list(set(found))

    def extract_experience_years(self, text: str):
        match = re.search(r"(\d+)\+?\s*years", text)
        if match:
            return int(match.group(1))
        return 0

    def parse(self, pdf_path: str):
        resume_text = self.extract_text_from_pdf(pdf_path)

        skills = self.extract_skills(resume_text)
        experience = self.extract_experience_years(resume_text)

        return {
            "skills": skills,
            "experience_years": experience,
            "raw_text": resume_text[:500]
        }
