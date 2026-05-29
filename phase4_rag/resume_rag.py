import os
import json
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

# ── WHAT IS RAG? ──────────────────────────────────────────
# Problem: You have 100 resumes. You can't put all in one prompt.
# Solution:
# 1. Convert all resumes to embeddings (numbers that capture meaning)
# 2. Store in ChromaDB (vector database)
# 3. When question comes in → find most similar resumes
# 4. Send only those to Claude → get accurate answer
#
# Embeddings explained:
# "Python developer" and "backend engineer who codes in Python"
# are different strings but VERY similar in meaning.
# Embeddings capture this semantic similarity as numbers.

# ── SAMPLE RESUME DATABASE ────────────────────────────────
# In real app these would be uploaded PDFs
# For learning we use text directly

RESUMES = [
    {
        "id": "001",
        "name": "Rahul Sharma",
        "content": """
        Name: Rahul Sharma | Experience: 3 years
        Skills: Python, FastAPI, PostgreSQL, Docker, Git, REST APIs
        Work: Backend Developer at TechCorp - built REST APIs with FastAPI
        Education: B.Tech Computer Science, KL University
        Location: Hyderabad | Salary expectation: 12 LPA
        Achievements: Reduced API response time by 40%, led team of 3
        """
    },
    {
        "id": "002", 
        "name": "Priya Patel",
        "content": """
        Name: Priya Patel | Experience: 4 years
        Skills: Python, Django, MySQL, AWS, Docker, Kubernetes, CI/CD
        Work: Full Stack Developer at StartupABC - Django apps, AWS deployment
        Education: M.Tech Software Engineering, BITS Pilani
        Location: Bangalore | Salary expectation: 18 LPA
        Achievements: Built microservices architecture, AWS certified
        """
    },
    {
        "id": "003",
        "name": "Arjun Reddy", 
        "content": """
        Name: Arjun Reddy | Experience: 1 year
        Skills: Python, Flask, SQLite, basic Git, HTML, CSS
        Work: Junior Developer at WebAgency - small Flask websites
        Education: B.Tech IT, Osmania University
        Location: Hyderabad | Salary expectation: 6 LPA
        Achievements: Delivered 5 client websites on time
        """
    },
    {
        "id": "004",
        "name": "Sneha Krishnan",
        "content": """
        Name: Sneha Krishnan | Experience: 5 years
        Skills: Python, FastAPI, LangChain, OpenAI, PostgreSQL, Redis, Docker
        Work: AI Engineer at AIStartup - LLM applications, RAG systems
        Education: B.Tech CSE, IIT Madras
        Location: Chennai | Salary expectation: 25 LPA
        Achievements: Built RAG system serving 10k users, published 2 AI papers
        """
    },
    {
        "id": "005",
        "name": "Vikram Singh",
        "content": """
        Name: Vikram Singh | Experience: 2 years
        Skills: Python, FastAPI, PostgreSQL, Git, REST APIs, basic Docker
        Work: Software Engineer at MidSizeCo - API development and maintenance
        Education: B.Tech CSE, NIT Warangal
        Location: Hyderabad | Salary expectation: 10 LPA
        Achievements: Built payment integration API, improved test coverage to 85%
        """
    }
]

# ── STEP 1: SETUP EMBEDDINGS ──────────────────────────────
# HuggingFace embeddings run locally — completely FREE
# Converts text to vectors (lists of numbers)
# Similar text → similar vectors → similar numbers

print("⚙️  Loading embedding model (first time takes 1-2 mins)...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",  # small, fast, free model
    model_kwargs={"device": "cpu"}
)
print("✅ Embedding model loaded!")

# ── STEP 2: CREATE DOCUMENTS ──────────────────────────────
# LangChain works with Document objects
# Each document has content + metadata

documents = []
for resume in RESUMES:
    doc = Document(
        page_content=resume["content"],
        metadata={
            "candidate_id": resume["id"],
            "candidate_name": resume["name"]
        }
    )
    documents.append(doc)

# ── STEP 3: SPLIT INTO CHUNKS ─────────────────────────────
# Large documents get split into smaller chunks
# Each chunk gets its own embedding
# This allows precise retrieval

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       # max characters per chunk
    chunk_overlap=50      # overlap prevents losing context at boundaries
)
splits = text_splitter.split_documents(documents)
print(f"📄 Created {len(splits)} chunks from {len(documents)} resumes")

# ── STEP 4: STORE IN VECTOR DATABASE ─────────────────────
# ChromaDB stores embeddings locally (no API needed, no cost)
# persist_directory saves to disk so you don't re-embed every time

print("💾 Building vector database...")
vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=embeddings,
    persist_directory="./chroma_db"  # saved locally
)
print(f"✅ Vector database ready with {vectorstore._collection.count()} entries!")

# ── STEP 5: CREATE RETRIEVER ──────────────────────────────
# Retriever finds the k most similar documents to a query
# k=3 means "find the 3 most relevant resumes"

retriever = vectorstore.as_retriever(
    search_kwargs={"k": 3}
)

# ── STEP 6: SETUP CLAUDE ──────────────────────────────────
llm = ChatAnthropic(
    model=os.getenv("CLAUDE_MODEL"),
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_tokens=1024
)

# ── STEP 7: BUILD RAG CHAIN ───────────────────────────────
# This is the full RAG pipeline:
# Question → Retriever finds relevant resumes → Claude answers

RAG_PROMPT = """You are a smart HR assistant for SmartHire.
Use the following candidate resumes to answer the question.
Only use information from the provided resumes.
If the answer isn't in the resumes, say so clearly.

RELEVANT RESUMES:
{context}

QUESTION: {question}

Provide a helpful, specific answer based on the resume data."""

prompt = ChatPromptTemplate.from_template(RAG_PROMPT)

def format_docs(docs):
    """Format retrieved documents into a single string"""
    return "\n\n---\n\n".join([
        f"Candidate: {doc.metadata['candidate_name']}\n{doc.page_content}"
        for doc in docs
    ])

# The RAG chain:
# question → retriever → format → prompt → llm
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
)

# ── QUERY FUNCTION ────────────────────────────────────────
def ask_smarthire(question: str) -> str:
    """Ask anything about candidates — RAG finds the answer"""
    
    # Show which resumes were retrieved (educational)
    retrieved_docs = retriever.invoke(question)
    print(f"\n🔍 Retrieved {len(retrieved_docs)} relevant resumes:")
    for doc in retrieved_docs:
        print(f"   → {doc.metadata['candidate_name']}")
    
    # Get answer from Claude
    response = rag_chain.invoke(question)
    return response.content

# ── DEMO QUERIES ──────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SmartHire RAG - Candidate Intelligence System")
    print("=" * 60)

    # These questions test semantic search
    # Notice how RAG finds relevant candidates even without exact word match
    
    questions = [
        "Who has experience with AI and machine learning?",
        "Which candidates know Docker and are based in Hyderabad?",
        "Who is the strongest candidate for a Python backend role?",
        "Which candidate has the lowest salary expectation?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{'='*60}")
        print(f"Q{i}: {question}")
        print("-" * 60)
        answer = ask_smarthire(question)
        print(f"💡 Answer: {answer}")

    print("\n" + "=" * 60)
    print("🎯 RAG Pipeline Complete!")
    print("Your system just searched a vector database semantically!")
    print("=" * 60)