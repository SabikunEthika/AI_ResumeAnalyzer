from services.skill_analyzer import extract_skills
from services.job_matcher import calculate_match
from services.ai_analyzer import analyze_resume


def analyze_job_match(resume_text, resume_skills, job_description):
    required_skills = extract_skills(job_description)

    if not required_skills:
        raise ValueError(
            "The provided text does not appear to be a valid job description."
        )

    result = calculate_match(
        resume_skills,
        required_skills
    )

    ai_analysis = analyze_resume(
        resume_text,
        job_description,
        result["matched_skills"],
        result["missing_skills"],
        result["match_score"]
    )

    return {
        "required_skills": required_skills,
        **result,
        "ai_analysis": ai_analysis
    }