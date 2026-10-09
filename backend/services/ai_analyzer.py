
import os
from typing import Literal

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field
from google.genai import types


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=api_key)


class RequirementAssessment(BaseModel):
    title: str = Field(description="A specific job requirement")
    importance: Literal["required", "preferred"] = Field(
        description="Whether the requirement is essential or preferred"
    )
    status: Literal["supported", "partial", "not_found"] = Field(
        description="How strongly the resume supports this requirement"
    )
    evidence: str = Field(
        description="Relevant evidence from the resume, or a clear statement that none was found"
    )
    explanation: str = Field(
        description="Why the evidence does or does not satisfy the requirement"
    )


class AIAnalysis(BaseModel):
    overall_assessment: str
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    requirement_assessments: list[RequirementAssessment]


def analyze_resume(
    resume_text,
    job_description,
    matched_skills,
    missing_skills,
    match_score
):
    prompt = f"""
You are an evidence-based resume evaluator and career advisor.
Evaluate candidates across ALL job families and academic disciplines.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

OPTIONAL KEYWORD-BASED INFORMATION:
Matched keywords: {matched_skills}
Missing keywords: {missing_skills}
Keyword overlap score: {match_score}%

IMPORTANT:
The keyword information above comes from a limited vocabulary.
It may be incomplete or misleading. Do not treat it as ground truth.
Analyze the resume and job description independently.

1. UNDERSTAND THE JOB
Infer the likely role, responsibilities, seniority, and objectives
from the description. If the role is unclear, acknowledge uncertainty.

2. IDENTIFY REQUIREMENTS DYNAMICALLY
Create a concise list of meaningful job-specific requirements.
Include explicit requirements and important responsibilities implied
by the description. Cover relevant skills, experience, qualifications,
tools, communication, domain knowledge, or other job-specific needs.

Do not assume every job needs technical skills.
Do not invent requirements that are not reasonably supported by
the description.
Mark a requirement "required" only when it is explicitly essential
or strongly implied. Otherwise, mark it "preferred".
Combine duplicate or substantially overlapping requirements.
If the description contains too little information to identify
meaningful requirements, return an empty list rather than inventing them.

3. EVALUATE RESUME EVIDENCE
For each requirement, assign exactly one status:

- supported: clear resume evidence demonstrates the requirement.
- partial: some relevant evidence exists, but coverage or proficiency
  is uncertain or incomplete.
- not_found: the supplied resume does not provide sufficient evidence.

Not_found does NOT mean the candidate lacks the ability.
Do not infer proficiency from a skill name alone when the context
does not support it.

Look for evidence in projects, employment, education, volunteering,
certifications, achievements, portfolios, and completed tasks.
Recognize equivalent terminology, transferable experience, and
relevant accomplishments from other fields.

For each requirement, provide concise, specific evidence from the
resume. Never fabricate quotations, accomplishments, qualifications,
or experience. If evidence is absent, say so clearly.
Do not claim to have verified anything outside the supplied text.

4. OVERALL ASSESSMENT
Explain the candidate's fit using concrete evidence, relevant gaps,
transferable abilities, and uncertainty. Do not rely on the keyword score.
Do not present an uncertain inference as a confirmed fact.

5. STRENGTHS
List specific, evidence-supported strengths and explain their relevance.

6. WEAKNESSES
Prioritize important gaps or missing evidence. Distinguish between
a demonstrated qualification gap and information the resume omits.

7. ACTIONABLE SUGGESTIONS
Recommend realistic, role-relevant improvements. Suggest projects,
training, certifications, or portfolio work only when appropriate.
Never advise the candidate to claim skills or experience they do not have.

Keep the analysis balanced, practical, specific, and non-repetitive.
Use the language and professional context appropriate to the role.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AIAnalysis
        )
    )

    if not response.text:
        raise ValueError("The AI returned an empty analysis.")

    return AIAnalysis.model_validate_json(response.text)