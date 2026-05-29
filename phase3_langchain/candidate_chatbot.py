import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

load_dotenv()

# ── WHY LANGCHAIN? ────────────────────────────────────────
# Raw Anthropic SDK is great for single calls.
# LangChain adds:
# 1. Memory   — remember conversation history automatically
# 2. Chains   — connect multiple AI steps together
# 3. Tools    — let AI use search, calculators, databases
# 4. Agents   — AI that decides what to do next
# We'll use all of these across phases 3-6.

# ── SETUP THE LLM ────────────────────────────────────────
llm = ChatAnthropic(
    model=os.getenv("CLAUDE_MODEL"),
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_tokens=1024
)

# ── JOB CONTEXT ──────────────────────────────────────────
# This is the job the candidate is asking about
JOB_CONTEXT = """
Company: SmartHire Technologies
Role: Python Developer
Experience: 2+ years
Location: Hyderabad, India (Hybrid)
Salary: ₹8-15 LPA based on experience

Required Skills: Python, FastAPI, PostgreSQL, Git, REST APIs
Nice to Have: Docker, AWS, LangChain

Responsibilities:
- Build and maintain backend APIs
- Work with cross-functional teams
- Code reviews and best practices

Benefits:
- Health insurance for family
- 15 days paid leave
- Learning & development budget
- Flexible work hours
"""

# ── SYSTEM PROMPT ─────────────────────────────────────────
SYSTEM_PROMPT = f"""You are a friendly and professional HR assistant 
for SmartHire Technologies. You help candidates understand the job 
opening and answer their questions honestly.

Here is the job details you should refer to:
{JOB_CONTEXT}

Guidelines:
- Be warm, encouraging, and professional
- Answer only based on the job details provided
- If you don't know something, say "I'll check with the hiring team"
- Ask candidates about their background to assess fit
- Never make up salary or benefit details not listed above
"""

# ── MEMORY STORE ─────────────────────────────────────────
# This dictionary stores conversation history per session
# In a real app, this would be a database
store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """Returns existing conversation or creates new one"""
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# ── BUILD THE CHAIN WITH MEMORY ───────────────────────────
# This is the core LangChain concept:
# llm = the AI model
# RunnableWithMessageHistory = wraps it with memory capability

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),  # ← memory goes here
    ("human", "{input}")                            # ← current message
])

# Chain = prompt → llm (pipe operator connects them)
chain = prompt | llm

# Wrap chain with memory
chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# ── CHAT FUNCTION ─────────────────────────────────────────
def chat(user_message: str, session_id: str = "candidate_001") -> str:
    """
    Send a message and get a response.
    Memory is automatic — previous messages are included.
    """
    response = chain_with_memory.invoke(
        {"input": user_message},
        config={"configurable": {"session_id": session_id}}
    )
    return response.content

# ── SHOW MEMORY ───────────────────────────────────────────
def show_conversation_history(session_id: str = "candidate_001"):
    """Show what the bot remembers about this conversation"""
    if session_id in store:
        messages = store[session_id].messages
        print(f"\n📝 Conversation Memory ({len(messages)} messages stored):")
        for msg in messages:
            role = "You" if isinstance(msg, HumanMessage) else "Bot"
            print(f"  {role}: {msg.content[:80]}...")
    else:
        print("No conversation history yet.")

# ── MAIN CHAT LOOP ────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("SmartHire - Candidate Q&A Chatbot (LangChain + Memory)")
    print("=" * 60)
    print("Type 'quit' to exit | Type 'memory' to see what bot remembers")
    print("-" * 60)

    session_id = "candidate_001"

    # Starter message from bot
    welcome = chat(
        "Greet the candidate warmly and ask their name and what role they're interested in.",
        session_id
    )
    print(f"\n🤖 Bot: {welcome}\n")

    # Chat loop
    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == 'quit':
            print("\n🤖 Bot: Thank you for your interest in SmartHire! We'll be in touch. 👋")
            break

        if user_input.lower() == 'memory':
            show_conversation_history(session_id)
            continue

        response = chat(user_input, session_id)
        print(f"\n🤖 Bot: {response}\n")