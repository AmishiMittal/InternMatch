from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.matching.engine import get_eligible_internships_for_student, rank_candidates_for_internship
from app.models import Company, Internship, Student
from app.schemas import (
    CandidateMatch,
    CompanyAuthResponse,
    CompanyCreate,
    CompanyLogin,
    CompanyResponse,
    InternshipCreate,
    InternshipRecommendation,
    InternshipResponse,
    StudentAuthResponse,
    StudentCreate,
    StudentLogin,
    StudentResponse,
)
from app.security import generate_auth_token, hash_password, verify_password
from app.services.resume_parser import parse_resume_pdf

router = APIRouter()
bearer_scheme = HTTPBearer()


def get_current_company(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Company:
    company = db.query(Company).filter(Company.auth_token == credentials.credentials).first()
    if not company:
        raise HTTPException(status_code=401, detail="Invalid or expired company token")
    return company


def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Student:
    student = db.query(Student).filter(Student.auth_token == credentials.credentials).first()
    if not student:
        raise HTTPException(status_code=401, detail="Invalid or expired student token")
    return student


@router.post("/companies", response_model=CompanyAuthResponse)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    existing = db.query(Company).filter(Company.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company with this email already exists")
    data = payload.model_dump(exclude={"password"})
    company = Company(**data, password_hash=hash_password(payload.password), auth_token=generate_auth_token())
    db.add(company)
    db.commit()
    db.refresh(company)
    return CompanyAuthResponse(token=company.auth_token, company=company)


@router.post("/companies/login", response_model=CompanyAuthResponse)
def login_company(payload: CompanyLogin, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.email == payload.email).first()
    if not company or not verify_password(payload.password, company.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    company.auth_token = generate_auth_token()
    db.commit()
    db.refresh(company)
    return CompanyAuthResponse(token=company.auth_token, company=company)


@router.get("/companies", response_model=list[CompanyResponse])
def list_companies(db: Session = Depends(get_db)):
    return db.query(Company).order_by(Company.name).all()


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/students", response_model=StudentAuthResponse)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student with this email already exists")
    data = payload.model_dump(exclude={"password"})
    student = Student(**data, password_hash=hash_password(payload.password), auth_token=generate_auth_token())
    db.add(student)
    db.commit()
    db.refresh(student)
    return StudentAuthResponse(token=student.auth_token, student=student)


@router.post("/students/login", response_model=StudentAuthResponse)
def login_student(payload: StudentLogin, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == payload.email).first()
    if not student or not verify_password(payload.password, student.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    student.auth_token = generate_auth_token()
    db.commit()
    db.refresh(student)
    return StudentAuthResponse(token=student.auth_token, student=student)


@router.get("/students", response_model=list[StudentResponse])
def list_students(db: Session = Depends(get_db), current_company: Company = Depends(get_current_company)):
    return db.query(Student).order_by(Student.name).all()


@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db), current_company: Company = Depends(get_current_company)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("/students/{student_id}/resume", response_model=StudentResponse)
async def upload_resume(
    student_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    if student_id != current_student.id:
        raise HTTPException(status_code=403, detail="Cannot upload a resume for another student")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are accepted")

    student = current_student

    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.max_upload_size_mb}MB limit")

    # Delete the previous resume file if the filename is changing
    if student.resume_filename and student.resume_filename != file.filename:
        old_path = settings.upload_dir / f"student_{student_id}_{student.resume_filename}"
        old_path.unlink(missing_ok=True)

    file_path = settings.upload_dir / f"student_{student_id}_{file.filename}"
    file_path.write_bytes(content)

    try:
        parsed = parse_resume_pdf(file_path)
    except ValueError as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    student.resume_text = parsed["resume_text"]
    student.skills = parsed["skills"]
    student.qualifications = parsed["qualifications"]
    student.resume_filename = file.filename
    student.resume_uploaded_at = datetime.utcnow()
    db.commit()
    db.refresh(student)
    return student


@router.post("/internships", response_model=InternshipResponse)
def create_internship(
    payload: InternshipCreate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):
    internship = Internship(company_id=current_company.id, **payload.model_dump())
    db.add(internship)
    db.commit()
    db.refresh(internship)
    return _internship_response(internship, current_company.name)


@router.get("/internships", response_model=list[InternshipResponse])
def list_internships(db: Session = Depends(get_db)):
    rows = db.query(Internship, Company.name).join(Company).order_by(Internship.created_at.desc()).all()
    return [_internship_response(internship, company_name) for internship, company_name in rows]


@router.get("/internships/{internship_id}", response_model=InternshipResponse)
def get_internship(internship_id: int, db: Session = Depends(get_db)):
    row = (
        db.query(Internship, Company.name)
        .join(Company)
        .filter(Internship.id == internship_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Internship not found")
    internship, company_name = row
    return _internship_response(internship, company_name)


@router.get("/internships/{internship_id}/candidates", response_model=list[CandidateMatch])
def get_ranked_candidates(
    internship_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    if internship.company_id != current_company.id:
        raise HTTPException(status_code=403, detail="Cannot view candidates for another company's internship")

    cutoff = datetime.utcnow() - timedelta(days=settings.resume_max_age_days)
    students = (
        db.query(Student)
        .filter(Student.resume_text != "")
        .filter(
            (Student.resume_uploaded_at >= cutoff) |
            (Student.resume_uploaded_at.is_(None))  # legacy rows without timestamp
        )
        .all()
    )
    ranked = rank_candidates_for_internship(internship, students)

    return [
        CandidateMatch(
            student_id=student.id,
            student_name=student.name,
            student_email=student.email,
            match_score=match.total_score,
            skills=student.skills,
            qualifications=student.qualifications,
            location_preference=student.location_preference,
            past_internships=student.past_internships,
        )
        for student, match in ranked
    ]


@router.get("/students/{student_id}/recommendations", response_model=list[InternshipRecommendation])
def get_student_recommendations(
    student_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    if student_id != current_student.id:
        raise HTTPException(status_code=403, detail="Cannot view another student's recommendations")
    student = current_student
    if not student.resume_text:
        raise HTTPException(status_code=400, detail="Upload a resume before viewing recommendations")

    internships = db.query(Internship).filter(Internship.is_active.is_(True)).all()
    eligible = get_eligible_internships_for_student(
        student,
        internships,
        threshold=settings.student_eligibility_threshold,
    )

    company_ids = {internship.company_id for internship, _, _ in eligible}
    companies = {
        c.id: c.name
        for c in db.query(Company).filter(Company.id.in_(company_ids)).all()
    } if company_ids else {}

    return [
        InternshipRecommendation(
            internship_id=internship.id,
            title=internship.title,
            company_name=companies.get(internship.company_id, "Unknown"),
            location=internship.location,
            sector=internship.sector,
            description=internship.description,
            recommendation=tier,
        )
        for internship, _, tier in eligible
    ]


def _internship_response(internship: Internship, company_name: str | None = None) -> InternshipResponse:
    data = InternshipResponse.model_validate(internship)
    data.company_name = company_name
    return data
