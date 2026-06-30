"""
Bulk import script: internship CSV + resume PDFs into InternMatch.
- Imports all actively_hiring internships from Internship.csv
- Imports 5 sample resumes per category from the Resumes PDF folder
Run with backend already running on port 8088.
"""

import csv
import os
import re
import time
import unicodedata
import pathlib
import requests

BASE_URL = "http://127.0.0.1:8088/api"
PASSWORD = "password123"
RESUME_FOLDER = r"C:\Users\amish\OneDrive\Documents\Downloads\archive\Resumes PDF"
CSV_PATH = r"C:\Users\amish\OneDrive\Documents\Downloads\Internship.csv"
RESUMES_PER_CATEGORY = 5

# ── sector inference ─────────────────────────────────────────────────────────
SECTOR_MAP = [
    (r"software|web|app|mobile|flutter|react|node|python|django|java|php|\.net|cloud|devops|backend|frontend|full.?stack|api|database|sql|blockchain|unreal|unity|game|ai|machine.?learning|data.?science|nlp|computer|coding|programming", "Technology"),
    (r"digital.?marketing|seo|sem|social.?media|content.?writ|copywriting|graphic.?design|video.?edit|photo|creative|brand|marketing|advertising|pr|public.?relation|media", "Marketing & Media"),
    (r"finance|account|tax|audit|banking|investment|equity|ca |chartered|cost|bookkeeping|tally|mba.?finance", "Finance"),
    (r"hr|human.?resource|recruit|talent", "Human Resources"),
    (r"sales|business.?development|b2b|b2c|inside.?sales|field.?sales|telecalling|telesales|client", "Sales & Business Development"),
    (r"teaching|education|tutor|academic|faculty|curriculum|e.?learning|edtech|training", "Education"),
    (r"fashion|textile|apparel|merchandis|design.*(fashion|interior|product|graphic|ui|ux)|interior.?design|architect", "Design"),
    (r"mechanical|civil|electrical|electronic|embedded|hardware|robotics|aerospace|automobile", "Engineering"),
    (r"health|medical|pharma|clinical|nutrition|diet|biology|biotech|lab|hospital|dentis", "Healthcare"),
    (r"law|legal|advocate|compliance|ip |patent|judiciary", "Legal"),
    (r"ngo|social.?work|volunte|non.?profit|fundrais|charity|welfare", "Social Sector"),
    (r"operation|logistics|supply.?chain|procurement|warehouse|project.?manage|general.?manage|admin|office|back.?office", "Operations"),
    (r"research|analyst|data.?entry|market.?research|survey|business.?research|policy", "Research & Analytics"),
    (r"event|hospitality|travel|tourism|hotel|culinary|chef|baking", "Events & Hospitality"),
]


def infer_sector(role: str) -> str:
    role_lower = role.lower()
    for pattern, sector in SECTOR_MAP:
        if re.search(pattern, role_lower):
            return sector
    return "General"


# ── skills inference ─────────────────────────────────────────────────────────
SKILLS_MAP = {
    "Technology": "python, javascript, sql, git, api, software development",
    "Marketing & Media": "digital marketing, social media, content writing, seo, canva, analytics",
    "Finance": "accounting, tally, excel, financial analysis, taxation, ms office",
    "Human Resources": "recruitment, hr, communication, ms office, interviewing, excel",
    "Sales & Business Development": "sales, communication, negotiation, crm, ms office, business development",
    "Education": "teaching, communication, content development, ms office, research",
    "Design": "graphic design, adobe, figma, creativity, ui/ux, canva",
    "Engineering": "autocad, solidworks, electrical, mechanical, embedded systems, matlab",
    "Healthcare": "research, biology, chemistry, clinical, communication, ms office",
    "Legal": "legal research, drafting, ms office, communication, analysis",
    "Social Sector": "communication, ms office, social work, research, outreach",
    "Operations": "ms office, excel, communication, project management, logistics",
    "Research & Analytics": "research, excel, data analysis, ms office, python",
    "Events & Hospitality": "event management, communication, hospitality, ms office, coordination",
    "General": "communication, ms office, teamwork, research",
}


def infer_skills(role: str, sector: str) -> str:
    return SKILLS_MAP.get(sector, SKILLS_MAP["General"])


# ── helpers ───────────────────────────────────────────────────────────────────
def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[\s-]+", "_", text)[:40]


_email_counter = 0


def unique_email(prefix: str, domain: str = "internmatch.example.com") -> str:
    global _email_counter
    _email_counter += 1
    slug = slugify(prefix)[:30]
    return f"{slug}_{_email_counter}@{domain}"


def post(endpoint: str, json_data: dict, token: str | None = None) -> dict | None:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.post(f"{BASE_URL}{endpoint}", json=json_data, headers=headers, timeout=10)
        if r.status_code in (200, 201):
            return r.json()
        return None
    except Exception:
        return None


