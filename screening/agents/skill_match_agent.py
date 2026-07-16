from screening.services import taxonomy


class SkillMatchAgent:
    """Scores how much of the JD's required skill list the candidate covers.

    Both sides are canonicalised before comparison. Comparing raw strings meant
    a resume saying "PostgreSQL" missed a JD asking for "postgres", which
    silently deflated every score.
    """

    def evaluate(self, resume_data: dict, jd_data: dict) -> dict:
        resume_skills = taxonomy.canonical_set(resume_data.get("skills") or [])
        jd_skills = taxonomy.canonical_set(jd_data.get("required_skills") or [])

        resume_set = set(resume_skills)
        jd_set = set(jd_skills)

        matched = [s for s in jd_skills if s in resume_set]
        missing = [s for s in jd_skills if s not in resume_set]
        extra = [s for s in resume_skills if s not in jd_set]

        # No requirements to check against; the DecisionAgent routes this to a
        # human on JD clarity rather than reading 0 as a bad candidate.
        score = round(len(matched) / len(jd_skills) * 100) if jd_skills else 0

        return {
            "score": score,
            "matched_skills": matched,
            "missing_skills": missing,
            "extra_skills": extra,
            "coverage": f"{len(matched)}/{len(jd_skills)}" if jd_skills else "0/0",
        }
