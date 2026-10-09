
import os

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field
from google.genai import types


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=api_key)


class ResumeSectionReview(BaseModel):
    section: str
    status: str
    feedback: str


class ResumeQualityAnalysis(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    summary: str
    strengths: list[str]
    improvements: list[str]
    section_reviews: list[ResumeSectionReview]
    missing_information: list[str]
    achievement_feedback: list[str]

    ats_score: int = Field(ge=0, le=100)
    ats_summary: str
    ats_strengths: list[str]
    ats_issues: list[str]
    ats_improvements: list[str]


def analyze_resume_quality(resume_text: str) -> ResumeQualityAnalysis:
    prompt = f"""
You are an evidence-based resume quality reviewer and ATS-readiness
advisor. Evaluate resumes from ALL professions, industries, academic
disciplines, and career stages.

RESUME TEXT:
{resume_text[:25000]}

PART A: RESUME QUALITY

1. Give an overall score from 0 to 100 using:
- Clarity and readability: 25%
- Structure and organization: 20%
- Specificity of experience and achievements: 25%
- Relevant information and completeness: 20%
- Consistency and professional wording: 10%

Be fair to students, beginners, career changers, and people without
extensive employment history. Consider relevant education, projects,
volunteering, coursework, certifications, and other experience.

2. Write a balanced summary.
3. List specific strengths supported by the resume.
4. Recommend practical, prioritized improvements.
5. Review identifiable sections such as profile, education, experience,
projects, skills, certifications, achievements, and contact details.
Only assess relevant sections. Do not require every section.
6. List important information that appears missing or unclear.
Distinguish genuinely missing details from possible extraction failures.
7. Identify vague achievement statements and explain how to improve
them. Never invent results, numbers, qualifications, or experience.

PART B: ATS-FRIENDLINESS

Give a separate ATS score from 0 to 100 based on evidence in the
EXTRACTED TEXT, using this rubric:

- Recognizable, logically organized sections: 25%
- Clear and consistently presented dates and experience: 20%
- Readable, straightforward text structure: 20%
- Relevant, specific skill and qualification terminology: 20%
- Clear job titles, education details, and other useful context: 15%

Assess:
- Whether standard section headings can be recognized.
- Whether job titles, organizations, education, and dates are clear
  when those details are applicable.
- Whether skills and qualifications are described specifically.
- Whether abbreviations may need to be written out at first mention.
- Whether the extracted text has confusing ordering, broken words,
  repeated fragments, or other potential parsing problems.
- Whether the resume relies on vague terms instead of meaningful
  descriptions of experience or skills.

ATS RULES:
- Evaluate the text provided; do not pretend to inspect the original
  PDF/DOCX visual layout, columns, tables, icons, graphics, or fonts.
- Do not automatically penalize a resume for not having every section.
- Do not require technical keywords for non-technical professions.
- Do not claim a resume will pass every employer's ATS.
- Do not assume a keyword is missing just because it is not in a
  fixed vocabulary.
- Do not recommend keyword stuffing or adding untrue qualifications.
- A resume can be good overall but have ATS parsing concerns, or
  vice versa. Score the two dimensions independently.
- If extraction quality makes a judgment uncertain, say so.
- Do not invent problems just to fill the output.

Return:
- ats_summary: short explanation of ATS readiness and uncertainty.
- ats_strengths: specific positive signs visible in the text.
- ats_issues: specific potential ATS concerns supported by the text.
- ats_improvements: actionable improvements, prioritized by usefulness.

Keep the review concise, specific, fair, and constructive.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ResumeQualityAnalysis,
        ),
    )

    if not response.text:
        raise ValueError("The AI returned an empty quality analysis.")

    return ResumeQualityAnalysis.model_validate_json(response.text)