"""
Rule-based skill extraction for fallback when LLM is unavailable.

This module provides deterministic skill extraction using keyword matching,
ensuring the system produces useful output even without LLM access.
"""

import re
from typing import List, Tuple, Optional

# Common technical skills vocabulary (lowercase for matching)
TECH_SKILLS = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",

    # Web Frameworks
    "django", "flask", "fastapi", "express", "expressjs", "react", "reactjs",
    "angular", "vue", "vuejs", "nextjs", "next.js", "nuxt", "svelte",
    "spring", "spring boot", "springboot", "rails", "ruby on rails",
    "laravel", "asp.net", "dotnet", ".net",

    # Databases
    "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "sqlite", "oracle", "mariadb", "neo4j", "graphql",

    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "terraform", "ansible", "jenkins", "gitlab", "github actions", "ci/cd",
    "linux", "unix", "bash", "shell scripting",

    # Data & ML
    "machine learning", "ml", "deep learning", "tensorflow", "pytorch", "keras",
    "pandas", "numpy", "scikit-learn", "sklearn", "spark", "hadoop", "kafka",
    "airflow", "data engineering", "etl", "data pipeline",

    # APIs & Protocols
    "rest", "rest api", "restful", "graphql", "grpc", "websocket", "microservices",
    "api design", "api development",

    # Tools & Practices
    "git", "github", "gitlab", "bitbucket", "jira", "agile", "scrum",
    "tdd", "unit testing", "pytest", "jest", "mocha", "selenium",

    # Other
    "html", "css", "sass", "tailwind", "bootstrap", "webpack", "node.js", "nodejs",
    "npm", "yarn", "celery", "rabbitmq", "nginx", "apache",
}

# Experience patterns
EXPERIENCE_PATTERNS = [
    r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)?',
    r'(?:experience|exp)[:\s]*(\d+)\+?\s*(?:years?|yrs?)',
    r'(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)',
]


def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract technical skills from text using keyword matching.

    Args:
        text: Raw text from resume or job description

    Returns:
        List of matched skills (lowercase, deduplicated)
    """
    if not text:
        return []

    text_lower = text.lower()
    found_skills = set()

    for skill in TECH_SKILLS:
        # Use word boundary matching to avoid partial matches
        # e.g., "sql" shouldn't match "mysql" separately
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.add(skill)

    # Normalize some skills (remove duplicates like "react" and "reactjs")
    normalized = set()
    for skill in found_skills:
        # Keep the shorter/canonical form
        if skill == "reactjs":
            normalized.add("react")
        elif skill == "vuejs":
            normalized.add("vue")
        elif skill == "expressjs":
            normalized.add("express")
        elif skill == "nodejs":
            normalized.add("node.js")
        elif skill == "golang":
            normalized.add("go")
        elif skill == "postgres":
            normalized.add("postgresql")
        elif skill == "springboot":
            normalized.add("spring boot")
        else:
            normalized.add(skill)

    return sorted(list(normalized))


def extract_experience_years(text: str) -> int:
    """
    Extract years of experience from text.

    Args:
        text: Raw text from resume

    Returns:
        Estimated years of experience (0 if not found)
    """
    if not text:
        return 0

    text_lower = text.lower()

    for pattern in EXPERIENCE_PATTERNS:
        matches = re.findall(pattern, text_lower)
        if matches:
            # Get the first match
            match = matches[0]
            if isinstance(match, tuple):
                # Range like "2-4 years" - take the lower bound
                return int(match[0])
            else:
                return int(match)

    # Fallback: count years mentioned in work experience sections
    year_mentions = re.findall(r'20\d{2}', text)
    if len(year_mentions) >= 2:
        years = sorted([int(y) for y in year_mentions])
        experience = years[-1] - years[0]
        if 0 < experience <= 30:  # Sanity check
            return experience

    return 0


def extract_experience_requirement(text: str) -> Optional[dict]:
    """
    Extract experience requirement from job description.

    Args:
        text: Job description text

    Returns:
        Dict with min/max experience or None if not found
    """
    if not text:
        return None

    text_lower = text.lower()

    # Pattern: "2-4 years"
    range_match = re.search(r'(\d+)\s*[-–to]+\s*(\d+)\s*(?:years?|yrs?)', text_lower)
    if range_match:
        return {
            "min": int(range_match.group(1)),
            "max": int(range_match.group(2))
        }

    # Pattern: "2+ years" or "minimum 2 years"
    min_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)', text_lower)
    if min_match:
        return {
            "min": int(min_match.group(1)),
            "max": None
        }

    return None
