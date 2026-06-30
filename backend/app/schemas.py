from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class RecommendationTier(str, Enum):
    HIGHLY_RECOMMENDED = "Highly Recommended"
    RECOMMENDED = "Recommended"
    ELIGIBLE = "Eligible"


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    sector: str = Field(min_length=1, max_length=100)
    location: str = Field(min_length=1, max_length=200)


class CompanyLogin(BaseModel):
    email: EmailStr
    password: str


class CompanyResponse(BaseModel):
    id: int
    name: str
    email: str
    sector: str
    location: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyAuthResponse(BaseModel):
    token: str
    company: CompanyResponse


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    location_preference: str = Field(min_length=1, max_length=200)
    sector_interests: str = Field(min_length=1)
    past_internships: int = Field(default=0, ge=0)


class StudentLogin(BaseModel):
    email: EmailStr
    password: str


class StudentResponse(BaseModel):
    id: int
    name: str
    email: str
    location_preference: str
    sector_interests: str
    qualifications: str
    skills: str
    resume_filename: str | None
    past_internships: int
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentAuthResponse(BaseModel):
    token: str
    student: StudentResponse


class InternshipCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    required_skills: str = Field(min_length=1)
    required_qualifications: str = ""
    location: str = Field(min_length=1, max_length=200)
    sector: str = Field(min_length=1, max_length=100)
    capacity: int = Field(default=1, ge=1)


class InternshipResponse(BaseModel):
    id: int
    company_id: int
    title: str
    description: str
    required_skills: str
    required_qualifications: str
    location: str
    sector: str
    capacity: int
    filled_slots: int
    is_active: bool
    created_at: datetime
    company_name: str | None = None

    model_config = {"from_attributes": True}


class CandidateMatch(BaseModel):
    student_id: int
    student_name: str
    student_email: str
    match_score: float
    skills: str
    qualifications: str
    location_preference: str
    past_internships: int


class InternshipRecommendation(BaseModel):
    internship_id: int
    title: str
    company_name: str
    location: str
    sector: str
    description: str
    recommendation: RecommendationTier


class MatchBreakdown(BaseModel):
    skills_score: float
    qualifications_score: float
    location_score: float
    sector_score: float
    experience_score: float
    capacity_score: float
    total_score: float
