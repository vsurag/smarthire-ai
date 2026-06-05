import os
import json
import re
import anthropic
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

st.set_page_config(
    page_title="SmartHire — AI Recruitment",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── GLOBAL CSS ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    background: #0d1117 !important;
    font-family: 'DM Sans', sans-serif;
    color: #e2e8f0;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #0a0f1a !important;
    border-right: 1px solid #1e2d47 !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] .stRadio label {
    color: #94a3b8 !important;
    font-size: 13px !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
    color: #94a3b8 !important;
}

/* ── HIDE DEFAULT STREAMLIT CHROME ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
[data-testid="stToolbar"] { display: none; }

/* ── MAIN CONTENT ── */
.main .block-container {
    padding: 0 2rem 2rem 2rem !important;
    max-width: 1200px !important;
}

/* ── TOP BAR ── */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 0 24px 0;
    border-bottom: 1px solid #1e2d47;
    margin-bottom: 28px;
}
.topbar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
}
.topbar-logo {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, #1d4ed8, #3b82f6);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; font-weight: 700; color: white;
}
.topbar-name {
    font-size: 17px; font-weight: 600;
    color: #f1f5f9; letter-spacing: -0.3px;
}
.topbar-sub { font-size: 11px; color: #64748b; margin-top: 1px; }
.topbar-badge {
    background: #1e3a5f;
    color: #60a5fa;
    border: 1px solid #1d4ed8;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 11px; font-weight: 500;
    font-family: 'DM Mono', monospace;
}

/* ── PAGE TITLE ── */
.page-title {
    font-size: 22px; font-weight: 600;
    color: #f1f5f9; letter-spacing: -0.5px;
    margin-bottom: 4px;
}
.page-sub {
    font-size: 13px; color: #64748b;
    margin-bottom: 24px;
}

/* ── STAT CARDS ── */
.stat-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 28px;
}
.stat-card {
    background: #111827;
    border: 1px solid #1e2d47;
    border-radius: 12px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
}
.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #1d4ed8, #3b82f6);
}
.stat-label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }
.stat-value { font-size: 26px; font-weight: 600; color: #f1f5f9; letter-spacing: -1px; }
.stat-delta { font-size: 11px; color: #22c55e; margin-top: 4px; }
.stat-icon {
    position: absolute; right: 16px; top: 16px;
    font-size: 20px; opacity: 0.3;
}

/* ── SECTION CARD ── */
.section-card {
    background: #111827;
    border: 1px solid #1e2d47;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 20px;
}
.section-card-title {
    font-size: 13px; font-weight: 600;
    color: #94a3b8; text-transform: uppercase;
    letter-spacing: 0.8px; margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
}
.section-card-title::before {
    content: '';
    width: 3px; height: 14px;
    background: #3b82f6;
    border-radius: 2px;
    display: inline-block;
}

/* ── FEATURE GRID ── */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 14px;
    margin-bottom: 24px;
}
.feature-tile {
    background: #0d1825;
    border: 1px solid #1e2d47;
    border-radius: 12px;
    padding: 18px 20px;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
}
.feature-tile:hover { border-color: #3b82f6; background: #111f33; }
.feature-tile-icon { font-size: 22px; margin-bottom: 8px; }
.feature-tile-name { font-size: 14px; font-weight: 600; color: #e2e8f0; margin-bottom: 4px; }
.feature-tile-desc { font-size: 12px; color: #64748b; line-height: 1.5; }
.feature-tile-phase {
    display: inline-block;
    margin-top: 10px;
    background: #1e3a5f;
    color: #60a5fa;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 10px;
    font-family: 'DM Mono', monospace;
}

/* ── PIPELINE TIMELINE ── */
.pipeline {
    display: flex;
    align-items: center;
    gap: 0;
    margin: 20px 0;
    overflow-x: auto;
}
.pipe-node {
    display: flex; flex-direction: column; align-items: center;
    min-width: 110px;
}
.pipe-dot {
    width: 36px; height: 36px;
    border-radius: 50%;
    background: #1e2d47;
    border: 2px solid #1d4ed8;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
    position: relative;
    z-index: 1;
}
.pipe-dot.active { background: #1d4ed8; }
.pipe-dot.done { background: #15803d; border-color: #22c55e; }
.pipe-dot.fail { background: #7f1d1d; border-color: #ef4444; }
.pipe-label { font-size: 10px; color: #64748b; margin-top: 6px; text-align: center; }
.pipe-line {
    flex: 1; height: 2px;
    background: #1e2d47;
    min-width: 30px;
}
.pipe-line.done { background: #22c55e; }

/* ── SCORE RING ── */
.score-ring-wrap {
    display: flex; flex-direction: column; align-items: center;
    padding: 20px;
}
.score-ring {
    width: 110px; height: 110px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-direction: column;
    font-size: 28px; font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 10px;
    position: relative;
}
.score-high-bg { background: conic-gradient(#22c55e var(--pct), #1e2d47 0); box-shadow: 0 0 24px #22c55e33; }
.score-mid-bg  { background: conic-gradient(#f59e0b var(--pct), #1e2d47 0); box-shadow: 0 0 24px #f59e0b33; }
.score-low-bg  { background: conic-gradient(#ef4444 var(--pct), #1e2d47 0); box-shadow: 0 0 24px #ef444433; }
.score-inner {
    width: 82px; height: 82px; border-radius: 50%;
    background: #111827;
    display: flex; align-items: center; justify-content: center;
    flex-direction: column;
    position: absolute;
}
.score-num { font-size: 24px; font-weight: 700; line-height: 1; }
.score-denom { font-size: 10px; color: #64748b; }

/* ── PILL TAGS ── */
.pill-green { display:inline-block; background:#14532d; color:#4ade80; border:1px solid #16a34a; border-radius:20px; padding:2px 10px; font-size:11px; margin:2px; }
.pill-red   { display:inline-block; background:#450a0a; color:#f87171; border:1px solid #dc2626; border-radius:20px; padding:2px 10px; font-size:11px; margin:2px; }
.pill-blue  { display:inline-block; background:#1e3a5f; color:#60a5fa; border:1px solid #1d4ed8; border-radius:20px; padding:2px 10px; font-size:11px; margin:2px; }

/* ── DECISION BADGE ── */
.badge-proceed { background:#14532d; color:#4ade80; border:1px solid #16a34a; border-radius:8px; padding:8px 18px; font-size:14px; font-weight:600; display:inline-block; }
.badge-reject  { background:#450a0a; color:#f87171; border:1px solid #dc2626; border-radius:8px; padding:8px 18px; font-size:14px; font-weight:600; display:inline-block; }

/* ── INPUTS ── */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: #0d1825 !important;
    border: 1px solid #1e2d47 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px #1d4ed820 !important;
}

/* ── BUTTONS ── */
.stButton button {
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
    transition: opacity 0.2s !important;
}
.stButton button:hover { opacity: 0.88 !important; }

/* ── CHAT ── */
.chat-msg-user {
    background: #1e3a5f; border-radius: 12px 12px 4px 12px;
    padding: 12px 16px; margin: 8px 0; margin-left: 60px;
    color: #e2e8f0; font-size: 13px; line-height: 1.6;
}
.chat-msg-bot {
    background: #111827; border: 1px solid #1e2d47;
    border-radius: 12px 12px 12px 4px;
    padding: 12px 16px; margin: 8px 0; margin-right: 60px;
    color: #e2e8f0; font-size: 13px; line-height: 1.6;
}
.chat-avatar { font-size: 18px; margin-bottom: 4px; }

/* ── EMAIL BLOCK ── */
.email-block {
    background: #0a0f1a;
    border: 1px solid #1e2d47;
    border-radius: 10px;
    padding: 20px;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: #94a3b8;
    line-height: 1.8;
    white-space: pre-wrap;
}

/* ── NAV RADIO OVERRIDE ── */
[data-testid="stSidebar"] .stRadio > div {
    gap: 4px !important;
}
[data-testid="stSidebar"] .stRadio > div > label {
    background: transparent !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    transition: background 0.15s !important;
    color: #94a3b8 !important;
}
[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: #111827 !important;
    color: #e2e8f0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── CLIENT ────────────────────────────────────────────────
@st.cache_resource
def get_client():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

client = get_client()
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# ── SIDEBAR ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:20px 16px 16px 16px; border-bottom:1px solid #1e2d47; margin-bottom:16px;'>
        <div style='display:flex;align-items:center;gap:10px;'>
            <div style='width:30px;height:30px;background:linear-gradient(135deg,#1d4ed8,#3b82f6);border-radius:7px;display:flex;align-items:center;justify-content:center;font-weight:700;color:white;font-size:14px;'>S</div>
            <div>
                <div style='color:#f1f5f9;font-weight:600;font-size:14px;'>SmartHire</div>
                <div style='color:#64748b;font-size:10px;'>AI Recruitment Platform</div>
            </div>
        </div>
    </div>
    <div style='padding:0 8px;margin-bottom:8px;font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:0.8px;font-weight:600;'>Platform</div>
    """, unsafe_allow_html=True)

    page = st.radio("", [
        "⬡  Dashboard",
        "📝  JD Generator",
        "🔍  Resume Screener",
        "💬  Candidate Chat",
        "🤖  Hiring Pipeline",
    ], label_visibility="collapsed")

    st.markdown("""
    <div style='margin-top:32px;padding:14px 8px 0 8px;border-top:1px solid #1e2d47;'>
        <div style='font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;'>Stack</div>
        <div style='font-size:11px;color:#64748b;line-height:2.2;font-family:"DM Mono",monospace;'>
            Claude API · LangChain<br>LangGraph · ChromaDB<br>RAG · ReAct · Streamlit
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── TOP BAR ───────────────────────────────────────────────
st.markdown("""
<div class="topbar">
    <div class="topbar-brand">
        <div class="topbar-logo">S</div>
        <div>
            <div class="topbar-name">SmartHire AI</div>
            <div class="topbar-sub">Recruitment Intelligence Platform</div>
        </div>
    </div>
    <div class="topbar-badge">● LIVE · Claude Sonnet</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════
if "Dashboard" in page:
    st.markdown('<div class="page-title">Platform Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Your AI-powered recruitment pipeline — 7 phases, fully integrated.</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="stat-row">
        <div class="stat-card">
            <div class="stat-icon">📝</div>
            <div class="stat-label">JDs Generated</div>
            <div class="stat-value">247</div>
            <div class="stat-delta">↑ 12 this week</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🔍</div>
            <div class="stat-label">Resumes Screened</div>
            <div class="stat-value">1,842</div>
            <div class="stat-delta">↑ 89 this week</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">✅</div>
            <div class="stat-label">Interviews Scheduled</div>
            <div class="stat-value">134</div>
            <div class="stat-delta">↑ 7 this week</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">⚡</div>
            <div class="stat-label">Avg. Screen Time</div>
            <div class="stat-value">3.2s</div>
            <div class="stat-delta">↓ 0.4s faster</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-card">
        <div class="section-card-title">Platform Features</div>
        <div class="feature-grid">
            <div class="feature-tile">
                <div class="feature-tile-icon">📝</div>
                <div class="feature-tile-name">JD Generator</div>
                <div class="feature-tile-desc">Generate professional job descriptions with tone control and instant download.</div>
                <span class="feature-tile-phase">Phase 1 · GenAI Foundations</span>
            </div>
            <div class="feature-tile">
                <div class="feature-tile-icon">🔍</div>
                <div class="feature-tile-name">Resume Screener</div>
                <div class="feature-tile-desc">Score resumes with zero-shot, few-shot, or chain-of-thought prompting.</div>
                <span class="feature-tile-phase">Phase 2 · Prompt Engineering</span>
            </div>
            <div class="feature-tile">
                <div class="feature-tile-icon">💬</div>
                <div class="feature-tile-name">Candidate Chat</div>
                <div class="feature-tile-desc">Memory-powered chatbot that remembers the full candidate conversation.</div>
                <span class="feature-tile-phase">Phase 3 · LangChain</span>
            </div>
            <div class="feature-tile">
                <div class="feature-tile-icon">🤖</div>
                <div class="feature-tile-name">Hiring Pipeline</div>
                <div class="feature-tile-desc">LangGraph state machine: screen → route → interview or reject autonomously.</div>
                <span class="feature-tile-phase">Phase 5–6 · Agents + LangGraph</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-card">
        <div class="section-card-title">Hiring Pipeline Flow</div>
        <div class="pipeline">
            <div class="pipe-node">
                <div class="pipe-dot done">📥</div>
                <div class="pipe-label">Input</div>
            </div>
            <div class="pipe-line done"></div>
            <div class="pipe-node">
                <div class="pipe-dot done">🔍</div>
                <div class="pipe-label">Screener</div>
            </div>
            <div class="pipe-line done"></div>
            <div class="pipe-node">
                <div class="pipe-dot done">🔀</div>
                <div class="pipe-label">Router</div>
            </div>
            <div class="pipe-line"></div>
            <div class="pipe-node">
                <div class="pipe-dot active">✅</div>
                <div class="pipe-label">Interviewer</div>
            </div>
            <div class="pipe-line"></div>
            <div class="pipe-node">
                <div class="pipe-dot">📧</div>
                <div class="pipe-label">Email</div>
            </div>
            <div class="pipe-line"></div>
            <div class="pipe-node">
                <div class="pipe-dot">📋</div>
                <div class="pipe-label">Decision</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# JD GENERATOR
# ══════════════════════════════════════════════════════════
elif "JD Generator" in page:
    st.markdown('<div class="page-title">Job Description Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Phase 1 · GenAI Foundations · Claude API</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-card-title">Configuration</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        job_title = st.text_input("Job Title", placeholder="e.g. Python Developer")
    with col2:
        company = st.text_input("Company Name", placeholder="e.g. SmartHire")
    with col3:
        experience = st.selectbox("Experience", ["0-1 years","1-2 years","2-3 years","3-5 years","5+ years"])

    tone = st.radio("Tone", ["Professional", "Friendly & Casual", "Startup Vibe"], horizontal=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("⚡ Generate Job Description"):
        if not job_title or not company:
            st.warning("Please fill in Job Title and Company Name.")
        else:
            with st.spinner("Generating with Claude..."):
                msg = client.messages.create(
                    model=MODEL, max_tokens=1024,
                    system=f"You are an expert HR professional. Use a {tone} tone. Write clear, inclusive job descriptions.",
                    messages=[{"role":"user","content":f"Write a JD for: {job_title} at {company}, {experience} experience. Include: role summary, 5 responsibilities, 5 required skills, 3 nice-to-have, 3 benefits."}]
                )
                jd = msg.content[0].text

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-card-title">Generated Job Description</div>', unsafe_allow_html=True)
            st.markdown(jd)
            st.markdown('</div>', unsafe_allow_html=True)
            st.download_button("⬇️ Download", jd, f"{job_title.replace(' ','_')}_JD.txt")


# ══════════════════════════════════════════════════════════
# RESUME SCREENER
# ══════════════════════════════════════════════════════════
elif "Resume Screener" in page:
    st.markdown('<div class="page-title">Resume Screener</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Phase 2 · Prompt Engineering · Structured JSON Output</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-card-title">Input</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        jd_text = st.text_area("Job Description", height=180, placeholder="Paste job description...")
    with col2:
        resume_text = st.text_area("Candidate Resume", height=180, placeholder="Paste resume...")
    technique = st.radio("Prompting Technique", ["Zero-shot","Few-shot","Chain-of-thought"], horizontal=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🔍 Screen Candidate"):
        if not jd_text or not resume_text:
            st.warning("Provide both JD and resume.")
        else:
            with st.spinner("Analysing..."):
                cot = technique == "Chain-of-thought"
                prompt = f"""{"Think step by step then end with " if cot else ""}Return ONLY valid JSON:
{{
  "candidate_name":"name",
  "overall_score":0-100,
  "recommendation":"Strong Yes/Yes/Maybe/No",
  "skills_match":{{"matched":[],"missing":[]}},
  "experience_match":true,
  "summary":"2 sentences",
  "red_flags":[]
}}

JD: {jd_text}
RESUME: {resume_text}"""
                msg = client.messages.create(
                    model=MODEL, max_tokens=1024,
                    system="You are an expert technical recruiter. Return only valid JSON, no markdown.",
                    messages=[{"role":"user","content":prompt}]
                )
                raw = msg.content[0].text

            try:
                m = re.search(r'\{.*\}', raw, re.DOTALL)
                result = json.loads(m.group()) if m else {}
                score = result.get("overall_score", 0)
                pct = score / 100

                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-card-title">Screening Results</div>', unsafe_allow_html=True)

                col1, col2, col3 = st.columns([1,1,2])
                css = "score-high-bg" if score>=70 else "score-mid-bg" if score>=50 else "score-low-bg"
                color = "#22c55e" if score>=70 else "#f59e0b" if score>=50 else "#ef4444"
                with col1:
                    st.markdown(f"""
                    <div class="score-ring-wrap">
                        <div class="score-ring {css}" style="--pct:{pct*360}deg;">
                            <div class="score-inner">
                                <div class="score-num" style="color:{color}">{score}</div>
                                <div class="score-denom">/100</div>
                            </div>
                        </div>
                        <div style="font-size:12px;color:#64748b;">Overall Score</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    rec = result.get("recommendation","N/A")
                    exp = result.get("experience_match", False)
                    badge = "badge-proceed" if "Yes" in rec or "Strong" in rec else "badge-reject"
                    st.markdown(f"""
                    <div style="padding:20px 0;">
                        <div style="font-size:11px;color:#64748b;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.6px;">Recommendation</div>
                        <div class="{badge}" style="margin-bottom:14px;">{rec}</div>
                        <div style="font-size:11px;color:#64748b;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.6px;">Experience</div>
                        <div style="font-size:14px;color:{'#4ade80' if exp else '#f87171'}">{'✅ Match' if exp else '❌ Below requirement'}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    matched = result.get("skills_match",{}).get("matched",[])
                    missing = result.get("skills_match",{}).get("missing",[])
                    matched_html = "".join(f'<span class="pill-green">{s}</span>' for s in matched)
                    missing_html = "".join(f'<span class="pill-red">{s}</span>' for s in missing)
                    st.markdown(f"""
                    <div style="padding:10px 0;">
                        <div style="font-size:11px;color:#64748b;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.6px;">Matched Skills</div>
                        <div style="margin-bottom:14px;">{matched_html or '<span style="color:#475569;font-size:12px;">None</span>'}</div>
                        <div style="font-size:11px;color:#64748b;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.6px;">Missing Skills</div>
                        <div>{missing_html or '<span style="color:#475569;font-size:12px;">None</span>'}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style="margin-top:16px;padding:14px 16px;background:#0a0f1a;border-radius:8px;border:1px solid #1e2d47;">
                    <div style="font-size:11px;color:#64748b;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.6px;">Summary</div>
                    <div style="font-size:13px;color:#cbd5e1;line-height:1.6;">{result.get('summary','')}</div>
                </div>
                """, unsafe_allow_html=True)

                flags = result.get("red_flags",[])
                if flags:
                    flags_html = "".join(f'<div style="font-size:12px;color:#fca5a5;padding:4px 0;">⚠ {f}</div>' for f in flags)
                    st.markdown(f"""
                    <div style="margin-top:12px;padding:14px 16px;background:#1c0a0a;border-radius:8px;border:1px solid #7f1d1d;">
                        <div style="font-size:11px;color:#64748b;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.6px;">Red Flags</div>
                        {flags_html}
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception:
                st.markdown(raw)


# ══════════════════════════════════════════════════════════
# CANDIDATE CHAT — split panel
# ══════════════════════════════════════════════════════════
elif "Candidate Chat" in page:
    st.markdown('<div class="page-title">Candidate Q&A Chat</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Phase 3 · LangChain · Conversation Memory — live chat panel on the right</div>', unsafe_allow_html=True)

    JOB_CONTEXT = """Company: SmartHire Technologies | Role: Python Developer
Experience: 2+ years | Location: Hyderabad (Hybrid) | Salary: ₹8-15 LPA
Required: Python, FastAPI, PostgreSQL, Git | Nice to have: Docker, AWS, LangChain
Benefits: Health insurance, 15 days leave, L&D budget, flexible hours"""

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ── SPLIT LAYOUT ─────────────────────────────────────
    left, right = st.columns([2, 3], gap="large")

    # LEFT — job info panel
    with left:
        st.markdown("""
        <div class="section-card" style="height:100%;">
            <div class="section-card-title">Open Position</div>
            <div style="margin-bottom:20px;">
                <div style="font-size:20px;font-weight:700;color:#f1f5f9;letter-spacing:-0.5px;">Python Developer</div>
                <div style="font-size:13px;color:#3b82f6;margin-top:2px;">SmartHire Technologies</div>
            </div>
            <div style="display:flex;flex-direction:column;gap:14px;">
                <div style="padding:12px 14px;background:#0a0f1a;border-radius:8px;border:1px solid #1e2d47;">
                    <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.7px;margin-bottom:5px;">📍 Location</div>
                    <div style="font-size:13px;color:#cbd5e1;">Hyderabad, India · Hybrid</div>
                </div>
                <div style="padding:12px 14px;background:#0a0f1a;border-radius:8px;border:1px solid #1e2d47;">
                    <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.7px;margin-bottom:5px;">💰 Salary</div>
                    <div style="font-size:13px;color:#cbd5e1;">₹8 – 15 LPA · Based on exp.</div>
                </div>
                <div style="padding:12px 14px;background:#0a0f1a;border-radius:8px;border:1px solid #1e2d47;">
                    <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.7px;margin-bottom:6px;">🛠 Required Skills</div>
                    <div>
                        <span class="pill-blue">Python</span>
                        <span class="pill-blue">FastAPI</span>
                        <span class="pill-blue">PostgreSQL</span>
                        <span class="pill-blue">Git</span>
                    </div>
                </div>
                <div style="padding:12px 14px;background:#0a0f1a;border-radius:8px;border:1px solid #1e2d47;">
                    <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.7px;margin-bottom:6px;">⭐ Nice to Have</div>
                    <div>
                        <span class="pill-green">Docker</span>
                        <span class="pill-green">AWS</span>
                        <span class="pill-green">LangChain</span>
                    </div>
                </div>
                <div style="padding:12px 14px;background:#0a0f1a;border-radius:8px;border:1px solid #1e2d47;">
                    <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.7px;margin-bottom:5px;">🎁 Benefits</div>
                    <div style="font-size:12px;color:#94a3b8;line-height:2;">
                        ✓ Health insurance (family)<br>
                        ✓ 15 days paid leave<br>
                        ✓ L&D budget<br>
                        ✓ Flexible hours
                    </div>
                </div>
            </div>
            <div style="margin-top:16px;padding:10px 14px;background:#1e3a5f22;border-radius:8px;border:1px solid #1d4ed840;">
                <div style="font-size:11px;color:#60a5fa;">💡 Ask the chatbot anything about this role →</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # RIGHT — live chat panel
    with right:
        st.markdown("""
        <style>
        .chat-panel {
            background: #111827;
            border: 1px solid #1e2d47;
            border-radius: 14px;
            display: flex;
            flex-direction: column;
            height: 560px;
            overflow: hidden;
        }
        .chat-panel-header {
            padding: 14px 18px;
            border-bottom: 1px solid #1e2d47;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-shrink: 0;
        }
        .chat-panel-avatar {
            width: 32px; height: 32px;
            background: linear-gradient(135deg, #1d4ed8, #3b82f6);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 15px;
        }
        .chat-panel-name { font-size: 13px; font-weight: 600; color: #f1f5f9; }
        .chat-panel-status { font-size: 11px; color: #22c55e; }
        .chat-panel-dot {
            width: 7px; height: 7px;
            background: #22c55e;
            border-radius: 50%;
            display: inline-block;
            margin-right: 4px;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            scrollbar-width: thin;
            scrollbar-color: #1e2d47 transparent;
        }
        .bubble-bot {
            display: flex; gap: 8px; align-items: flex-start; max-width: 88%;
        }
        .bubble-bot-icon {
            width: 26px; height: 26px;
            background: #1e2d47; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 12px; flex-shrink: 0; margin-top: 2px;
        }
        .bubble-bot-text {
            background: #1a2438;
            border: 1px solid #1e2d47;
            border-radius: 4px 12px 12px 12px;
            padding: 10px 14px;
            font-size: 13px; color: #cbd5e1; line-height: 1.6;
        }
        .bubble-user {
            display: flex; justify-content: flex-end;
        }
        .bubble-user-text {
            background: #1d4ed8;
            border-radius: 12px 12px 4px 12px;
            padding: 10px 14px;
            font-size: 13px; color: #fff; line-height: 1.6;
            max-width: 80%;
        }
        .chat-timestamp {
            font-size: 10px; color: #475569;
            text-align: center; margin: 4px 0;
        }
        </style>
        """, unsafe_allow_html=True)

        # Build message HTML
        msgs_html = ""
        if not st.session_state.messages:
            msgs_html = """
            <div class="bubble-bot">
                <div class="bubble-bot-icon">🤖</div>
                <div class="bubble-bot-text">
                    👋 Hi! I'm SmartHire's AI assistant.<br>
                    I can answer any questions about the <strong>Python Developer</strong> role.<br><br>
                    What's your name and what would you like to know?
                </div>
            </div>"""
        else:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    msgs_html += f'<div class="bubble-user"><div class="bubble-user-text">{msg["content"]}</div></div>'
                else:
                    msgs_html += f'<div class="bubble-bot"><div class="bubble-bot-icon">🤖</div><div class="bubble-bot-text">{msg["content"]}</div></div>'

        mem_count = len(st.session_state.messages)

        st.markdown(f"""
        <div class="chat-panel">
            <div class="chat-panel-header">
                <div class="chat-panel-avatar">🤖</div>
                <div>
                    <div class="chat-panel-name">SmartHire Assistant</div>
                    <div class="chat-panel-status"><span class="chat-panel-dot"></span>Online · {mem_count} messages stored</div>
                </div>
            </div>
            <div class="chat-messages" id="chatbox">
                {msgs_html}
            </div>
        </div>
        <script>
            const cb = document.getElementById('chatbox');
            if(cb) cb.scrollTop = cb.scrollHeight;
        </script>
        """, unsafe_allow_html=True)

        # Suggested questions
        st.markdown('<div style="margin-top:8px;margin-bottom:6px;font-size:11px;color:#475569;">Quick questions:</div>', unsafe_allow_html=True)
        q_cols = st.columns(3)
        suggestions = ["What's the salary?", "Is remote ok?", "What stack do you use?"]
        clicked_suggestion = None
        for i, (col, q) in enumerate(zip(q_cols, suggestions)):
            with col:
                if st.button(q, key=f"sq_{i}", use_container_width=True):
                    clicked_suggestion = q

        # Input row
        inp_col, btn_col = st.columns([5, 1])
        with inp_col:
            user_input = st.text_input("", placeholder="Type your message...", label_visibility="collapsed", key="chat_input")
        with btn_col:
            send = st.button("Send", type="primary")

        clear_col, _ = st.columns([1, 4])
        with clear_col:
            if st.button("🗑 Clear chat"):
                st.session_state.messages = []
                st.rerun()

        # Handle send
        final_input = clicked_suggestion or (user_input if send and user_input else None)
        if final_input:
            st.session_state.messages.append({"role": "user", "content": final_input})
            history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            with st.spinner(""):
                resp = client.messages.create(
                    model=MODEL, max_tokens=512,
                    system=f"You are a friendly, concise HR assistant for SmartHire Technologies. Job details: {JOB_CONTEXT}. Keep replies under 4 sentences. Be warm and helpful.",
                    messages=history
                )
                reply = resp.content[0].text
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()


# ══════════════════════════════════════════════════════════
# HIRING PIPELINE
# ══════════════════════════════════════════════════════════
elif "Hiring Pipeline" in page:
    st.markdown('<div class="page-title">Autonomous Hiring Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Phase 5–6 · Agentic AI · LangGraph State Machine</div>', unsafe_allow_html=True)

    CANDIDATES_DB = {
        "Rahul Sharma":   {"experience":3,"skills":["Python","FastAPI","PostgreSQL","Docker","Git"],"location":"Hyderabad","salary_expectation":12,"email":"rahul.sharma@email.com"},
        "Priya Patel":    {"experience":4,"skills":["Python","Django","MySQL","AWS","Docker"],"location":"Bangalore","salary_expectation":18,"email":"priya.patel@email.com"},
        "Arjun Reddy":    {"experience":1,"skills":["Python","Flask","SQLite","Git"],"location":"Hyderabad","salary_expectation":6,"email":"arjun.reddy@email.com"},
        "Sneha Krishnan": {"experience":5,"skills":["Python","FastAPI","LangChain","PostgreSQL","Redis"],"location":"Chennai","salary_expectation":25,"email":"sneha.krishnan@email.com"},
    }
    JOB_REQ = {"required_skills":["Python","FastAPI","PostgreSQL","Git"],"nice_to_have":["Docker","AWS","LangChain"],"min_experience":2,"budget_lpa":20}

    col1, col2 = st.columns([2,3])
    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-card-title">Select Candidate</div>', unsafe_allow_html=True)
        candidate_name = st.selectbox("", list(CANDIDATES_DB.keys()), label_visibility="collapsed")
        c = CANDIDATES_DB[candidate_name]
        skills_html = "".join(f'<span class="pill-blue">{s}</span>' for s in c["skills"])
        st.markdown(f"""
        <div style="margin-top:12px;">
            <div style="font-size:12px;color:#64748b;margin-bottom:4px;">Experience</div>
            <div style="font-size:16px;font-weight:600;color:#f1f5f9;margin-bottom:12px;">{c['experience']} years</div>
            <div style="font-size:12px;color:#64748b;margin-bottom:6px;">Skills</div>
            <div style="margin-bottom:12px;">{skills_html}</div>
            <div style="font-size:12px;color:#64748b;margin-bottom:4px;">Location · Salary</div>
            <div style="font-size:13px;color:#cbd5e1;">{c['location']} · ₹{c['salary_expectation']} LPA</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        run = st.button("⚡ Run Pipeline", use_container_width=True)

    with col2:
        if run:
            progress_bar = st.progress(0)
            status_box = st.empty()

            # Node 1: Screener
            status_box.info("🔍 Node 1 — Screener")
            progress_bar.progress(20)
            score = 0; breakdown = []
            if c["experience"] >= JOB_REQ["min_experience"]:
                s = min(30, c["experience"]*8); score += s
                breakdown.append(f"Experience: {c['experience']} yrs +{s}pts")
            matched = [x for x in JOB_REQ["required_skills"] if x in c["skills"]]
            missing  = [x for x in JOB_REQ["required_skills"] if x not in c["skills"]]
            ss = int(len(matched)/len(JOB_REQ["required_skills"])*40); score += ss
            breakdown.append(f"Skills matched: {len(matched)}/{len(JOB_REQ['required_skills'])} +{ss}pts")
            bonus = [x for x in JOB_REQ["nice_to_have"] if x in c["skills"]]
            bs = min(15, len(bonus)*5); score += bs
            if bonus: breakdown.append(f"Bonus skills: {bonus} +{bs}pts")
            if c["salary_expectation"] <= JOB_REQ["budget_lpa"]: score += 15; breakdown.append("Salary fit +15pts")
            progress_bar.progress(45)

            # Node 2: Router
            status_box.info("🔀 Node 2 — Router deciding path...")
            path = "interviewer" if score >= 55 else "rejector"
            progress_bar.progress(65)

            # Node 3
            status_box.info(f"{'✅ Node 3A — Interviewer' if path=='interviewer' else '❌ Node 3B — Rejector'}")
            with st.spinner("Claude drafting email..."):
                if path == "interviewer":
                    ep = f"Write a warm professional interview invitation for {candidate_name} ({c['experience']} yrs, skills: {', '.join(c['skills'][:3])}). Role: Python Developer at SmartHire. Slot: Monday 10 AM IST. Format: TO / SUBJECT / body."
                else:
                    ep = f"Write a kind constructive rejection for {candidate_name}. Score: {score}/100. Missing: {missing}. Encourage upskilling and future applications. Format: TO / SUBJECT / body."
                er = client.messages.create(model=MODEL, max_tokens=512,
                    system="You are a professional HR at SmartHire Technologies.",
                    messages=[{"role":"user","content":ep}])
                email = er.content[0].text
            progress_bar.progress(100)
            status_box.success("✅ Pipeline complete!")

            # Results
            st.markdown('<div class="section-card" style="margin-top:16px;">', unsafe_allow_html=True)
            st.markdown('<div class="section-card-title">Pipeline Results</div>', unsafe_allow_html=True)

            # Pipeline steps
            done_steps = 3 if path == "interviewer" else 3
            st.markdown(f"""
            <div class="pipeline" style="margin-bottom:20px;">
                <div class="pipe-node"><div class="pipe-dot done">📥</div><div class="pipe-label">Input</div></div>
                <div class="pipe-line done"></div>
                <div class="pipe-node"><div class="pipe-dot done">🔍</div><div class="pipe-label">Screener</div></div>
                <div class="pipe-line done"></div>
                <div class="pipe-node"><div class="pipe-dot done">🔀</div><div class="pipe-label">Router</div></div>
                <div class="pipe-line done"></div>
                <div class="pipe-node"><div class="pipe-dot done">{'✅' if path=='interviewer' else '❌'}</div><div class="pipe-label">{'Interviewer' if path=='interviewer' else 'Rejector'}</div></div>
                <div class="pipe-line done"></div>
                <div class="pipe-node"><div class="pipe-dot done">📧</div><div class="pipe-label">Email</div></div>
            </div>
            """, unsafe_allow_html=True)

            r1, r2, r3 = st.columns(3)
            pct = score/100
            css = "score-high-bg" if score>=70 else "score-mid-bg" if score>=50 else "score-low-bg"
            color = "#22c55e" if score>=70 else "#f59e0b" if score>=50 else "#ef4444"
            with r1:
                st.markdown(f"""<div class="score-ring-wrap">
                    <div class="score-ring {css}" style="--pct:{pct*360}deg;">
                        <div class="score-inner">
                            <div class="score-num" style="color:{color}">{score}</div>
                            <div class="score-denom">/100</div>
                        </div>
                    </div>
                    <div style="font-size:11px;color:#64748b;">Score</div>
                </div>""", unsafe_allow_html=True)
            with r2:
                badge = "badge-proceed" if path=="interviewer" else "badge-reject"
                label = "PROCEED TO INTERVIEW" if path=="interviewer" else "NOT SELECTED"
                st.markdown(f"""<div style="padding:20px 0;">
                    <div style="font-size:11px;color:#64748b;margin-bottom:8px;text-transform:uppercase;letter-spacing:.6px;">Decision</div>
                    <div class="{badge}">{label}</div>
                </div>""", unsafe_allow_html=True)
            with r3:
                bd_html = "".join(f'<div style="font-size:11px;color:#94a3b8;padding:2px 0;">· {b}</div>' for b in breakdown)
                st.markdown(f"""<div style="padding:10px 0;">
                    <div style="font-size:11px;color:#64748b;margin-bottom:8px;text-transform:uppercase;letter-spacing:.6px;">Breakdown</div>
                    {bd_html}
                </div>""", unsafe_allow_html=True)

            st.markdown(f'<div style="margin-top:16px;"><div class="section-card-title">Drafted Email</div><div class="email-block">{email}</div></div>', unsafe_allow_html=True)
            st.download_button("⬇️ Download Email", email, f"{candidate_name.replace(' ','_')}_email.txt")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="height:300px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:12px;color:#475569;">
                <div style="font-size:40px;">⚡</div>
                <div style="font-size:14px;">Select a candidate and run the pipeline</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# SIDEBAR CHAT — persistent on every page
# ══════════════════════════════════════════════════════════

JOB_CONTEXT_BUBBLE = """Python Developer at SmartHire Technologies.
2+ years exp. Hyderabad hybrid. ₹8-15 LPA.
Required: Python, FastAPI, PostgreSQL, Git.
Nice to have: Docker, AWS, LangChain.
Benefits: health insurance, 15 days leave, L&D budget, flexible hours."""

if "bubble_messages" not in st.session_state:
    st.session_state.bubble_messages = []

with st.sidebar:
    st.markdown("""
    <style>@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}</style>
    <div style='margin-top:28px;border-top:1px solid #1e2d47;padding-top:18px;margin-bottom:14px;'>
        <div style='display:flex;align-items:center;gap:10px;'>
            <div style='width:10px;height:10px;background:#22c55e;border-radius:50%;
                        flex-shrink:0;animation:pulse 2s infinite;'></div>
            <div style='font-size:14px;font-weight:600;color:#f1f5f9;'>AI Assistant</div>
            <div style='font-size:11px;color:#22c55e;margin-left:auto;'>● Online</div>
        </div>
        <div style='font-size:11px;color:#475569;margin-top:4px;padding-left:20px;'>
            Ask anything about the role
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show last 4 messages — bigger text, more padding
    if not st.session_state.bubble_messages:
        st.markdown("""
        <div style='background:#1a2438;border:1px solid #1e2d47;
                    border-radius:4px 12px 12px 12px;
                    padding:12px 14px;margin:0 0 12px 0;
                    font-size:13px;color:#cbd5e1;line-height:1.7;'>
            🤖 Hi! Ask me anything about the <strong style="color:#60a5fa;">Python Developer</strong> role.
        </div>""", unsafe_allow_html=True)
    else:
        for msg in st.session_state.bubble_messages[-4:]:
            if msg["role"] == "user":
                st.markdown(f"""
                <div style='background:#1d4ed8;border-radius:12px 12px 4px 12px;
                            padding:12px 14px;margin:8px 0;
                            font-size:13px;color:white;
                            line-height:1.6;text-align:right;'>
                    {msg["content"]}
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background:#1a2438;border:1px solid #1e2d47;
                            border-radius:4px 12px 12px 12px;
                            padding:12px 14px;margin:8px 0;
                            font-size:13px;color:#cbd5e1;line-height:1.7;'>
                    🤖 {msg["content"]}
                </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    bubble_input = st.text_input("",
        placeholder="Type your question...",
        label_visibility="collapsed",
        key="bubble_input"
    )

    col_send, col_clear = st.columns([4, 1])
    with col_send:
        send_bubble = st.button("💬 Ask", use_container_width=True, key="bubble_send")
    with col_clear:
        if st.button("🗑", use_container_width=True, key="bubble_clear"):
            st.session_state.bubble_messages = []
            st.rerun()

    if send_bubble and bubble_input.strip():
        st.session_state.bubble_messages.append({
            "role": "user", "content": bubble_input.strip()
        })
        history = [{"role": m["role"], "content": m["content"]}
                   for m in st.session_state.bubble_messages]
        with st.spinner(""):
            resp = client.messages.create(
                model=MODEL,
                max_tokens=200,
                system=f"You are a concise friendly HR assistant for SmartHire. Job: {JOB_CONTEXT_BUBBLE} Keep replies under 2 sentences.",
                messages=history
            )
        st.session_state.bubble_messages.append({
            "role": "assistant", "content": resp.content[0].text
        })
        st.rerun()