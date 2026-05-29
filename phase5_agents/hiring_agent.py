import os
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage


load_dotenv()

# ── WHAT IS AN AGENT? ─────────────────────────────────────
# A normal LLM call: Question → Answer (one shot)
#
# An Agent:
# Question → Think → "I need to use a tool" → Use Tool
#          → Think → "I need another tool"  → Use Tool
#          → Think → "I have enough info"   → Final Answer
#
# The agent DECIDES which tools to use and in what order.
# You don't hardcode the steps — the AI figures it out.
# This is called the ReAct pattern:
# Reason → Act → Observe → Reason → Act → ...

# ── CANDIDATE DATABASE ────────────────────────────────────
# Simulated database of candidates
CANDIDATES_DB = {
    "rahul sharma": {
        "name": "Rahul Sharma",
        "experience": 3,
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
        "location": "Hyderabad",
        "salary_expectation": 12,
        "email": "rahul.sharma@email.com",
        "phone": "+91-9876543210"
    },
    "priya patel": {
        "name": "Priya Patel", 
        "experience": 4,
        "skills": ["Python", "Django", "MySQL", "AWS", "Docker", "Kubernetes"],
        "location": "Bangalore",
        "salary_expectation": 18,
        "email": "priya.patel@email.com",
        "phone": "+91-9876543211"
    },
    "arjun reddy": {
        "name": "Arjun Reddy",
        "experience": 1,
        "skills": ["Python", "Flask", "SQLite", "Git"],
        "location": "Hyderabad", 
        "salary_expectation": 6,
        "email": "arjun.reddy@email.com",
        "phone": "+91-9876543212"
    },
    "sneha krishnan": {
        "name": "Sneha Krishnan",
        "experience": 5,
        "skills": ["Python", "FastAPI", "LangChain", "OpenAI", "PostgreSQL", "Redis", "Docker"],
        "location": "Chennai",
        "salary_expectation": 25,
        "email": "sneha.krishnan@email.com",
        "phone": "+91-9876543213"
    }
}

JOB_REQUIREMENTS = {
    "title": "Python Developer",
    "min_experience": 2,
    "required_skills": ["Python", "FastAPI", "PostgreSQL", "Git"],
    "nice_to_have": ["Docker", "AWS", "LangChain"],
    "budget_lpa": 20,
    "location": "Hyderabad"
}

# ── TOOLS ─────────────────────────────────────────────────
# Tools are functions the agent can CHOOSE to call.
# The @tool decorator tells LangChain this is a usable tool.
# The docstring tells the agent WHEN to use this tool.

@tool
def get_candidate_profile(candidate_name: str) -> str:
    """
    Retrieve a candidate's full profile from the database.
    Use this when you need to look up a candidate's skills,
    experience, location, or contact information.
    Input: candidate's full name (lowercase)
    """
    key = candidate_name.lower().strip()
    if key in CANDIDATES_DB:
        candidate = CANDIDATES_DB[key]
        return json.dumps(candidate, indent=2)
    return f"Candidate '{candidate_name}' not found in database."


