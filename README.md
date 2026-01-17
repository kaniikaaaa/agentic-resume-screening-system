# Agentic Resume Screening System

An AI-powered, agentic backend system that evaluates candidate resumes against job descriptions, explains its reasoning, and recommends the next hiring action.  
This project is built as a response to the Pitcrew Backend Engineering Assignment and focuses on clarity of thought, explainability, and multi-agent design rather than UI or deployment.

---

## Problem Statement

Hiring teams receive hundreds of resumes per role. Manually screening them is slow and inconsistent.  
This system acts like a “hiring committee” made of multiple agents, where each agent specializes in one task:

- Reading resumes  
- Understanding job requirements  
- Comparing skills  
- Evaluating experience  
- Making decisions  
- Explaining reasoning  

Instead of a single monolithic function, decisions emerge from collaboration between agents.

---

## Architecture Overview

 ┌─────────────────────┐
            │     Orchestrator    │
            └─────────┬───────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ ResumeParser │ │ JDParser │ │ Error Handling │
│ Agent │ │ Agent │ │ & Validation │
└────────┬────────┘ └────────┬────────┘ └─────────────────┘
│ │
▼ ▼
Structured Resume Structured JD
│ │
└────────────┬──────┘
▼
┌─────────────────┐
│ SkillMatchAgent │
└────────┬────────┘
▼
┌────────────────────┐
│ ExperienceAgent │
└────────┬───────────┘
▼
┌────────────────────┐
│ DecisionAgent │
└────────┬───────────┘
▼
┌────────────────────┐
│ ExplanationAgent │
└────────┬───────────┘
▼


---
## Skill Extraction Strategy

Currently, skill extraction is implemented using a rule-based keyword matching approach.
This decision was made intentionally to keep the system:

- Deterministic
- Fast
- Easy to debug
- Fully explainable

Instead of relying on black-box LLM outputs, the system uses predefined skill vocabularies
for both resumes and job descriptions. This ensures transparency in how matches are calculated.

In future versions, this can be enhanced using:
- LLM-based extraction (Gemini / GPT)
- Resume embeddings for semantic similarity
- Context-aware skill normalization

## Testing Strategy

The system is tested using real resumes and job descriptions across multiple scenarios:

- Strong backend candidate vs standard backend JD  
- Frontend candidate vs backend JD (expected rejection)  
- Junior / career switcher candidate vs junior JD  
- Strong candidate vs vague JD (expected human review)

Each test runs the full agent pipeline through the Orchestrator to ensure all agents
collaborate correctly and produce explainable outputs.


## Agents and Responsibilities

| Agent Name | Responsibility |
|------------|---------------|
| ResumeParserAgent | Reads resume PDFs and extracts raw text, skills, and experience |
| JDParserAgent | Reads job descriptions and extracts required skills and experience ranges |
| SkillMatchAgent | Compares resume skills with JD requirements |
| ExperienceAgent | Evaluates candidate experience against JD experience |
| DecisionAgent | Combines skill and experience scores to make a hiring decision |
| ExplanationAgent | Generates human-readable reasoning |
| Orchestrator | Coordinates all agents and produces final output |

---

## Agentic Design Philosophy

This system is agentic because:

- Each agent has a **single clear responsibility**
- Agents **pass structured data** to one another
- Decisions are made at multiple intermediate stages
- The system handles uncertainty and flags cases for human review
- State evolves as the pipeline progresses

What we avoided:

- One giant function doing everything
- One massive LLM prompt
- A blind linear pipeline with no branching
- Keyword-only matching without reasoning

---

## Input

1. Resume  
   - Format: PDF  
   - Example: `resume_01_priya_sharma.pdf`

2. Job Description  
   - Format: TXT  
   - Example: `jd_01_backend_python_standard.txt`

---

## Output (Pitcrew Format)

