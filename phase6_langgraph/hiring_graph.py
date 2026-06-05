import os
import json
from typing import TypedDict, Literal
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

load_dotenv()

# ── WHAT IS LANGGRAPH? ────────────────────────────────────
# LangGraph models your AI workflow as a graph:
#
# NODES = steps (each node is a function that does something)
# EDGES = connections between steps
# STATE = data that flows through the entire graph
#
# Why better than Phase 5 agent?
# ✅ You control the flow — no surprises
# ✅ Each node is testable independently  
# ✅ Conditional routing — different paths for different cases
# ✅ Easy to debug — you can see exactly where it is
# ✅ Multi-agent — each node can be a different specialist AI

# ── STATE DEFINITION ──────────────────────────────────────
# State is the "memory" of your graph.
# Every node can READ and WRITE to the state.
# This is how nodes communicate with each other.

class HiringState(TypedDict):
    # Input
    candidate_name: str
    
    # Filled by Screener Node
    candidate_profile: dict
    score: int
    score_breakdown: list
    
    # Filled by Router
    routing_decision: str  # "interview" or "reject"
    
    # Filled by Interviewer or Rejector Node
    email_draft: str
    final_decision: str
    final_reasoning: str
    
    # Track which nodes ran (for debugging)
    nodes_visited: list


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
        "skills": ["Python", "Django", "MySQL", "AWS", "Docker", "Kubernetes"],
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
        "skills": ["Python", "FastAPI", "LangChain", "OpenAI", "PostgreSQL", "Redis"],
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

# ── LLM SETUP ─────────────────────────────────────────────
llm = ChatAnthropic(
    model=os.getenv("CLAUDE_MODEL"),
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_tokens=2048
)


# ══════════════════════════════════════════════════════════
# NODE 1: SCREENER
# Fetches candidate profile and scores them
# ══════════════════════════════════════════════════════════

def screener_node(state: HiringState) -> HiringState:
    """
    Node 1: Fetch candidate profile and calculate score.
    This node READS: candidate_name
    This node WRITES: candidate_profile, score, score_breakdown
    """
    print("\n" + "="*60)
    print("🔍 NODE 1: SCREENER running...")
    print("="*60)
    
    name = state["candidate_name"].lower().strip()
    
    # Fetch from database
    if name not in CANDIDATES_DB:
        return {
            **state,
            "candidate_profile": {},
            "score": 0,
            "score_breakdown": [f"❌ Candidate '{name}' not found"],
            "nodes_visited": state.get("nodes_visited", []) + ["screener"]
        }
    
    candidate = CANDIDATES_DB[name]
    
    # Calculate score
    score = 0
    breakdown = []
    
    # Experience (30 pts)
    if candidate["experience"] >= JOB_REQUIREMENTS["min_experience"]:
        exp_score = min(30, candidate["experience"] * 8)
        score += exp_score
        breakdown.append(f"✅ Experience: {candidate['experience']} yrs (+{exp_score}pts)")
    else:
        breakdown.append(f"❌ Experience: only {candidate['experience']} yr(s)")

    # Required skills (40 pts)
    matched = [s for s in JOB_REQUIREMENTS["required_skills"]
               if s in candidate["skills"]]
    missing = [s for s in JOB_REQUIREMENTS["required_skills"]
               if s not in candidate["skills"]]
    skill_score = int((len(matched) / len(JOB_REQUIREMENTS["required_skills"])) * 40)
    score += skill_score
    breakdown.append(f"✅ Skills matched: {matched} (+{skill_score}pts)")
    if missing:
        breakdown.append(f"❌ Missing: {missing}")

    # Bonus skills (15 pts)
    bonus = [s for s in JOB_REQUIREMENTS["nice_to_have"]
             if s in candidate["skills"]]
    bonus_score = min(15, len(bonus) * 5)
    score += bonus_score
    if bonus:
        breakdown.append(f"⭐ Bonus skills: {bonus} (+{bonus_score}pts)")

    # Budget (15 pts)
    if candidate["salary_expectation"] <= JOB_REQUIREMENTS["budget_lpa"]:
        score += 15
        breakdown.append(f"✅ Salary: ₹{candidate['salary_expectation']}LPA fits budget (+15pts)")
    else:
        breakdown.append(f"❌ Salary: ₹{candidate['salary_expectation']}LPA over budget")

    print(f"   Candidate: {candidate['name']}")
    print(f"   Score: {score}/100")
    for b in breakdown:
        print(f"   {b}")

    return {
        **state,
        "candidate_profile": candidate,
        "score": score,
        "score_breakdown": breakdown,
        "nodes_visited": state.get("nodes_visited", []) + ["screener"]
    }


