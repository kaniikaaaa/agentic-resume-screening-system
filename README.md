# Agentic Resume Screening System

An AI-powered, multi-agent backend system that evaluates candidate resumes against job descriptions, provides explainable reasoning, and recommends next hiring steps such as interviews or technical assessments.

This project demonstrates how modern AI-first companies like Pitcrew build intelligent, decision-making backend systems using agentic architectures.

---

## Why Agentic Architecture?

Instead of a single monolithic model, this system uses multiple specialized agents:
- Each agent performs a single responsibility.
- Agents collaborate to make a final decision.
- Output is transparent, explainable, and reliable.

This mirrors real-world AI backend systems used in HR automation.

---

## System Workflow

1. Resume and Job Description are uploaded.
2. Resume Parser Agent extracts structured candidate data.
3. JD Parser Agent extracts structured job requirements.
4. Skill Match Agent evaluates skill alignment.
5. Experience Agent evaluates experience relevance.
6. Decision Agent computes final score and hiring decision.
7. Explanation Agent generates human-readable reasoning.
8. System outputs ranked candidates and next steps.

---

## Agent Responsibilities

| Agent Name | Responsibility |
|-----------|---------------|
| Resume Parser Agent | Extracts skills, experience, projects from resumes |
| JD Parser Agent | Extracts requirements and expectations from job descriptions |
| Skill Match Agent | Matches candidate skills with job requirements |
| Experience Agent | Evaluates experience relevance |
| Decision Agent | Computes final score and recommendation |
| Explanation Agent | Generates explainable reasoning |

---

## Tech Stack

- Python
- FastAPI
- LangChain / LLM APIs
- Pydantic
- PostgreSQL (optional for persistence)

---

## API Endpoints (Planned)

| Method | Endpoint | Description |
|------|---------|-------------|
| POST | `/screen` | Upload JD and resume to get evaluation |

---

## Example Output

```json
{
  "score": 72,
  "decision": "Maybe Hire",
  "reasoning": "Candidate has strong Python skills but lacks LLM deployment experience. Projects show AI understanding but limited backend exposure.",
  "next_step": "Assign a short technical task."
}
