from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from services.resume_parser import extract_resume_text
from services.skill_analyzer import extract_skills
from services.job_matcher import calculate_match


app = FastAPI()

class JobDescription(BaseModel):
    text: str

resume_data = {
    "text": "",
    "skills": []
}

@app.get("/")
def home():
    return {"message": "AI Resume Analyzer Backend is running!"}


@app.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        text = extract_resume_text(file.filename, file_bytes)
        skills = extract_skills(text)

        resume_data["text"] = text
        resume_data["skills"] = skills

        return {
            "filename": file.filename,
            "text": text,
            "skills": skills
        }

    except ValueError as error:
        return {
            "error": str(error)
        }
@app.post("/job/match")
async def match_job(job: JobDescription):
    if not resume_data["skills"]:
        return {
            "error": "Please upload a resume before matching a job."
        }

    required_skills = extract_skills(job.text)

    result = calculate_match(
        resume_data["skills"],
        required_skills
    )

    return {
        "required_skills": required_skills,
        **result
    }
  