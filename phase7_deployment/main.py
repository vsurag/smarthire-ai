from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import json
import re
import io
from dotenv import load_dotenv
import anthropic
import pypdf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv(dotenv_path="../.env")

# ── APP SETUP ─────────────────────────────────────────────
app = FastAPI(
    title="SmartHire AI API",
    description="AI-powered recruitment platform backend",
    version="1.0.0"
)

# ── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── CLAUDE CLIENT ─────────────────────────────────────────
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# ── CANDIDATE DATABASE ────────────────────────────────────
CANDIDATES_DB = {
    "rahul sharma": {
        "name": "Rahul Sharma",
        "experience": 3,
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
        "location": "Hyderabad",
        "salary_expectation": 12,
        "email": "rahul.sharma@email.com"
    },
    "priya patel": {
        "name": "Priya Patel",
        "experience": 4,
        "skills": ["Python", "Django", "MySQL", "AWS", "Docker"],
        "location": "Bangalore",
        "salary_expectation": 18,
        "email": "priya.patel@email.com"
    },
    "arjun reddy": {
        "name": "Arjun Reddy",
        "experience": 1,
        "skills": ["Python", "Flask", "SQLite", "Git"],
        "location": "Hyderabad",
        "salary_expectation": 6,
        "email": "arjun.reddy@email.com"
    },
    "sneha krishnan": {
        "name": "Sneha Krishnan",
        "experience": 5,
        "skills": ["Python", "FastAPI", "LangChain", "PostgreSQL", "Redis"],
        "location": "Chennai",
        "salary_expectation": 25,
        "email": "sneha.krishnan@email.com"
    }
}

JOB_REQUIREMENTS = {
    "title": "Python Developer",
    "min_experience": 2,
    "required_skills": ["Python", "FastAPI", "PostgreSQL", "Git"],
    "nice_to_have": ["Docker", "AWS", "LangChain"],
    "budget_lpa": 20
}

# ── CONVERSATION STORE ────────────────────────────────────
conversation_store = {}


# ══════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ══════════════════════════════════════════════════════════

class JDRequest(BaseModel):
    job_title: str
    company: str
    experience: str
    tone: str = "Professional"

class JDResponse(BaseModel):
    job_description: str
    job_title: str
    company: str

class ScreenRequest(BaseModel):
    job_description: str
    resume: str
    technique: str = "zero-shot"

class ScreenResponse(BaseModel):
    candidate_name: str
    overall_score: int
    recommendation: str
    skills_match: dict
    experience_match: bool
    summary: str
    red_flags: list
    raw_response: str

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    message_count: int

class PipelineRequest(BaseModel):
    candidate_name: str = ""
    resume_text: str = ""

class PipelineResponse(BaseModel):
    candidate: dict
    score: int
    score_breakdown: list
    decision: str
    path: str
    email_draft: str


# ══════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {
        "status": "running",
        "product": "SmartHire AI API",
        "version": "1.0.0",
        "endpoints": [
            "POST /api/generate-jd",
            "POST /api/screen-resume",
            "POST /api/chat",
            "POST /api/run-pipeline",
            "POST /api/extract-pdf",
            "GET  /api/candidates",
            "GET  /docs"
        ]
    }


@app.get("/api/candidates")
def get_candidates():
    return {
        "candidates": [
            {
                "name": c["name"],
                "experience": c["experience"],
                "skills": c["skills"],
                "location": c["location"],
                "salary_expectation": c["salary_expectation"]
            }
            for c in CANDIDATES_DB.values()
        ],
        "total": len(CANDIDATES_DB)
    }


