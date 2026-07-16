class ExperienceAgent:
    """Scores the candidate's years against the JD's stated range."""

    def evaluate(self, resume_data: dict, jd_data: dict) -> dict:
        years = resume_data.get("experience_years") or 0
        requirement = jd_data.get("experience_required")

        if not requirement or requirement.get("min") is None:
            return {
                "score": 50,
                "status": "Unknown",
                "reason": "The job description does not state an experience requirement.",
            }

        minimum = requirement.get("min", 0)
        maximum = requirement.get("max")
        stated = _describe(minimum, maximum)
        has = _plural(years)

        if years < minimum:
            # A near miss is a judgement call, not a disqualification.
            shortfall = minimum - years
            if shortfall <= 1:
                return {
                    "score": 65,
                    "status": "Slightly under",
                    "reason": f"Candidate has {has} against a requirement of {stated} — marginally short.",
                }
            return {
                "score": 30,
                "status": "Under-qualified",
                "reason": f"Candidate has {has} against a requirement of {stated}.",
            }

        if maximum is None or years <= maximum:
            return {
                "score": 100,
                "status": "Fit",
                "reason": f"Candidate has {has}, meeting the requirement of {stated}.",
            }

        return {
            "score": 70,
            "status": "Over-qualified",
            "reason": f"Candidate has {has} against a requirement of {stated}; may be over-levelled for the role.",
        }


def _plural(years: float) -> str:
    value = int(years) if float(years).is_integer() else years
    return f"{value} year" if value == 1 else f"{value} years"


def _describe(minimum: int, maximum: int | None) -> str:
    if maximum is None:
        return f"{minimum}+ years"
    if minimum == maximum:
        return _plural(minimum)
    return f"{minimum}–{maximum} years"
