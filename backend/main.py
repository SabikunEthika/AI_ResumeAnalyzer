from fastapi import FastAPI, File, UploadFile

from services.resume_parser import extract_resume_text

app = FastAPI()


@app.get("/")
def home():
    return {"message": "AI Resume Analyzer Backend is running!"}


@app.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        text = extract_resume_text(file.filename, file_bytes)

        return {
            "filename": file.filename,
            "text": text
        }

    except ValueError as error:
        return {
            "error": str(error)
        }