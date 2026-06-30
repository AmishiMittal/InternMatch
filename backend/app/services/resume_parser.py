import re
from pathlib import Path

import pdfplumber

SKILL_KEYWORDS = {
    "python", "java", "javascript", "typescript", "react", "node", "sql", "mongodb",
    "postgresql", "mysql", "aws", "azure", "gcp", "docker", "kubernetes", "git",
    "html", "css", "c++", "c#", "ruby", "go", "rust", "swift", "kotlin", "php",
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
    "pandas", "numpy", "data analysis", "data science", "statistics", "excel",
    "tableau", "power bi", "figma", "ui/ux", "agile", "scrum", "rest api",
    "graphql", "linux", "bash", "shell", "networking", "cybersecurity",
    "communication", "leadership", "teamwork", "problem solving", "project management",
    "marketing", "sales", "finance", "accounting", "research", "writing",
    "public speaking", "spring boot", "django", "flask", "fastapi", "next.js",
    "vue", "angular", "redis", "kafka", "spark", "hadoop", "nlp", "computer vision",
}

QUALIFICATION_KEYWORDS = {
    "bachelor", "bachelors", "b.s.", "b.sc", "b.tech", "b.e.", "master", "masters",
    "m.s.", "m.sc", "m.tech", "mba", "phd", "doctorate", "associate", "diploma",
    "certificate", "certification", "computer science", "engineering", "business",
    "economics", "mathematics", "statistics", "information technology", "data science",
    "software engineering", "electrical", "mechanical", "civil", "finance", "marketing",
    "gpa", "honors", "summa cum laude", "dean", "graduate", "undergraduate",
}


def extract_text_from_pdf(file_path: Path) -> str:
    text_parts: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def extract_skills(text: str) -> list[str]:
    normalized = _normalize(text)
    found = []
    for skill in sorted(SKILL_KEYWORDS, key=len, reverse=True):
        if skill in normalized and skill not in found:
            found.append(skill)
    return found


def extract_qualifications(text: str) -> list[str]:
    normalized = _normalize(text)
    found = []
    for qual in sorted(QUALIFICATION_KEYWORDS, key=len, reverse=True):
        if qual in normalized and qual not in found:
            found.append(qual)
    return found


def parse_resume_pdf(file_path: Path) -> dict:
    text = extract_text_from_pdf(file_path)
    if not text.strip():
        raise ValueError("Could not extract text from PDF. Ensure the file is not scanned/image-only.")

    skills = extract_skills(text)
    qualifications = extract_qualifications(text)

    return {
        "resume_text": text,
        "skills": ", ".join(skills) if skills else "",
        "qualifications": ", ".join(qualifications) if qualifications else "",
    }