def upload_resume(student_id: int, pdf_path: str, token: str) -> bool:
    try:
        with open(pdf_path, "rb") as f:
            r = requests.post(
                f"{BASE_URL}/students/{student_id}/resume",
                files={"file": (os.path.basename(pdf_path), f, "application/pdf")},
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
        return r.status_code == 200
    except Exception:
        return False


# ── internship import ─────────────────────────────────────────────────────────
def import_internships() -> int:
    print("\n=== Importing Internships ===")
    company_tokens: dict[str, str] = {}  # company_name -> token
    company_ids: dict[str, int] = {}     # company_name -> id
    imported = 0
    skipped = 0

    with open(CSV_PATH, encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r.get("actively_hiring", "").strip() == "1.0"]

    print(f"  Actively hiring rows: {len(rows)}")

    for row in rows:
        company_name = row["company_name"].strip()
        role = row["Type_of_internship"].strip()
        location = row["location"].strip() or "Work From Home"
        sector = infer_sector(role)

        # Register company if first time seen
        if company_name not in company_tokens:
            email = unique_email(company_name, "corp.internmatch.example.com")
            result = post("/companies", {
                "name": company_name,
                "email": email,
                "password": PASSWORD,
                "sector": sector,
                "location": location,
            })
            if result:
                company_tokens[company_name] = result["token"]
                company_ids[company_name] = result["company"]["id"]
            else:
                skipped += 1
                continue

        token = company_tokens[company_name]
        skills = infer_skills(role, sector)

        result = post("/internships", {
            "title": role[:200],
            "description": f"{role} internship opportunity. Join {company_name} and gain hands-on experience.",
            "required_skills": skills,
            "required_qualifications": "bachelor",
            "location": location[:200],
            "sector": sector[:100],
            "capacity": 2,
        }, token=token)

        if result:
            imported += 1
        else:
            skipped += 1

        if imported % 100 == 0 and imported > 0:
            print(f"  ... {imported} internships imported")

    print(f"  Done: {imported} imported, {skipped} skipped")
    return imported


# ── resume import ─────────────────────────────────────────────────────────────
CATEGORY_SKILLS = {
    "Accountant": "accounting, tally, excel, taxation, financial statements, auditing",
    "Advocate": "legal research, drafting, litigation, contract law, ms office",
    "Agricultural": "agriculture, research, field work, data collection, report writing",
    "Agriculture": "agronomy, soil science, plant biology, field operations",
    "Apparel": "fashion design, merchandising, textile, garment production",
    "Architect": "autocad, revit, 3d modeling, site supervision, architectural design",
    "Arts": "creative design, illustration, photography, visual arts",
    "Automobile": "autocad, mechanical engineering, vehicle systems, maintenance",
    "Aviation": "aviation operations, safety procedures, communication",
    "Banking": "banking operations, finance, excel, customer service, financial analysis",
    "Blockchain": "blockchain, ethereum, solidity, web3, smart contracts, python",
    "BPO resumes": "customer service, communication, bpo, data entry, ms office",
    "BusinessAnalyst": "business analysis, sql, excel, requirements gathering, documentation",
    "Business Analyst resumes": "business analysis, sql, excel, requirements gathering",
    "Building _Construction resumes": "civil engineering, autocad, construction management",
    "CivilEngineer": "civil engineering, autocad, structural analysis, site supervision",
    "Civil Engineer resumes": "civil engineering, autocad, structural design",
    "Consult": "consulting, research, analysis, ms office, communication",
    "Consultant": "consulting, strategy, analysis, ms office, presentation",
    "Consultant resumes": "business consulting, research, presentation, communication",
    "Data Science": "python, machine learning, data analysis, pandas, numpy, sql, statistics",
    "data science resumes": "python, machine learning, data analysis, sql, statistics",
    "DataScience": "python, machine learning, data science, tensorflow, sql",
    "Database": "sql, mysql, postgresql, database design, query optimization",
    "Database resumes": "sql, database administration, mysql, postgresql",
    "Design": "graphic design, adobe, figma, ui/ux, canva, illustrator",
    "Designer": "graphic design, adobe photoshop, illustrator, ui/ux design",
    "Designing resumes": "graphic design, adobe, figma, creativity",
    "DevOps Engineer": "devops, docker, kubernetes, ci/cd, linux, aws, jenkins",
    "DevOps Engineer resumes": "devops, docker, kubernetes, linux, aws",
    "DevOpsEngineer": "devops, aws, docker, kubernetes, terraform, ci/cd",
    "Digital": "digital marketing, seo, social media, content, analytics",
    "Digital Media": "digital marketing, social media, content creation, video editing",
    "Digital Media resumes": "digital marketing, social media, content",
    "DOT": ".net, c#, asp.net, sql server, mvc",
    "DotNet Developer resumes": ".net, c#, asp.net, sql server",
    "Education": "teaching, curriculum development, communication, ms office",
    "Education resumes": "teaching, e-learning, curriculum, communication",
    "ElectricalEngineer": "electrical engineering, circuit design, matlab, plc, power systems",
    "Electrical Engineering resumes": "electrical engineering, autocad, circuit design",
    "ETL": "etl, sql, data warehousing, python, informatica",
    "ETL Developer": "etl, sql, data warehousing, informatica, talend",
    "ETL Developer resumes": "etl, sql, data integration, informatica",
    "Finance": "financial analysis, excel, accounting, investment, financial modeling",
    "Finance resumes": "finance, excel, accounting, financial analysis",
    "Food": "food technology, quality control, food safety, haccp",
    "Food_Beverages resumes": "food technology, quality control, fssai",
    "Health_Fitness resumes": "health, fitness, nutrition, communication",
    "HealthFitness": "health coaching, fitness, nutrition, wellness",
    "HR": "human resources, recruitment, payroll, ms office, communication",
    "HR resumes": "hr, recruitment, talent acquisition, ms office",
    "Human Resources": "human resources, recruitment, talent management, excel, communication",
    "Information Technology": "it support, networking, windows, linux, troubleshooting",
    "Information Technology resumes": "it support, networking, ms office",
    "IT": "information technology, networking, system administration, sql",
    "Java Developer resumes": "java, spring boot, maven, sql, rest api",
    "JavaDeveloper": "java, spring boot, hibernate, sql, maven, rest api",
    "Management": "project management, ms office, leadership, communication",
    "Managment resumes": "management, ms office, leadership, teamwork",
    "MechanicalEngineer": "mechanical engineering, autocad, solidworks, manufacturing",
    "Mechanical Engineer resumes": "mechanical design, autocad, solidworks, catia",
    "Network Security Engineer resumes": "network security, firewall, penetration testing, cissp",
    "NSE": "network security, ethical hacking, firewall, siem",
    "OperationManager": "operations management, supply chain, logistics, excel",
    "Operations Manager resumes": "operations, project management, supply chain",
    "PBO": "project management, pmp, ms project, stakeholder management",
    "PMO": "pmo, project management, ms project, governance, reporting",
    "PMO resumes": "project management office, ms project, governance",
    "Public": "public relations, communication, media, pr campaigns",
    "Public Relations resumes": "public relations, media, communication, press release",
    "PythonDeveloper": "python, django, flask, rest api, sql, aws",
    "Python Developer": "python, django, flask, machine learning, sql",
    "Python Developer resumes": "python, django, sql, rest api",
    "React": "react, javascript, html, css, redux, node.js",
    "React Developer": "react, javascript, typescript, node.js, html, css",
    "React Developer resumes": "react, javascript, html, css, redux",
    "Sales": "sales, negotiation, crm, communication, business development",
    "Sales resumes": "sales, customer service, communication, crm",
    "SAP Developer": "sap, abap, s/4hana, bw, hana, sql",
    "SAP Developer resumes": "sap, abap, s/4hana, sql",
    "SAPDeveloper": "sap, abap, s/4hana, hana, fiori",
    "SQL": "sql, mysql, postgresql, plsql, database, query optimization",
    "SQL Developer resumes": "sql, pl/sql, oracle, database",
    "Testing": "software testing, selenium, manual testing, automation, jira, qa",
    "Testing resumes": "qa testing, selenium, manual testing, test cases",
    "WebDesigning": "html, css, javascript, photoshop, figma, responsive design",
    "web designing resumes": "web design, html, css, javascript, figma",
}


def import_resumes() -> int:
    from app.database import SessionLocal, init_db
    from app.models import Student

    print("\n=== Importing Resumes ===")
    init_db()
    db = SessionLocal()

    resume_root = pathlib.Path(RESUME_FOLDER)
    categories = [d for d in resume_root.iterdir() if d.is_dir()]
    imported = 0

    for cat_dir in sorted(categories):
        category = cat_dir.name
        pdfs = list(cat_dir.glob("*.pdf"))[:RESUMES_PER_CATEGORY]
        if not pdfs:
            continue

        sector = infer_sector(category)
        skills = CATEGORY_SKILLS.get(category, infer_skills(category, sector))
        qualifications = "bachelor, " + sector.lower().replace(" & ", ", ")

        count = 0
        for i, _ in enumerate(pdfs):
            email = unique_email(f"{category}_student", "students.internmatch.example.com")
            result = post("/students", {
                "name": f"{category} Candidate {i + 1}",
                "email": email,
                "password": PASSWORD,
                "location_preference": "Work From Home",
                "sector_interests": category,
                "past_internships": 0,
            })
            if not result:
                continue

            student_id = result["student"]["id"]

            # Set skills/qualifications directly since PDFs are image-based
            student = db.query(Student).filter(Student.id == student_id).first()
            if student:
                student.skills = skills
                student.qualifications = qualifications
                student.resume_text = f"{category} professional with experience in {skills}."
                student.resume_filename = f"{category}_resume.pdf"
                db.commit()
                imported += 1
                count += 1

        print(f"  {category}: {count} students imported")

    db.close()
    print(f"  Done: {imported} students imported with skills")
    return imported


# ── main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    start = time.time()
    n_internships = import_internships()
    n_resumes = import_resumes()
    elapsed = time.time() - start
    print(f"\n=== Import complete in {elapsed:.0f}s ===")
    print(f"  Internships: {n_internships}")
    print(f"  Resumes:     {n_resumes}")
