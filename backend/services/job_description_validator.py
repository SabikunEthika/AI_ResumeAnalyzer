
JOB_DESCRIPTION_INDICATORS = [
    "responsibilities",
    "requirements",
    "qualifications",
    "experience",
    "job description",
    "about the role",
    "about the position",
    "we are looking",
    "you will",
    "candidate",
    "position",
    "role",
    "job",
    "developer",
    "engineer",
    "analyst",
    "designer",
    "intern",
    "specialist",
    "manager",
    "technician",
    "consultant",
    "coordinator",
    "professional",
    "education",
    "skills",
]

MAX_JOB_DESCRIPTION_LENGTH = 10_000


def validate_job_description(text):
    text = text.strip()

    if len(text) < 30:
        raise ValueError(
            "Job description must contain at least 30 characters."
        )

    if len(text) > MAX_JOB_DESCRIPTION_LENGTH:
        raise ValueError(
            "Job description must be 10,000 characters or fewer."
        )

    normalized_text = text.lower()

    has_job_indicator = any(
        indicator in normalized_text
        for indicator in JOB_DESCRIPTION_INDICATORS
    )

    if not has_job_indicator:
        raise ValueError(
            "Please provide a valid job description with role details, "
            "responsibilities, requirements, or qualifications."
        )

    return text