@app.post("/api/generate-jd", response_model=JDResponse)
async def generate_jd(request: JDRequest):
    """Phase 1 — Generate a professional job description."""
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=f"""You are an expert HR professional writing job descriptions.
            Use a {request.tone} tone. Write clear, inclusive, and engaging JDs.""",
            messages=[{
                "role": "user",
                "content": f"""Write a professional job description for:
Job Title: {request.job_title}
Company: {request.company}
Experience: {request.experience}

Include: role summary (2-3 lines), 5 key responsibilities,
5 required skills, 3 nice-to-have skills, 3 benefits."""
            }]
        )
        return JDResponse(
            job_description=message.content[0].text,
            job_title=request.job_title,
            company=request.company
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/screen-resume", response_model=ScreenResponse)
async def screen_resume(request: ScreenRequest):
    """Phase 2 — Screen a resume against a job description."""
    try:
        if request.technique == "chain-of-thought":
            prompt = f"""Think step by step then give final JSON.

JD: {request.job_description}
RESUME: {request.resume}

STEP 1 - List required skills from JD
STEP 2 - Check which are in resume
STEP 3 - Check experience match
STEP 4 - Identify red flags
STEP 5 - Final JSON only:
{{
  "candidate_name": "name",
  "overall_score": 0-100,
  "recommendation": "Strong Yes/Yes/Maybe/No",
  "skills_match": {{"matched": [], "missing": []}},
  "experience_match": true,
  "summary": "2 sentences",
  "red_flags": []
}}"""
        else:
            prompt = f"""Return ONLY valid JSON, no extra text:
{{
  "candidate_name": "name",
  "overall_score": 0-100,
  "recommendation": "Strong Yes/Yes/Maybe/No",
  "skills_match": {{"matched": [], "missing": []}},
  "experience_match": true,
  "summary": "2 sentences",
  "red_flags": []
}}

JD: {request.job_description}
RESUME: {request.resume}"""

        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system="You are an expert technical recruiter. Return only valid JSON.",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text

        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            raise HTTPException(status_code=500, detail="Could not parse AI response")

        return ScreenResponse(
            candidate_name=result.get("candidate_name", "Unknown"),
            overall_score=result.get("overall_score", 0),
            recommendation=result.get("recommendation", "N/A"),
            skills_match=result.get("skills_match", {}),
            experience_match=result.get("experience_match", False),
            summary=result.get("summary", ""),
            red_flags=result.get("red_flags", []),
            raw_response=raw
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Phase 3 — Candidate Q&A chatbot with memory."""
    JOB_CONTEXT = """Company: SmartHire Technologies | Role: Python Developer
Experience: 2+ years | Location: Hyderabad (Hybrid) | Salary: ₹8-15 LPA
Required: Python, FastAPI, PostgreSQL, Git
Nice to have: Docker, AWS, LangChain
Benefits: Health insurance, 15 days leave, L&D budget, flexible hours"""

    if request.session_id not in conversation_store:
        conversation_store[request.session_id] = []

    history = conversation_store[request.session_id]
    history.append({"role": "user", "content": request.message})

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=f"""You are a friendly HR assistant for SmartHire Technologies.
Job details: {JOB_CONTEXT}
Be warm, professional, and helpful. Keep replies concise (2-3 sentences).""",
            messages=history
        )
        reply = response.content[0].text
        history.append({"role": "assistant", "content": reply})
        conversation_store[request.session_id] = history[-20:]

        return ChatResponse(
            reply=reply,
            session_id=request.session_id,
            message_count=len(conversation_store[request.session_id])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/extract-pdf")
async def extract_pdf(file: UploadFile = File(...)):
    """Extract text from an uploaded PDF resume."""
    try:
        contents = await file.read()
        pdf_reader = pypdf.PdfReader(io.BytesIO(contents))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"

        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")

        return {
            "filename": file.filename,
            "text": text.strip(),
            "pages": len(pdf_reader.pages)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/run-pipeline", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest):
    """Phase 5+6 — Run the full LangGraph hiring pipeline."""

    # If resume_text provided, extract candidate info using Claude
    if request.resume_text:
        try:
            extract_msg = client.messages.create(
                model=MODEL,
                max_tokens=512,
                system="Extract candidate info from resume. Return ONLY valid JSON, no extra text.",
                messages=[{
                    "role": "user",
                    "content": f"""Extract from this resume:
{request.resume_text}

Return ONLY this JSON:
{{
    "name": "full name",
    "experience": years as integer,
    "skills": ["skill1", "skill2"],
    "location": "city",
    "salary_expectation": expected salary in LPA as integer or 10,
    "email": "email or candidate@email.com"
}}"""
                }]
            )
            raw = extract_msg.content[0].text
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            candidate = json.loads(match.group()) if match else {}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")
    else:
        key = request.candidate_name.lower().strip()
        if key not in CANDIDATES_DB:
            raise HTTPException(
                status_code=404,
                detail=f"Candidate '{request.candidate_name}' not found"
            )
        candidate = CANDIDATES_DB[key]

    # Score the candidate
    score = 0
    breakdown = []

    exp = candidate.get("experience", 0)
    if exp >= JOB_REQUIREMENTS["min_experience"]:
        exp_score = min(30, exp * 8)
        score += exp_score
        breakdown.append(f"Experience: {exp} yrs (+{exp_score}pts)")
    else:
        breakdown.append(f"Experience too low: {exp} yrs")

    skills = candidate.get("skills", [])
    matched = [s for s in JOB_REQUIREMENTS["required_skills"] if s in skills]
    missing  = [s for s in JOB_REQUIREMENTS["required_skills"] if s not in skills]
    skill_score = int(len(matched) / len(JOB_REQUIREMENTS["required_skills"]) * 40)
    score += skill_score
    breakdown.append(f"Skills: {len(matched)}/{len(JOB_REQUIREMENTS['required_skills'])} matched (+{skill_score}pts)")

    bonus = [s for s in JOB_REQUIREMENTS["nice_to_have"] if s in skills]
    bonus_score = min(15, len(bonus) * 5)
    score += bonus_score
    if bonus:
        breakdown.append(f"Bonus skills: {bonus} (+{bonus_score}pts)")

    salary = candidate.get("salary_expectation", 0)
    if salary <= JOB_REQUIREMENTS["budget_lpa"]:
        score += 15
        breakdown.append(f"Salary fits budget (+15pts)")
    else:
        breakdown.append(f"Salary over budget")

    # Route decision
    path = "interviewer" if score >= 55 else "rejector"
    name = candidate.get("name", "Candidate")
    email = candidate.get("email", "candidate@email.com")

    # Draft email with Claude
    if path == "interviewer":
        email_prompt = f"""Write a warm professional interview invitation for:
Candidate: {name}
Email: {email}
Experience: {exp} years
Skills: {', '.join(skills[:3])}
Score: {score}/100

Role: Python Developer at SmartHire Technologies
Interview slot: Next Monday 10:00 AM IST (Google Meet)
Format: TO / SUBJECT / email body"""
    else:
        email_prompt = f"""Write a kind encouraging rejection email for:
Candidate: {name}
Email: {email}
Score: {score}/100
Missing skills: {missing}

Be warm, thank them, mention gaps constructively,
encourage them to upskill and apply again.
Format: TO / SUBJECT / email body"""

    try:
        email_response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system="You are a professional, empathetic HR at SmartHire Technologies.",
            messages=[{"role": "user", "content": email_prompt}]
        )
        email_draft = email_response.content[0].text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return PipelineResponse(
        candidate=candidate,
        score=score,
        score_breakdown=breakdown,
        decision="PROCEED TO INTERVIEW" if path == "interviewer" else "NOT SELECTED",
        path=path,
        email_draft=email_draft
    )

class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str

@app.post("/api/send-email")
async def send_email(request: SendEmailRequest):
    """Send real email via Gmail SMTP"""
    try:
        smtp_email = os.getenv("SMTP_EMAIL")
        smtp_password = os.getenv("SMTP_PASSWORD")

        if not smtp_email or not smtp_password:
            raise HTTPException(status_code=500, detail="Email credentials not configured")

        msg = MIMEMultipart()
        msg["From"] = smtp_email
        msg["To"] = request.to_email
        msg["Subject"] = request.subject
        msg.attach(MIMEText(request.body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_email, smtp_password)
            server.send_message(msg)

        return {"status": "sent", "to": request.to_email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
# ── RUN ───────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)