from app.orchestrator import Orchestrator

orchestrator = Orchestrator()

# Case 1: Strong backend candidate
print("\n===== CASE 1: PRIYA vs BACKEND JD =====")
result1 = orchestrator.run(
    "data/resume_01_priya_sharma.pdf",
    "data/jd_01_backend_python_standard.txt"
)
print(result1)

# Case 2: Frontend candidate for backend role
print("\n===== CASE 2: ANANYA vs BACKEND JD =====")
result2 = orchestrator.run(
    "data/resume_03_ananya_patel.pdf",
    "data/jd_01_backend_python_standard.txt"
)
print(result2)
print("\n===== CASE 3: PRIYA vs VAGUE JD =====")
result3 = orchestrator.run(
    "data/resume_01_priya_sharma.pdf",
    "data/jd_04_vague_ambiguous.txt"
)
print(result3)
print("\n===== CASE 3: PRIYA vs VAGUE JD =====")
result3 = orchestrator.run(
    "data/resume_01_priya_sharma.pdf",
    "data/jd_04_vague_ambiguous.txt"
)
print(result3)
print("\n===== CASE 4: VIKRAM vs JUNIOR JD =====")
result4 = orchestrator.run(
    "data/resume_04_vikram_singh.pdf",
    "data/jd_03_junior_flexible.txt"
)
print(result4)
