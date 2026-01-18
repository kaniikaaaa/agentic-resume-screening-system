import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Toggle between original and LangGraph orchestrator
USE_LANGGRAPH = os.getenv("USE_LANGGRAPH", "true").lower() == "true"

if USE_LANGGRAPH:
    from app.graph_orchestrator import GraphOrchestrator
    orchestrator = GraphOrchestrator()
    print("Using LangGraph Orchestrator")
else:
    from app.orchestrator import Orchestrator
    orchestrator = Orchestrator()
    print("Using Original Orchestrator")

test_cases = [
    {
        "name": "Strong backend candidate vs Backend Python JD",
        "resume": "data/resume_01_priya_sharma.pdf",
        "jd": "data/jd_01_backend_python_standard.txt"
    },
    {
        "name": "Weak candidate vs Backend Python JD",
        "resume": "data/resume_02_rahul_verma.pdf",
        "jd": "data/jd_01_backend_python_standard.txt"
    },
    {
        "name": "Junior candidate vs Junior Flexible JD",
        "resume": "data/resume_04_vikram_singh.pdf",
        "jd": "data/jd_03_junior_flexible.txt"
    },
    {
        "name": "Strong candidate vs Vague JD",
        "resume": "data/resume_01_priya_sharma.pdf",
        "jd": "data/jd_04_vague_ambiguous.txt"
    }
]

for i, case in enumerate(test_cases, 1):
    print(f"\n{'='*60}")
    print(f"TEST CASE {i}: {case['name']}")
    print(f"{'='*60}")

    result = orchestrator.run(case["resume"], case["jd"])

    print("Final Output:")
    print(result)
