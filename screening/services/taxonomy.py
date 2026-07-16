"""Skill vocabulary, canonicalisation, and deterministic extraction.

Two jobs:

1.  Deterministic mode. When no LLM is configured (or it fails), the parser
    agents fall back here and still produce usable structured data.

2.  Canonicalisation for *both* modes. The LLM writes "PostgreSQL", a job
    description says "postgres"; matching those as raw strings under-reports
    every time. Both sides are pushed through `canonical()` before comparison
    so "Node.js", "nodejs" and "node" collapse to one term.
"""

import re

# canonical name -> surface forms found in the wild.
# The canonical name is what the UI displays, so it carries real casing.
_SKILL_VOCAB: dict[str, list[str]] = {
    # languages
    "Python": ["python", "python3", "py3"],
    "JavaScript": ["javascript", "java script", "es6", "ecmascript"],
    "TypeScript": ["typescript"],
    "Java": ["java"],
    "Go": ["golang", "go lang"],
    "Ruby": ["ruby"],
    "PHP": ["php"],
    "C#": ["c#", "csharp", "c sharp"],
    "C++": ["c++", "cpp"],
    "Rust": ["rust"],
    "Scala": ["scala"],
    "Kotlin": ["kotlin"],
    "Swift": ["swift"],
    "SQL": ["sql"],
    "Bash": ["bash", "shell scripting"],
    # backend frameworks
    "Django": ["django"],
    "Django REST Framework": ["django rest framework", "drf"],
    "FastAPI": ["fastapi", "fast api"],
    "Flask": ["flask"],
    "Node.js": ["node.js", "nodejs", "node js", "node"],
    "Express": ["express.js", "expressjs", "express"],
    "Spring Boot": ["spring boot", "springboot", "spring"],
    "Rails": ["ruby on rails", "rails"],
    "GraphQL": ["graphql"],
    "REST APIs": [
        "rest api", "rest apis", "restful api", "restful apis",
        "restful", "rest",
    ],
    "gRPC": ["grpc"],
    "Microservices": ["microservice", "microservices"],
    # frontend
    "React": ["react.js", "reactjs", "react"],
    "Next.js": ["next.js", "nextjs"],
    "Vue": ["vue.js", "vuejs", "vue"],
    "Angular": ["angular.js", "angularjs", "angular"],
    "Svelte": ["svelte"],
    "Redux": ["redux"],
    "HTML": ["html5", "html"],
    "CSS": ["css3", "css"],
    "Sass": ["sass", "scss"],
    "Tailwind CSS": ["tailwind css", "tailwindcss", "tailwind"],
    "Webpack": ["webpack"],
    "jQuery": ["jquery"],
    # data stores
    "PostgreSQL": ["postgresql", "postgres", "psql"],
    "MySQL": ["mysql"],
    "SQLite": ["sqlite"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Elasticsearch": ["elasticsearch", "elastic search"],
    "Cassandra": ["cassandra"],
    "DynamoDB": ["dynamodb"],
    "Database Design": [
        "database design", "schema design", "data modeling", "data modelling",
    ],
    "Query Optimization": ["query optimization", "query optimisation"],
    # infra / devops
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "Azure": ["azure", "microsoft azure"],
    "Terraform": ["terraform"],
    "Jenkins": ["jenkins"],
    "CI/CD": ["ci/cd", "ci cd", "cicd", "continuous integration",
              "continuous deployment"],
    "Nginx": ["nginx"],
    "Linux": ["linux", "unix"],
    "Git": ["git", "version control", "github", "gitlab"],
    # queues
    "Celery": ["celery"],
    "RabbitMQ": ["rabbitmq", "rabbit mq"],
    "Kafka": ["kafka", "apache kafka"],
    "Message Queues": ["message queue", "message queues", "message broker"],
    # data / ml
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "PyTorch": ["pytorch"],
    "TensorFlow": ["tensorflow"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "Machine Learning": ["machine learning", "ml"],
    "Airflow": ["airflow", "apache airflow"],
    "Spark": ["spark", "apache spark", "pyspark"],
    # practice
    "Testing": [
        "unit testing", "unit tests", "pytest", "jest", "test driven",
        "tdd", "testing",
    ],
    "Agile": ["agile", "scrum", "kanban"],
    "Code Review": ["code review", "code reviews"],
    "System Design": ["system design", "software architecture", "architecture"],
}

# surface form -> canonical, longest form first so "django rest framework"
# is consumed before the bare "django" inside it can match.
_LOOKUP: dict[str, str] = {
    alias: canonical
    for canonical, aliases in _SKILL_VOCAB.items()
    for alias in aliases
}
_ALIASES_BY_LENGTH: list[str] = sorted(_LOOKUP, key=len, reverse=True)

_ALIAS_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # \b behaves badly against aliases ending in punctuation (c++, c#, node.js),
    # so the boundaries are asserted by hand.
    (alias, re.compile(
        r"(?<![a-z0-9+#.])" + re.escape(alias) + r"(?![a-z0-9+#]|\.[a-z])",
        re.IGNORECASE,
    ))
    for alias in _ALIASES_BY_LENGTH
]


def canonical(term: str) -> str:
    """Map any surface form to its canonical name.

    Unknown terms are returned title-cased rather than dropped: the LLM
    legitimately finds skills the vocabulary has never heard of, and silently
    discarding them would make the match score lie.
    """
    if not term:
        return ""

    cleaned = re.sub(r"\s+", " ", str(term).strip().strip(".,;:()[]"))
    if not cleaned:
        return ""

    hit = _LOOKUP.get(cleaned.lower())
    if hit:
        return hit

    # "experience with docker" -> Docker
    for alias, pattern in _ALIAS_PATTERNS:
        if pattern.search(cleaned):
            return _LOOKUP[alias]

    return cleaned if cleaned.isupper() else cleaned.title()


def canonical_set(terms) -> list[str]:
    """Canonicalise a list, dropping blanks and duplicates, order preserved."""
    seen: dict[str, None] = {}
    for term in terms or []:
        name = canonical(term)
        if name:
            seen.setdefault(name, None)
    return list(seen)


# Resumes head their sections in caps ("WORK EXPERIENCE", "EDUCATION").
_SECTION_HEADER_RE = re.compile(r"^[ \t]*([A-Z][A-Z&/'’\- ]{2,40})[ \t]*:?[ \t]*$", re.MULTILINE)

_EDUCATION_HEADER_RE = re.compile(
    r"\b(education|academic|training|certification|coursework|university|college)\b",
    re.IGNORECASE,
)


def _sections(text: str) -> list[tuple[str, str]]:
    """Split a resume into (header, body) pairs. Preamble is headed "".

    Section awareness matters because a degree's date range is not work
    experience, and a "Learning:" list is not a skill set.
    """
    matches = list(_SECTION_HEADER_RE.finditer(text))
    if not matches:
        return [("", text)]

    out: list[tuple[str, str]] = []
    if matches[0].start() > 0:
        out.append(("", text[: matches[0].start()]))

    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((match.group(1).strip(), text[match.end() : end]))

    return out


def _without_education(text: str) -> str:
    return "\n".join(
        body for header, body in _sections(text)
        if not _EDUCATION_HEADER_RE.search(header)
    )


# A skill named only in one of these frames is an aspiration, not a
# qualification: "Currently learning Django", "Learning: Docker, AWS basics".
_ASPIRATIONAL_LINE_RE = re.compile(
    r"^\s*(?:learning|currently\s+learning|self[-\s]study|want\s+to\s+learn|"
    r"interested\s+in|exploring|familiar\s+with|exposure\s+to)\b",
    re.IGNORECASE,
)
_ASPIRATIONAL_PHRASE_RE = re.compile(
    r"(?:currently\s+learning|learning|self[-\s]study(?:ing)?|"
    r"want(?:ing)?\s+to\s+learn|hoping\s+to\s+learn|looking\s+to\s+learn|"
    r"interested\s+in|beginning\s+to\s+learn|started\s+learning)\b",
    re.IGNORECASE,
)


def _is_aspirational(line: str, position: int) -> bool:
    """True if the mention at `position` sits in a learning frame."""
    if _ASPIRATIONAL_LINE_RE.match(line):
        return True

    # "Currently learning Django through online courses" — the cue precedes
    # the skill, so only look behind it, and only within the same clause.
    clause_start = max(
        line.rfind(".", 0, position),
        line.rfind(",", 0, position),
        line.rfind(";", 0, position),
    )
    lookbehind = line[clause_start + 1 : position]
    return bool(_ASPIRATIONAL_PHRASE_RE.search(lookbehind))


def extract_skills(text: str) -> list[str]:
    """Pull every known skill out of free text.

    A skill counts only where it is claimed as held. Mentions that appear
    exclusively in a learning frame are dropped, so "currently learning Django"
    no longer reads as Django experience.
    """
    if not text:
        return []

    held: dict[str, None] = {}
    aspirational: set[str] = set()

    for line in text.splitlines():
        if not line.strip():
            continue
        for alias, pattern in _ALIAS_PATTERNS:
            for match in pattern.finditer(line):
                skill = _LOOKUP[alias]
                if _is_aspirational(line, match.start()):
                    aspirational.add(skill)
                else:
                    held.setdefault(skill, None)

    return list(held)


# "2-4 years", "2 to 4 years"
_RANGE_RE = re.compile(
    r"(\d{1,2})\s*(?:-|–|—|to)\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)",
    re.IGNORECASE,
)
# "5+ years", "minimum 3 years", "at least 2 yrs"
_MIN_RE = re.compile(
    r"(?:(?:minimum|min\.?|at\s+least|over|more\s+than)\s*)?"
    r"(\d{1,2})\s*\+\s*(?:years?|yrs?)"
    r"|(?:minimum|min\.?|at\s+least)\s*(?:of\s*)?(\d{1,2})\s*(?:years?|yrs?)",
    re.IGNORECASE,
)
# "3 years of experience"
_PLAIN_RE = re.compile(
    r"(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)\s*(?:of\s*)?"
    r"(?:professional\s+|relevant\s+|hands[-\s]?on\s+|total\s+)?"
    r"(?:experience|exp\b)",
    re.IGNORECASE,
)


def extract_experience_years(text: str) -> float:
    """Best-effort years of experience from a resume.

    Takes the largest credible claim: resumes tend to state a headline total
    ("4 years of experience") alongside smaller per-role spans, and the
    headline is the one being asserted.
    """
    if not text:
        return 0.0

    candidates = [float(m.group(1)) for m in _PLAIN_RE.finditer(text)]

    for match in _RANGE_RE.finditer(text):
        candidates.append(float(match.group(2)))

    plausible = [c for c in candidates if 0 < c <= 45]
    if plausible:
        return max(plausible)

    # Nothing stated outright, so fall back to summing employment dates —
    # excluding education, whose date range is a degree, not a job.
    return float(_years_from_date_ranges(_without_education(text)))


_DATE_RANGE_RE = re.compile(
    r"(20\d{2}|19\d{2})\s*(?:-|–|—|to)\s*(present|current|now|20\d{2}|19\d{2})",
    re.IGNORECASE,
)
_CURRENT_YEAR = 2026


def _years_from_date_ranges(text: str) -> int:
    """Union of employment date ranges, as a fallback when no total is stated."""
    spans: list[tuple[int, int]] = []

    for match in _DATE_RANGE_RE.finditer(text):
        start = int(match.group(1))
        end_raw = match.group(2).lower()
        end = _CURRENT_YEAR if end_raw in {"present", "current", "now"} else int(end_raw)
        if end >= start and end - start <= 45:
            spans.append((start, end))

    if not spans:
        return 0

    # Merge overlaps so two concurrent roles don't double-count.
    spans.sort()
    merged: list[list[int]] = [list(spans[0])]
    for start, end in spans[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    return sum(end - start for start, end in merged)


def extract_experience_requirement(text: str) -> dict | None:
    """Years-of-experience requirement from a job description."""
    if not text:
        return None

    match = _RANGE_RE.search(text)
    if match:
        low, high = int(match.group(1)), int(match.group(2))
        if low <= high:
            return {"min": low, "max": high}

    match = _MIN_RE.search(text)
    if match:
        value = match.group(1) or match.group(2)
        return {"min": int(value), "max": None}

    match = _PLAIN_RE.search(text)
    if match:
        return {"min": int(float(match.group(1))), "max": None}

    return None


_REQUIRED_SECTION_RE = re.compile(
    r"(?:required|requirements|must[\s-]have|qualifications|"
    r"technical\s+requirements|skills)\b(.*?)"
    r"(?=\n\s*(?:nice[\s-]to[\s-]have|preferred|benefits|what\s+we\s+offer|"
    r"how\s+to\s+apply|about\s+(?:us|the\s+company))|\Z)",
    re.IGNORECASE | re.DOTALL,
)


def extract_required_skills(jd_text: str) -> list[str]:
    """Required skills from a JD, preferring the requirements section.

    Scoping to that section keeps perks and company blurbs ("we use Slack")
    from being read as requirements. If no section is recognisable the whole
    document is scanned, which is the right call for terse JDs.
    """
    if not jd_text:
        return []

    sections = [m.group(1) for m in _REQUIRED_SECTION_RE.finditer(jd_text)]
    scoped = "\n".join(sections)

    skills = extract_skills(scoped)
    return skills if skills else extract_skills(jd_text)
