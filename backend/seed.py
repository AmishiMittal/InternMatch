"""Seed sample data for demo purposes."""

from app.database import SessionLocal, init_db
from app.models import Company, Internship, Student
from app.security import generate_auth_token, hash_password

SAMPLE_PASSWORD = "password123"

SAMPLE_COMPANIES = [
    {"name": "TechNova Solutions", "email": "hr@technova.com", "sector": "Technology", "location": "San Francisco, CA"},
    {"name": "GreenEnergy Corp", "email": "careers@greenenergy.com", "sector": "Energy", "location": "Austin, TX"},
    {"name": "FinWise Analytics", "email": "jobs@finwise.com", "sector": "Finance", "location": "New York, NY"},
]

SAMPLE_INTERNSHIPS = [
    {
        "company_email": "hr@technova.com",
        "title": "Software Engineering Intern",
        "description": "Build web applications using Python and React. Work on REST APIs and cloud deployment.",
        "required_skills": "python, react, javascript, sql, git, rest api",
        "required_qualifications": "computer science, software engineering, bachelor",
        "location": "San Francisco, CA",
        "sector": "Technology",
        "capacity": 3,
    },
    {
        "company_email": "hr@technova.com",
        "title": "Data Science Intern",
        "description": "Analyze datasets, build ML models, and create dashboards for business insights.",
        "required_skills": "python, machine learning, pandas, statistics, data analysis",
        "required_qualifications": "data science, statistics, mathematics, bachelor",
        "location": "San Francisco, CA",
        "sector": "Technology",
        "capacity": 2,
    },
    {
        "company_email": "careers@greenenergy.com",
        "title": "Sustainability Research Intern",
        "description": "Research renewable energy trends and support environmental impact assessments.",
        "required_skills": "research, data analysis, writing, excel",
        "required_qualifications": "engineering, environmental, bachelor",
        "location": "Austin, TX",
        "sector": "Energy",
        "capacity": 2,
    },
    {
        "company_email": "jobs@finwise.com",
        "title": "Financial Analyst Intern",
        "description": "Support financial modeling, market research, and reporting for investment teams.",
        "required_skills": "excel, finance, data analysis, communication",
        "required_qualifications": "finance, economics, business, bachelor",
        "location": "New York, NY",
        "sector": "Finance",
        "capacity": 4,
    },
]

SAMPLE_STUDENTS = [
    {
        "name": "Alex Chen",
        "email": "alex.chen@university.edu",
        "location_preference": "San Francisco, CA",
        "sector_interests": "Technology, Data Science",
        "past_internships": 1,
        "skills": "python, react, javascript, sql, git, rest api, docker",
        "qualifications": "computer science, bachelor, software engineering",
        "resume_text": "Computer Science student with Python and React experience.",
    },
    {
        "name": "Jordan Lee",
        "email": "jordan.lee@university.edu",
        "location_preference": "New York, NY",
        "sector_interests": "Finance, Analytics",
        "past_internships": 0,
        "skills": "excel, finance, data analysis, python, communication",
        "qualifications": "finance, economics, bachelor",
        "resume_text": "Finance major skilled in Excel and financial modeling.",
    },
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        if db.query(Company).count() > 0:
            print("Database already seeded.")
            return

        email_to_company = {}
        for data in SAMPLE_COMPANIES:
            company = Company(
                **data,
                password_hash=hash_password(SAMPLE_PASSWORD),
                auth_token=generate_auth_token(),
            )
            db.add(company)
            db.flush()
            email_to_company[company.email] = company

        for data in SAMPLE_INTERNSHIPS:
            company = email_to_company[data.pop("company_email")]
            internship = Internship(company_id=company.id, **data)
            db.add(internship)

        for data in SAMPLE_STUDENTS:
            student = Student(
                **data,
                password_hash=hash_password(SAMPLE_PASSWORD),
                auth_token=generate_auth_token(),
            )
            db.add(student)

        db.commit()
        print(f"Sample data seeded successfully. All accounts use password: {SAMPLE_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
