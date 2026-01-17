class ExperienceAgent:
    def evaluate(self, resume_data, jd_data):
        candidate_exp = resume_data.get("experience_years", 0)
        jd_exp = jd_data.get("experience_required")

        # JD me experience hi mention nahi hai
        if jd_exp is None:
            return {
                "score": 50,
                "status": "Unknown",
                "reason": "Job description does not clearly define experience requirement"
            }

        min_exp = jd_exp.get("min", 0)
        max_exp = jd_exp.get("max")

        # Case 1: JD like 0-2 years, candidate is fresher (0 years)
        if max_exp is not None and min_exp <= candidate_exp <= max_exp:
            score = 100
            status = "Perfect Fit"
            reason = f"Candidate experience ({candidate_exp} years) matches JD range ({min_exp}-{max_exp} years)"

            # Junior candidate special handling
            if candidate_exp == 0:
                score = 70
                status = "Junior Fit"
                reason = (
                    f"Candidate is a fresher with {candidate_exp} years experience, "
                    f"which fits the junior JD range ({min_exp}-{max_exp} years), "
                    f"but should be reviewed by a human recruiter."
                )

            return {
                "score": score,
                "status": status,
                "reason": reason
            }

        # Case 2: Under-qualified
        if candidate_exp < min_exp:
            return {
                "score": 30,
                "status": "Under-qualified",
                "reason": f"Candidate has {candidate_exp} years, JD requires minimum {min_exp} years"
            }

        # Case 3: Over-qualified
        if max_exp is not None and candidate_exp > max_exp:
            return {
                "score": 70,
                "status": "Over-qualified",
                "reason": f"Candidate has {candidate_exp} years, JD expects up to {max_exp} years"
            }

        # Case 4: JD like "4+ years"
        if max_exp is None:
            if candidate_exp >= min_exp:
                return {
                    "score": 100,
                    "status": "Qualified",
                    "reason": f"Candidate has {candidate_exp} years which meets minimum {min_exp}+ years"
                }
            else:
                return {
                    "score": 30,
                    "status": "Under-qualified",
                    "reason": f"Candidate has {candidate_exp} years, JD requires {min_exp}+ years"
                }