# ══════════════════════════════════════════════════════════
# NODE 2: ROUTER (Conditional Edge)
# Decides which path to take based on score
# ══════════════════════════════════════════════════════════

def router_node(state: HiringState) -> Literal["interviewer", "rejector"]:
    """
    This is a CONDITIONAL EDGE — not a regular node.
    It returns a string that tells LangGraph which node to go to next.
    
    This is the KEY LangGraph concept:
    Based on data in state → choose different paths
    """
    score = state["score"]
    print(f"\n{'='*60}")
    print(f"🔀 ROUTER: Score is {score}/100")
    
    if score >= 55:
        print(f"   → Routing to INTERVIEWER (score >= 55)")
        return "interviewer"
    else:
        print(f"   → Routing to REJECTOR (score < 55)")
        return "rejector"


# ══════════════════════════════════════════════════════════
# NODE 3A: INTERVIEWER
# For qualified candidates — drafts invite email
# ══════════════════════════════════════════════════════════

def interviewer_node(state: HiringState) -> HiringState:
    """
    Node 3A: Handle qualified candidates.
    Uses Claude to draft a personalized interview invitation.
    This node READS: candidate_profile, score, score_breakdown
    This node WRITES: email_draft, final_decision, final_reasoning
    """
    print(f"\n{'='*60}")
    print("✅ NODE 3A: INTERVIEWER running...")
    print("="*60)
    
    candidate = state["candidate_profile"]
    score = state["score"]
    
    # Use Claude to write personalized email
    response = llm.invoke([
        SystemMessage(content="You are a friendly HR professional at SmartHire Technologies."),
        HumanMessage(content=f"""Write a warm, personalized interview invitation email for:

Candidate: {candidate['name']}
Email: {candidate['email']}
Experience: {candidate['experience']} years
Skills: {', '.join(candidate['skills'])}
Score: {score}/100

Job: Python Developer at SmartHire Technologies
Interview slot: Next Monday 10:00 AM IST (Video call)

Make it personal — reference their specific skills.
Format: TO, SUBJECT, then email body.""")
    ])
    
    email = response.content
    print(f"   ✉️  Email drafted for {candidate['name']}")
    print(f"   Preview: {email[:100]}...")
    
    return {
        **state,
        "email_draft": email,
        "final_decision": "PROCEED TO INTERVIEW",
        "final_reasoning": f"Score {score}/100 — meets threshold. Strong skill match.",
        "nodes_visited": state.get("nodes_visited", []) + ["interviewer"]
    }


# ══════════════════════════════════════════════════════════
# NODE 3B: REJECTOR  
# For unqualified candidates — drafts kind rejection
# ══════════════════════════════════════════════════════════

def rejector_node(state: HiringState) -> HiringState:
    """
    Node 3B: Handle unqualified candidates.
    Drafts a kind, constructive rejection email.
    This node READS: candidate_profile, score, score_breakdown
    This node WRITES: email_draft, final_decision, final_reasoning
    """
    print(f"\n{'='*60}")
    print("❌ NODE 3B: REJECTOR running...")
    print("="*60)
    
    candidate = state["candidate_profile"]
    score = state["score"]
    missing = [b for b in state["score_breakdown"] if "Missing" in b]
    
    # Use Claude to write kind rejection
    response = llm.invoke([
        SystemMessage(content="You are a kind, empathetic HR professional at SmartHire."),
        HumanMessage(content=f"""Write a kind rejection email for:

Candidate: {candidate['name']}
Email: {candidate['email']}
Score: {score}/100
Gaps: {missing}

Guidelines:
- Be warm and encouraging, not harsh
- Thank them for their time
- Mention 1-2 specific gaps constructively  
- Encourage them to apply again in future
- Keep it brief (5-6 sentences)

Format: TO, SUBJECT, then email body.""")
    ])
    
    email = response.content
    print(f"   ✉️  Rejection email drafted for {candidate['name']}")
    
    return {
        **state,
        "email_draft": email,
        "final_decision": "NOT SELECTED",
        "final_reasoning": f"Score {score}/100 — below 55 threshold.",
        "nodes_visited": state.get("nodes_visited", []) + ["rejector"]
    }


