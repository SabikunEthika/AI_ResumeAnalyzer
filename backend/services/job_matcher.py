def calculate_match(resume_skills, required_skills):
    resume_skills_lower = {skill.lower(): skill for skill in resume_skills}
    required_skills_lower = {skill.lower(): skill for skill in required_skills}

    matched_skills = [
        resume_skills_lower[skill]
        for skill in required_skills_lower
        if skill in resume_skills_lower
    ]

    missing_skills = [
        required_skills_lower[skill]
        for skill in required_skills_lower
        if skill not in resume_skills_lower
    ]

    if not required_skills:
        score = 0
    else:
        score = round((len(matched_skills) / len(required_skills)) * 100)

    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "match_score": score
    }