```json
{
  "match_score": 0.94,
  "recommendation": "Proceed to interview",
  "requires_human": false,
  "confidence": 0.9,
  "reasoning_summary": "Strong skill alignment. Candidate matches most required skills such as python, django, fastapi, postgresql. Candidate experience (3 years) matches JD range (2-4 years)."
}

| Field             | Meaning                               |
| ----------------- | ------------------------------------- |
| match_score       | Overall match from 0.0 to 1.0         |
| recommendation    | Hiring action                         |
| requires_human    | Whether recruiter should double-check |
| confidence        | How confident the system is           |
| reasoning_summary | Explainable decision rationale        |

How Agents Pass State

ResumeParserAgent → resume_data

{
  "skills": [...],
  "experience_years": 3,
  "raw_text": "..."
}


JDParserAgent → jd_data

{
  "required_skills": [...],
  "experience_required": {"min": 2, "max": 4}
}


SkillMatchAgent → skill_result

{
  "score": 90,
  "matched_skills": [...],
  "missing_skills": [...]
}


ExperienceAgent → experience_result

{
  "score": 100,
  "status": "Perfect Fit",
  "reason": "Candidate experience (3 years) matches JD range (2-4 years)"
}


DecisionAgent → decision_result

{
  "final_score": 94.0,
  "match_score": 0.94,
  "recommendation": "Proceed to interview",
  "requires_human": false,
  "confidence": 0.9
}


ExplanationAgent → reasoning_summary

| Scenario              | System Behavior          |
| --------------------- | ------------------------ |
| Vague JD              | Manual Review Required   |
| Junior candidate      | Needs manual review      |
| Parsing failure       | Graceful error handling  |
| Low confidence cases  | Human-in-the-loop        |
| Overconfident scoring | Avoided using thresholds |

Why Rule-Based First?

Trade-offs:

Deterministic

Easy to debug

Explainable

Fast execution

No dependency on paid APIs

With more time:

Use LLMs (Gemini/OpenAI) for extraction

Use embeddings for semantic skill matching

Resume similarity scoring

Feedback loop from recruiter decisions

Setup Instructions
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m tests.test_parsers

Sample Scenarios Covered
Case	Behavior
Strong backend candidate	Auto-approve
Frontend candidate	Reject
Career switcher	Human review
Vague JD	Manual review
Future Improvements

LLM-powered parsing

Resume embeddings + vector similarity

Batch resume processing

Web UI dashboard

Confidence calibration using historical data

Final Thoughts

This system prioritizes:

Clear reasoning

Multi-agent collaboration

Cautious automation

Human-in-the-loop design

Transparent decision-making

Which directly aligns with Pitcrew’s philosophy of explainable, trustworthy AI systems.

🔁 LLM Execution Modes (Hybrid Design)

This system supports two execution modes:

LLM Mode (Default)

Uses Gemini LLM for semantic understanding of resumes and job descriptions.

Provides intelligent extraction of skills, experience, and requirements.

Activated when:

USE_LLM=true


Deterministic Mode (Fallback)

Uses rule-based parsing when:

LLM quota is exhausted

API is unavailable

LLM returns invalid responses

Ensures system never crashes and always produces output.

Activated when:

USE_LLM=false


This hybrid design ensures reliability, stability, and explainability.

🧠 Quota & Failure Safe Design

The system is designed to gracefully handle:

API quota exhaustion (429 errors)

Network failures

Invalid LLM JSON responses

In such cases:

The pipeline automatically switches to deterministic mode

Hiring decisions are still produced

Human-in-the-loop is triggered when uncertainty exists

This matches real-world AI backend reliability standards.

🧪 Testing in Both Modes

Run with LLM:

$env:USE_LLM="true"
python -m tests.test_parsers


Run without LLM (offline / quota-free):

$env:USE_LLM="false"
python -m tests.test_parsers


This allows:

Stable local testing

Reproducible results

Easy demos even without API access

> Note: This repository is private as per Pitcrew submission guidelines.
> Code access is provided to reviewers via GitHub collaborator invite.