# ══════════════════════════════════════════════════════════
# BUILD THE GRAPH
# ══════════════════════════════════════════════════════════

def build_hiring_graph():
    """
    Assemble all nodes and edges into a LangGraph workflow.
    
    This is the core LangGraph API:
    1. Create graph with state type
    2. Add nodes (functions)
    3. Add edges (connections)
    4. Add conditional edges (routing)
    5. Set entry point
    6. Compile
    """
    
    # Create graph — tell it what state type to use
    graph = StateGraph(HiringState)
    
    # Add nodes — each node is a Python function
    graph.add_node("screener", screener_node)
    graph.add_node("interviewer", interviewer_node)
    graph.add_node("rejector", rejector_node)
    
    # Add edges — define the flow
    graph.set_entry_point("screener")  # always start here
    
    # Conditional edge — router decides next node
    graph.add_conditional_edges(
        "screener",      # from this node
        router_node,     # call this function to decide
        {
            "interviewer": "interviewer",   # if returns "interviewer" → go there
            "rejector": "rejector"          # if returns "rejector" → go there
        }
    )
    
    # Both paths end after their node
    graph.add_edge("interviewer", END)
    graph.add_edge("rejector", END)
    
    return graph.compile()


# ── FINAL REPORT ──────────────────────────────────────────

def print_final_report(result: HiringState):
    """Print a clean summary of the graph execution"""
    print("\n" + "="*60)
    print("📋 SMARTHIRE GRAPH — FINAL REPORT")
    print("="*60)
    
    candidate = result.get("candidate_profile", {})
    
    print(f"\n👤 Candidate:     {candidate.get('name', 'Unknown')}")
    print(f"📊 Score:         {result.get('score', 0)}/100")
    print(f"🎯 Decision:      {result.get('final_decision', 'N/A')}")
    print(f"🗺️  Path taken:    {' → '.join(result.get('nodes_visited', []))}")
    
    print(f"\n📧 EMAIL DRAFTED:")
    print("-"*60)
    print(result.get("email_draft", "No email generated"))
    
    print("\n" + "="*60)
    print(f"✅ Graph execution complete!")
    print(f"   Nodes visited: {result.get('nodes_visited', [])}")
    print("="*60)


# ── RUN THE GRAPH ─────────────────────────────────────────

if __name__ == "__main__":
    print("="*60)
    print("SmartHire — LangGraph Hiring Pipeline")
    print("="*60)
    print("Available: Rahul Sharma, Priya Patel,")
    print("           Arjun Reddy, Sneha Krishnan")
    print("="*60)
    
    # Build the graph
    hiring_graph = build_hiring_graph()
    
    candidate = input("\nEnter candidate name: ").strip()
    
    # Initial state — only candidate_name is set
    # All other fields get filled as graph runs
    initial_state = {
        "candidate_name": candidate,
        "candidate_profile": {},
        "score": 0,
        "score_breakdown": [],
        "routing_decision": "",
        "email_draft": "",
        "final_decision": "",
        "final_reasoning": "",
        "nodes_visited": []
    }
    
    print(f"\n🚀 Running LangGraph pipeline for: {candidate}")
    
    # Run the graph
    result = hiring_graph.invoke(initial_state)
    
    # Print report
    print_final_report(result)
    
    # Show the graph visually (text representation)
    print("\n🗺️  GRAPH STRUCTURE:")
    print("   START → screener → [router] → interviewer → END")
    print("                              └→ rejector    → END")