@tool
def score_candidate(candidate_name: str) -> str:
    """
    Score a candidate against the current job requirements.
    Use this to evaluate how well a candidate fits the role.
    Returns a score out of 100 with detailed breakdown.
    Input: candidate's full name (lowercase)
    """
    key = candidate_name.lower().strip()
    if key not in CANDIDATES_DB:
        return f"Candidate '{candidate_name}' not found."
    
    candidate = CANDIDATES_DB[key]
    score = 0
    breakdown = []

    # Experience scoring (30 points)
    if candidate["experience"] >= JOB_REQUIREMENTS["min_experience"]:
        exp_score = min(30, candidate["experience"] * 8)
        score += exp_score
        breakdown.append(f"✅ Experience: {candidate['experience']} years (+{exp_score} points)")
    else:
        breakdown.append(f"❌ Experience: {candidate['experience']} years (below {JOB_REQUIREMENTS['min_experience']} required)")

    # Required skills scoring (40 points)
    matched = [s for s in JOB_REQUIREMENTS["required_skills"] 
               if s in candidate["skills"]]
    missing = [s for s in JOB_REQUIREMENTS["required_skills"] 
               if s not in candidate["skills"]]
    skill_score = int((len(matched) / len(JOB_REQUIREMENTS["required_skills"])) * 40)
    score += skill_score
    breakdown.append(f"✅ Required skills matched: {matched} (+{skill_score} points)")
    if missing:
        breakdown.append(f"❌ Missing skills: {missing}")

    # Nice to have skills (15 points)
    bonus_skills = [s for s in JOB_REQUIREMENTS["nice_to_have"] 
                    if s in candidate["skills"]]
    bonus_score = len(bonus_skills) * 5
    score += bonus_score
    if bonus_skills:
        breakdown.append(f"⭐ Bonus skills: {bonus_skills} (+{bonus_score} points)")

    # Budget fit (15 points)  
    if candidate["salary_expectation"] <= JOB_REQUIREMENTS["budget_lpa"]:
        score += 15
        breakdown.append(f"✅ Salary fit: ₹{candidate['salary_expectation']} LPA within budget (+15 points)")
    else:
        breakdown.append(f"❌ Salary: ₹{candidate['salary_expectation']} LPA exceeds budget")

    # Recommendation
    if score >= 75:
        recommendation = "STRONG YES — Schedule interview immediately"
    elif score >= 55:
        recommendation = "YES — Good candidate, worth interviewing"
    elif score >= 35:
        recommendation = "MAYBE — Has potential but gaps exist"
    else:
        recommendation = "NO — Does not meet core requirements"

    result = {
        "candidate": candidate["name"],
        "total_score": score,
        "recommendation": recommendation,
        "breakdown": breakdown
    }
    return json.dumps(result, indent=2)


@tool
def check_interview_slots() -> str:
    """
    Check available interview time slots for the next 7 days.
    Use this when you need to schedule or suggest interview times.
    Returns a list of available slots.
    """
    # Simulated calendar slots
    slots = []
    for i in range(1, 8):
        date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        # Randomly available slots (simulating a real calendar)
        if random.random() > 0.3:
            slots.append(f"{date} 10:00 AM IST")
        if random.random() > 0.5:
            slots.append(f"{date} 3:00 PM IST")
    
    return json.dumps({
        "available_slots": slots[:5],  # Return top 5 slots
        "timezone": "IST (India Standard Time)",
        "duration": "45 minutes",
        "format": "Video call (Google Meet)"
    }, indent=2)


@tool
def draft_outreach_email(candidate_name: str, interview_slot: str) -> str:
    """
    Draft a personalized outreach email to invite a candidate for interview.
    Use this after scoring the candidate and checking interview slots.
    Input: candidate_name and the selected interview_slot
    """
    key = candidate_name.lower().strip()
    if key not in CANDIDATES_DB:
        return f"Candidate '{candidate_name}' not found."
    
    candidate = CANDIDATES_DB[key]
    
    email = f"""
TO: {candidate['email']}
SUBJECT: Interview Invitation — Python Developer Role at SmartHire Technologies

Dear {candidate['name']},

I hope this message finds you well! My name is Sarah from the Talent 
Acquisition team at SmartHire Technologies.

After reviewing your profile, we are impressed with your {candidate['experience']} 
years of experience and your expertise in {', '.join(candidate['skills'][:3])}.

We would love to invite you for an interview for our Python Developer position.

📅 Proposed Time: {interview_slot}
📍 Format: Video Call (Google Meet — link will be shared separately)
⏱️ Duration: 45 minutes

The interview will cover:
- Technical discussion about your past projects
- Python and backend development concepts  
- System design (based on your experience level)
- Culture fit and team collaboration

Please reply to confirm this slot or suggest an alternative time that 
works better for you.

Looking forward to connecting!

Best regards,
Sarah Johnson
Talent Acquisition | SmartHire Technologies
sarah.johnson@smarthire.com | +91-80-12345678
"""
    return email


