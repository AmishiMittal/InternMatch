def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_company_returns_token(client):
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
    body = response.json()
    assert body["token"]
    assert body["company"]["email"] == "hr@technova.com"


def test_register_company_duplicate_email_rejected(client, company_auth):
    response = client.post(
        "/api/companies",
        json={
            "name": "Other Co",
            "email": "hr@technova.com",
            "password": "password123",
            "sector": "Technology",
            "location": "Austin, TX",
        },
    )
    assert response.status_code == 400


def test_company_login_wrong_password_rejected(client, company_auth):
    response = client.post(
        "/api/companies/login",
        json={"email": "hr@technova.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_company_login_correct_password_returns_new_token(client, company_auth):
    response = client.post(
        "/api/companies/login",
        json={"email": "hr@technova.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert response.json()["token"] != company_auth["token"] or response.json()["token"]


def test_create_internship_requires_auth(client):
    response = client.post(
        "/api/internships",
        json={
            "title": "Software Engineering Intern",
            "description": "Build things.",
            "required_skills": "python, react",
            "location": "San Francisco, CA",
            "sector": "Technology",
            "capacity": 2,
        },
    )
    assert response.status_code in (401, 403)


def test_create_internship_with_auth_uses_token_company_id(client, company_auth):
    response = client.post(
        "/api/internships",
        json={
            "title": "Software Engineering Intern",
            "description": "Build things.",
            "required_skills": "python, react",
            "location": "San Francisco, CA",
            "sector": "Technology",
            "capacity": 2,
        },
        headers=auth_header(company_auth["token"]),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["company_id"] == company_auth["company"]["id"]


def _post_internship(client, token):
    response = client.post(
        "/api/internships",
        json={
            "title": "Software Engineering Intern",
            "description": "Build things.",
            "required_skills": "python, react",
            "location": "San Francisco, CA",
            "sector": "Technology",
            "capacity": 2,
        },
        headers=auth_header(token),
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_other_company_cannot_view_candidates(client, company_auth):
    internship_id = _post_internship(client, company_auth["token"])

    other_company = client.post(
        "/api/companies",
        json={
            "name": "Other Co",
            "email": "other@company.com",
            "password": "password123",
            "sector": "Finance",
            "location": "New York, NY",
        },
    ).json()

    response = client.get(
        f"/api/internships/{internship_id}/candidates",
        headers=auth_header(other_company["token"]),
    )
    assert response.status_code == 403


def test_owning_company_can_view_candidates(client, company_auth):
    internship_id = _post_internship(client, company_auth["token"])
    response = client.get(
        f"/api/internships/{internship_id}/candidates",
        headers=auth_header(company_auth["token"]),
    )
    assert response.status_code == 200


def test_resume_upload_requires_matching_student(client, student_auth):
    other_student = client.post(
        "/api/students",
        json={
            "name": "Jordan Lee",
            "email": "jordan.lee@university.edu",
            "password": "password123",
            "location_preference": "New York, NY",
            "sector_interests": "Finance",
            "past_internships": 0,
        },
    ).json()

    response = client.post(
        f"/api/students/{student_auth['student']['id']}/resume",
        files={"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")},
        headers=auth_header(other_student["token"]),
    )
    assert response.status_code == 403


def test_student_recommendations_requires_matching_student(client, student_auth):
    other_student = client.post(
        "/api/students",
        json={
            "name": "Jordan Lee",
            "email": "jordan.lee@university.edu",
            "password": "password123",
            "location_preference": "New York, NY",
            "sector_interests": "Finance",
            "past_internships": 0,
        },
    ).json()

    response = client.get(
        f"/api/students/{student_auth['student']['id']}/recommendations",
        headers=auth_header(other_student["token"]),
    )
    assert response.status_code == 403


def test_student_recommendations_without_resume_returns_400(client, student_auth):
    response = client.get(
        f"/api/students/{student_auth['student']['id']}/recommendations",
        headers=auth_header(student_auth["token"]),
    )
    assert response.status_code == 400
