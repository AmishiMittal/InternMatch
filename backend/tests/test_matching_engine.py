from app.matching.engine import (
    _jaccard_similarity,
    _location_score,
    classify_recommendation,
    compute_match,
)
from app.models import Internship, Student
from app.schemas import RecommendationTier


def make_student(**overrides):
    defaults = dict(
        name="Alex Chen",
        email="alex@example.com",
        location_preference="San Francisco, CA",
        sector_interests="Technology",
        qualifications="computer science, bachelor",
        skills="python, react, sql, git",
        resume_text="Computer Science student with Python and React experience.",
        past_internships=0,
    )
    defaults.update(overrides)
    return Student(**defaults)


def make_internship(**overrides):
    defaults = dict(
        company_id=1,
        title="Software Engineering Intern",
        description="Build web applications using Python and React.",
        required_skills="python, react, sql, git",
        required_qualifications="computer science, bachelor",
        location="San Francisco, CA",
        sector="Technology",
        capacity=3,
        filled_slots=0,
    )
    defaults.update(overrides)
    return Internship(**defaults)


def test_jaccard_similarity_identical_sets():
    assert _jaccard_similarity({"python", "sql"}, {"python", "sql"}) == 1.0


def test_jaccard_similarity_disjoint_sets():
    assert _jaccard_similarity({"python"}, {"java"}) == 0.0


def test_jaccard_similarity_empty_set_returns_zero():
    assert _jaccard_similarity(set(), {"python"}) == 0.0


def test_location_score_exact_match():
    assert _location_score("San Francisco, CA", "San Francisco, CA") == 1.0


def test_location_score_no_overlap():
    assert _location_score("New York, NY", "Austin, TX") == 0.0


def test_compute_match_perfect_fit_scores_high():
    student = make_student()
    internship = make_internship()
    result = compute_match(student, internship)
    assert result.total_score >= 90


def test_compute_match_poor_fit_scores_low():
    student = make_student(
        skills="excel, finance",
        qualifications="finance, economics",
        location_preference="New York, NY",
        sector_interests="Finance",
        resume_text="Finance major skilled in Excel.",
    )
    internship = make_internship()
    result = compute_match(student, internship)
    assert result.total_score < 50


def test_compute_match_capacity_zero_lowers_score():
    student = make_student()
    full_internship = make_internship(capacity=2, filled_slots=2)
    open_internship = make_internship(capacity=2, filled_slots=0)
    full_result = compute_match(student, full_internship)
    open_result = compute_match(student, open_internship)
    assert full_result.total_score < open_result.total_score


def test_classify_recommendation_tiers():
    assert classify_recommendation(95) == RecommendationTier.HIGHLY_RECOMMENDED
    assert classify_recommendation(85) == RecommendationTier.RECOMMENDED
    assert classify_recommendation(75) == RecommendationTier.ELIGIBLE
    assert classify_recommendation(90) == RecommendationTier.HIGHLY_RECOMMENDED
    assert classify_recommendation(80) == RecommendationTier.RECOMMENDED