@tool  
def send_hiring_decision(candidate_name: str, decision: str, reason: str) -> str:
    """
    Record the final hiring decision for a candidate.
    Use this as the LAST step after all evaluation is complete.
    Input: candidate_name, decision (PROCEED/REJECT/HOLD), reason
    """
    key = candidate_name.lower().strip()
    if key not in CANDIDATES_DB:
        return f"Candidate not found."
    
    candidate = CANDIDATES_DB[key]
    
    record = {
        "candidate": candidate["name"],
        "email": candidate["email"],
        "decision": decision,
        "reason": reason,
        "decided_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "decided_by": "SmartHire AI Agent",
        "status": "✅ Decision recorded successfully"
    }
    return json.dumps(record, indent=2)


# ── BUILD THE AGENT ───────────────────────────────────────
llm = ChatAnthropic(
    model=os.getenv("CLAUDE_MODEL"),
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_tokens=4096
)

# Give the LLM access to all tools
tools = [
    get_candidate_profile,
    score_candidate,
    check_interview_slots,
    draft_outreach_email,
    send_hiring_decision
]

# Bind tools to the model
# This tells Claude: "you have these tools available"
llm_with_tools = llm.bind_tools(tools)

# ── AGENT LOOP ────────────────────────────────────────────
# This is the ReAct loop:
# Think → Act (use tool) → Observe result → Think → Act → ...

def run_agent(task: str, max_steps: int = 10) -> str:
    """
    Run the hiring agent on a task.
    The agent will autonomously decide which tools to use.
    """
    print(f"\n🤖 Agent starting task: {task}")
    print("=" * 60)
    
    messages = [
        HumanMessage(content=f"""You are SmartHire's autonomous hiring agent.
        
Your job requirements:
{json.dumps(JOB_REQUIREMENTS, indent=2)}

Your task: {task}

Use your tools systematically:
1. First get the candidate profile
2. Score them against requirements  
3. If score is good (>55), check interview slots
4. Draft an outreach email with a specific slot
5. Record the final hiring decision

Be thorough and explain your reasoning at each step.""")
    ]
    
    step = 0
    tool_map = {t.name: t for t in tools}
    
    while step < max_steps:
        step += 1
        print(f"\n🔄 Step {step}:")
        
        # Get agent's response
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        
        # Check if agent wants to use tools
        if not response.tool_calls:
            # No more tool calls — agent is done
            print(f"\n✅ Agent finished!")
            print("\n" + "=" * 60)
            print("📋 FINAL REPORT:")
            print("=" * 60)
            return response.content
        
        # Execute each tool the agent requested
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            print(f"   🔧 Using tool: {tool_name}")
            print(f"   📥 Input: {tool_args}")
            
            # Run the actual tool
            if tool_name in tool_map:
                tool_result = tool_map[tool_name].invoke(tool_args)
            else:
                tool_result = f"Tool {tool_name} not found"
            
            print(f"   📤 Result preview: {str(tool_result)[:100]}...")
            
            # Add tool result back to conversation
            from langchain_core.messages import ToolMessage
            messages.append(ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"]
            ))
    
    return "Agent reached maximum steps."


# ── RUN THE AGENT ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("SmartHire - Autonomous Hiring Agent")
    print("=" * 60)
    print("Available candidates: Rahul Sharma, Priya Patel,")
    print("                      Arjun Reddy, Sneha Krishnan")
    print("=" * 60)

    candidate = input("\nEnter candidate name to evaluate: ").strip()
    
    task = f"""Fully evaluate {candidate} for our Python Developer position.
    Complete the entire hiring workflow end-to-end."""
    
    result = run_agent(task)
    print(result)