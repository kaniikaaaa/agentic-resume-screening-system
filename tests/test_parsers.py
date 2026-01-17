from app.orchestrator import Orchestrator

orchestrator = Orchestrator()

result = orchestrator.run(
    "data/resume_01_priya_sharma.pdf",
    "data/jd_01_backend_python_standard.txt"
)

print("\n===== FINAL SYSTEM OUTPUT =====")
print(result)
