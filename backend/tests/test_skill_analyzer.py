
from services.skill_analyzer import extract_skills


def test_extracts_known_skills():
    text = "I use Python, JavaScript, and React."

    result = extract_skills(text)

    assert "Python" in result
    assert "JavaScript" in result
    assert "React" in result


def test_skill_extraction_is_case_insensitive():
    result = extract_skills("python and REACT")

    assert "Python" in result
    assert "React" in result


def test_unknown_skill_is_not_added():
    result = extract_skills("I have experience with an imaginary tool.")

    assert result == []


def test_empty_text_returns_no_skills():
    result = extract_skills("")

    assert result == []