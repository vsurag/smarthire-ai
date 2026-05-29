import os
import json
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# ── SAMPLE DATA ──────────────────────────────────────────
# In a real app this comes from uploaded files
# For now we hardcode to focus on prompt engineering

SAMPLE_JD = """
Job Title: Python Developer
Company: SmartHire
Experience: 2+ years

Required Skills:
- Python, FastAPI, Django
- REST APIs
- PostgreSQL
- Git
- Problem solving

Nice to Have:
- Docker
- AWS
- LangChain
"""

SAMPLE_RESUME = """
Name: Rahul Sharma
Experience: 3 years

Work History:
- Backend Developer at TechCorp (2 years)
  Built REST APIs using FastAPI and Python
  Worked with PostgreSQL databases
  Used Git daily for version control

- Junior Developer at StartupXYZ (1 year)
  Python scripting and automation
  Basic AWS deployment

Skills: Python, FastAPI, PostgreSQL, Git, Docker, REST APIs
Education: B.Tech Computer Science
"""

# ── ZERO-SHOT PROMPTING ───────────────────────────────────
# We give NO examples — just instructions
# Claude figures it out from the prompt alone

def screen_resume_zero_shot(resume, job_description):
    """Zero-shot: no examples given, just clear instructions"""

    message = client.messages.create(
        model=os.getenv("CLAUDE_MODEL"),
        max_tokens=1024,
        system="""You are an expert technical recruiter. 
        Analyze resumes against job descriptions and return 
        ONLY a valid JSON response. No extra text.""",
        messages=[
            {
                "role": "user",
                "content": f"""Screen this resume against the job description.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume}

Return ONLY this JSON structure:
{{
    "candidate_name": "name here",
    "overall_score": 0-100,
    "recommendation": "Strong Yes / Yes / Maybe / No",
    "skills_match": {{
        "matched": ["skill1", "skill2"],
        "missing": ["skill1", "skill2"]
    }},
    "experience_match": true or false,
    "summary": "2 sentence summary",
    "red_flags": ["any concerns"] 
}}"""
            }
        ]
    )
    return message.content[0].text


# ── FEW-SHOT PROMPTING ────────────────────────────────────
# We give ONE example of what good output looks like
# This dramatically improves consistency

def screen_resume_few_shot(resume, job_description):
    """Few-shot: we show Claude an example first"""

    message = client.messages.create(
        model=os.getenv("CLAUDE_MODEL"),
        max_tokens=1024,
        system="""You are an expert technical recruiter.
        Always return ONLY valid JSON. No extra text, no markdown.""",
        messages=[
            {
                "role": "user",
                "content": """Screen this resume against the job description.

JOB DESCRIPTION: Python developer, 2 years exp, needs Django, PostgreSQL

RESUME: John, 1 year exp, knows Django basics, no PostgreSQL

Return JSON with overall_score, recommendation, summary."""
            },
            {
                "role": "assistant",  # ← this is the EXAMPLE we show Claude
                "content": """{
    "candidate_name": "John",
    "overall_score": 35,
    "recommendation": "No",
    "summary": "Candidate has only 1 year of experience vs required 2 years. Missing PostgreSQL which is a core requirement.",
    "skills_match": {"matched": ["Django"], "missing": ["PostgreSQL"]},
    "experience_match": false,
    "red_flags": ["Insufficient experience", "Missing core database skill"]
}"""
            },
            {
                "role": "user",  # ← now the REAL request
                "content": f"""Screen this resume against the job description.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume}

Return ONLY JSON with: candidate_name, overall_score, recommendation, 
skills_match (matched/missing lists), experience_match, summary, red_flags"""
            }
        ]
    )
    return message.content[0].text


# ── CHAIN OF THOUGHT PROMPTING ────────────────────────────
# We ask Claude to THINK STEP BY STEP before giving the answer
# This improves accuracy on complex reasoning

def screen_resume_chain_of_thought(resume, job_description):
    """Chain-of-thought: ask Claude to reason before answering"""

    message = client.messages.create(
        model=os.getenv("CLAUDE_MODEL"),
        max_tokens=2048,
        system="You are an expert technical recruiter.",
        messages=[
            {
                "role": "user",
                "content": f"""Screen this resume against the job description.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume}

Think through this step by step:
STEP 1 - List every required skill from the JD
STEP 2 - Check which ones appear in the resume  
STEP 3 - Calculate experience match (years required vs years had)
STEP 4 - Identify any red flags
STEP 5 - Give final score out of 100 and recommendation

Show your thinking for each step, then end with a JSON summary."""
            }
        ]
    )
    return message.content[0].text


# ── MAIN RUNNER ───────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("SmartHire - Resume Screener (Prompt Engineering Demo)")
    print("=" * 60)

    print("\n🔵 ZERO-SHOT RESULT:")
    print("-" * 40)
    result = screen_resume_zero_shot(SAMPLE_RESUME, SAMPLE_JD)
    print(result)

    # Parse and pretty print the JSON
    try:
        parsed = json.loads(result)
        print(f"\n✅ Score: {parsed['overall_score']}/100")
        print(f"✅ Recommendation: {parsed['recommendation']}")
    except:
        print("(JSON parsing note: check raw output above)")

    print("\n\n🟡 FEW-SHOT RESULT:")
    print("-" * 40)
    result2 = screen_resume_few_shot(SAMPLE_RESUME, SAMPLE_JD)
    print(result2)

    print("\n\n🟢 CHAIN-OF-THOUGHT RESULT:")
    print("-" * 40)
    result3 = screen_resume_chain_of_thought(SAMPLE_RESUME, SAMPLE_JD)
    print(result3)

    print("\n" + "=" * 60)
    print("Notice how each prompting technique gives different output!")
    print("=" * 60)