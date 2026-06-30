import re
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models import Internship, Student
from app.schemas import RecommendationTier


@dataclass
class MatchResult:
    skills_score: float
    qualifications_score: float
    location_score: float
    sector_score: float
    experience_score: float
    capacity_score: float
    total_score: float


WEIGHTS = {
    "skills": 0.40,
    "qualifications": 0.20,
    "location": 0.15,
    "sector": 0.15,
    "experience": 0.05,
    "capacity": 0.05,
}


_QUAL_ALIASES = {
    "b.tech": "bachelor", "btech": "bachelor", "b.e": "bachelor", "be ": "bachelor",
    "b.sc": "bachelor", "bsc": "bachelor", "b.com": "bachelor", "bcom": "bachelor",
    "b.a": "bachelor", "ba ": "bachelor", "b.arch": "bachelor",
    "m.tech": "master", "mtech": "master", "m.e": "master", "m.sc": "master",
    "msc": "master", "mba": "master", "m.com": "master", "m.a": "master",
    "phd": "doctorate", "ph.d": "doctorate",
    "12th": "high school", "hsc": "high school", "intermediate": "high school",
    "10th": "high school", "ssc": "high school",
}


def _normalize_qual(token: str) -> str:
    t = token.strip().lower()
    for alias, canonical in _QUAL_ALIASES.items():
        if t == alias or t.startswith(alias):
            return canonical
    return t


def _tokenize_csv(value: str) -> set[str]:
    return {item.strip().lower() for item in re.split(r"[,;|/\n]+", value) if item.strip()}


def _tokenize_qualifications(value: str) -> set[str]:
    return {_normalize_qual(item) for item in re.split(r"[,;|/\n]+", value) if item.strip()}


def _jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def _text_similarity(text_a: str, text_b: str) -> float:
    if not text_a.strip() or not text_b.strip():
        return 0.0
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform([text_a, text_b])
    return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])


def _location_score(student_pref: str, internship_location: str) -> float:
    pref = student_pref.lower().strip()
    loc = internship_location.lower().strip()
    if not pref or not loc:
        return 0.3
    if pref == loc or pref in loc or loc in pref:
        return 1.0
    pref_tokens = set(re.findall(r"[a-z]+", pref))
    loc_tokens = set(re.findall(r"[a-z]+", loc))
    jaccard = _jaccard_similarity(pref_tokens, loc_tokens)
    # Minimum 0.3 — no location match is still better than penalising remote-friendly roles
    return max(0.3, jaccard)


def _sector_score(student_interests: str, internship_sector: str) -> float:
    interests = _tokenize_csv(student_interests)
    sector = internship_sector.lower().strip()
    if not interests or not sector:
        return 0.0
    if sector in interests:
        return 1.0
    for interest in interests:
        if interest in sector or sector in interest:
            return 0.85
    return _jaccard_similarity(interests, {sector})


def _experience_score(past_internships: int) -> float:
    if past_internships == 0:
        return 1.0
    if past_internships == 1:
        return 0.85
    if past_internships == 2:
        return 0.7
    return 0.55


def _capacity_score(internship: Internship) -> float:
    remaining = max(internship.capacity - internship.filled_slots, 0)
    if remaining <= 0:
        return 0.0
    ratio = remaining / internship.capacity
    return min(1.0, 0.5 + 0.5 * ratio)


def compute_match(student: Student, internship: Internship) -> MatchResult:
    student_skills = _tokenize_csv(student.skills)
    required_skills = _tokenize_csv(internship.required_skills)
    skills_jaccard = _jaccard_similarity(student_skills, required_skills)
    skills_tfidf = _text_similarity(
        f"{student.skills} {student.resume_text}",
        internship.required_skills,
    )
    skills_score = 0.6 * skills_jaccard + 0.4 * skills_tfidf

    student_quals = _tokenize_qualifications(student.qualifications)
    required_quals = _tokenize_qualifications(internship.required_qualifications)
    if required_quals:
        qual_jaccard = _jaccard_similarity(student_quals, required_quals)
        qual_tfidf = _text_similarity(student.qualifications, internship.required_qualifications)
        qualifications_score = 0.5 * qual_jaccard + 0.5 * qual_tfidf
    else:
        qualifications_score = 0.7 if student_quals else 0.5

    location_score = _location_score(student.location_preference, internship.location)
    sector_score = _sector_score(student.sector_interests, internship.sector)
    experience_score = _experience_score(student.past_internships)
    capacity_score = _capacity_score(internship)

    total = (
        WEIGHTS["skills"] * skills_score
        + WEIGHTS["qualifications"] * qualifications_score
        + WEIGHTS["location"] * location_score
        + WEIGHTS["sector"] * sector_score
        + WEIGHTS["experience"] * experience_score
        + WEIGHTS["capacity"] * capacity_score
    )

    return MatchResult(
        skills_score=round(skills_score * 100, 2),
        qualifications_score=round(qualifications_score * 100, 2),
        location_score=round(location_score * 100, 2),
        sector_score=round(sector_score * 100, 2),
        experience_score=round(experience_score * 100, 2),
        capacity_score=round(capacity_score * 100, 2),
        total_score=round(total * 100, 2),
    )


def classify_recommendation(score: float) -> RecommendationTier:
    if score >= 90:
        return RecommendationTier.HIGHLY_RECOMMENDED
    if score >= 80:
        return RecommendationTier.RECOMMENDED
    return RecommendationTier.ELIGIBLE


def rank_candidates_for_internship(
    internship: Internship,
    students: list[Student],
    min_score: float = 0.0,
) -> list[tuple[Student, MatchResult]]:
    results: list[tuple[Student, MatchResult]] = []
    for student in students:
        match = compute_match(student, internship)
        if match.total_score >= min_score:
            results.append((student, match))
    results.sort(key=lambda item: item[1].total_score, reverse=True)
    return results


def get_eligible_internships_for_student(
    student: Student,
    internships: list[Internship],
    threshold: float = 70.0,
) -> list[tuple[Internship, MatchResult, RecommendationTier]]:
    eligible: list[tuple[Internship, MatchResult, RecommendationTier]] = []
    for internship in internships:
        if not internship.is_active:
            continue
        match = compute_match(student, internship)
        if match.total_score >= threshold:
            tier = classify_recommendation(match.total_score)
            eligible.append((internship, match, tier))
    eligible.sort(
        key=lambda item: (
            {"Highly Recommended": 0, "Recommended": 1, "Eligible": 2}[item[2].value],
            -item[1].total_score,
        )
    )
    return eligible
