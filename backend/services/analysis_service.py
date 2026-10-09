
from services.skill_analyzer import extract_skills
from services.ai_analyzer import analyze_resume
from services.job_description_validator import validate_job_description


def analyze_job_match(resume_text, resume_skills, job_description):
    job_description = validate_job_description(job_description)

    keyword_matches = extract_skills(job_description)

    ai_analysis = analyze_resume(
        resume_text,
        job_description,
        [
            skill for skill in resume_skills
            if skill.lower() in {
                item.lower() for item in keyword_matches
            }
        ],
        [
            skill for skill in keyword_matches
            if skill.lower() not in {
                item.lower() for item in resume_skills
            }
        ],
        0
    )

    assessments = ai_analysis.requirement_assessments

    required_skills = [item.title for item in assessments]

    matched_skills = [
        item.title for item in assessments
        if item.status == "supported"
    ]

    missing_skills = [
        item.title for item in assessments
        if item.status != "supported"
    ]

    weights = {
        "required": 2,
        "preferred": 1
    }

    total_weight = sum(
        weights[item.importance] for item in assessments
    )

    earned_weight = sum(
        weights[item.importance] * {
            "supported": 1,
            "partial": 0.5,
            "not_found": 0
        }[item.status]
        for item in assessments
    )

    match_score = (
        round(earned_weight / total_weight * 100)
        if total_weight > 0
        else None
    )

    return {
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "match_score": match_score,
        "ai_analysis": ai_analysis
    }