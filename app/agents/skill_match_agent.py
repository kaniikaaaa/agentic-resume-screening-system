class SkillMatchAgent:
    def evaluate(self, resume_data, jd_data):
        resume_skills = set(resume_data["skills"])
        jd_skills = set(jd_data["required_skills"])

        matched = resume_skills.intersection(jd_skills)
        missing = jd_skills - resume_skills
        extra = resume_skills - jd_skills

        if len(jd_skills) == 0:
            score = 0
        else:
            score = int((len(matched) / len(jd_skills)) * 100)

        return {
            "score": score,
            "matched_skills": list(matched),
            "missing_skills": list(missing),
            "extra_skills": list(extra)
        }
