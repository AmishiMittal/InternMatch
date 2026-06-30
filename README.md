# InternMatch

AI-powered internship matchmaking system that connects companies and students using intelligent resume-to-role matching.

## Features

### For Companies
- Register (with password) and log in to a company account
- Post internship openings with skills, qualifications, location, sector, and capacity
- View **ranked candidate lists** with match scores (percentage) for your own internships only
- Rankings account for skills, qualifications, location fit, sector interests, past internship experience, and remaining slot capacity

### For Students
- Create a profile (with password) and log in to a student account
- Upload resumes in **PDF format** (skills and qualifications extracted automatically)
- See only internships where match score is **≥ 70%**
- Recommendations shown as tiers — **match percentages are hidden**:
  - **Highly Recommended** (90%+)
  - **Recommended** (80–89%)
  - **Eligible** (70–79%)

### Auth
- Token-based authentication: registration/login return a bearer token (`Authorization: Bearer <token>`)
- Companies can only view candidates for their own internships; students can only view/upload their own resume and recommendations

## Matching Algorithm

The engine combines multiple weighted signals:

| Factor | Weight |
|--------|--------|
| Skills overlap (Jaccard + TF-IDF cosine similarity) | 40% |
| Qualifications match | 20% |
| Location preference | 15% |
| Sector interest | 15% |
| Past internship participation | 5% |
| Remaining internship capacity | 5% |

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, scikit-learn, pdfplumber
- **Frontend:** React, Vite
- **Database:** PostgreSQL

## Quick Start

### 1. Backend

Requires a running PostgreSQL server with a database named `internmatch` (create it with `createdb internmatch` or `psql -c "CREATE DATABASE internmatch;"`). Connection string defaults to `postgresql+psycopg2://postgres:postgres@localhost:5432/internmatch` — override with the `INTERNMATCH_DATABASE_URL` env var.

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload --port 8080
```

API docs: http://localhost:8080/docs

Run tests with `pytest` (uses an in-memory SQLite DB, no PostgreSQL needed).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/companies` | — | Register a company, returns a token |
| POST | `/api/companies/login` | — | Log in, returns a token |
| POST | `/api/internships` | Company | Post an internship (owned by the logged-in company) |
| GET | `/api/internships/{id}/candidates` | Company (owner only) | Ranked candidates with scores |
| POST | `/api/students` | — | Register a student, returns a token |
| POST | `/api/students/login` | — | Log in, returns a token |
| POST | `/api/students/{id}/resume` | Student (self only) | Upload PDF resume |
| GET | `/api/students/{id}/recommendations` | Student (self only) | Eligible internships (tier only) |

## Project Structure

```
InternMatch/
├── backend/
│   ├── app/
│   │   ├── matching/engine.py    # AI matching logic
│   │   ├── services/resume_parser.py
│   │   ├── api.py
│   │   ├── models.py
│   │   └── main.py
│   ├── seed.py
│   └── requirements.txt
└── frontend/
    └── src/
        ├── components/
        │   ├── CompanyPortal.jsx
        │   └── StudentPortal.jsx
        └── App.jsx
```

## Sample Data

Running `python seed.py` creates demo companies, internships, and students so you can test matching immediately. All seeded accounts use the password `password123`.
