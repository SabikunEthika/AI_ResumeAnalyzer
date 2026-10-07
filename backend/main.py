from fastapi import FastAPI, File, UploadFile

from services.resume_parser import extract_resume_text
from services.skill_analyzer import extract_skills

app = FastAPI()


@app.get("/")
def home():
    return {"message": "AI Resume Analyzer Backend is running!"}


@app.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        text = extract_resume_text(file.filename, file_bytes)
        skills = extract_skills(text)

        return {
            "filename": file.filename,
            "text": text,
            "skills": skills
        }

    except ValueError as error:
        return {
            "error": str(error)
        }