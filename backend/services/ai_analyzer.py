import os

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel
from google.genai import types


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=api_key)


class AIAnalysis(BaseModel):
    overall_assessment: str
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]


def analyze_resume(resume_text, job_description, matched_skills, missing_skills, match_score):
    prompt = f"""
You are an AI resume analyzer.

Analyze the candidate's resume against the target job description.

Candidate Resume:
{resume_text}

Target Job Description:
{job_description}

Matched Skills:
{matched_skills}

Missing Skills:
{missing_skills}

Current Skill Match Score:
{match_score}%

Provide a practical and honest analysis.

The overall assessment should briefly explain how suitable the candidate is for the job.

Strengths should focus on skills, experience, education, projects, or other relevant qualifications found in the resume.

Weaknesses should identify important gaps or areas where the resume is weaker compared with the job description.

Suggestions should provide specific and actionable ways the candidate can improve their resume or qualifications for this job.

Do not invent experience, skills, education, or achievements that are not present in the resume.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AIAnalysis
        )
    )

    return AIAnalysis.model_validate_json(response.text)