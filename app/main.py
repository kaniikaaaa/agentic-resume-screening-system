from fastapi import FastAPI

app = FastAPI(title="Agentic Resume Screening System")

@app.get("/")
def root():
    return {"message": "Agentic Resume Screening System is running"}
