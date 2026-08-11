from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads" / "resumes"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/internmatch"
    upload_dir: Path = UPLOAD_DIR
    max_upload_size_mb: int = 10
    student_eligibility_threshold: float = 70.0
    resume_max_age_days: int = 90

    class Config:
        env_prefix = "INTERNMATCH_"


settings = Settings()
