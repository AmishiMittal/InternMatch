import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import app.database as database_module
from app.database import Base, get_db
from app.main import app

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    real_engine = database_module.engine
    database_module.engine = test_engine
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        database_module.engine = real_engine
        app.dependency_overrides.clear()


@pytest.fixture
def company_auth(client):
    response = client.post(
        "/api/companies",
        json={
            "name": "TechNova Solutions",
            "email": "hr@technova.com",
            "password": "password123",
            "sector": "Technology",
            "location": "San Francisco, CA",
        },
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def student_auth(client):
    response = client.post(
        "/api/students",
        json={
            "name": "Alex Chen",
            "email": "alex.chen@university.edu",
            "password": "password123",
            "location_preference": "San Francisco, CA",
            "sector_interests": "Technology",
            "past_internships": 0,
        },
    )
    assert response.status_code == 200
    return response.json()
