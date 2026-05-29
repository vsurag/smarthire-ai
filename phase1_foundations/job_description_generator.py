import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

def generate_job_description(job_title, company_name, experience_years):
    
    message = client.messages.create(
        model=os.getenv("CLAUDE_MODEL"),
        max_tokens=1024,
        system="""You are an expert HR professional and technical recruiter 
        with 10 years of experience writing compelling job descriptions. 
        Write clear, inclusive, and attractive job descriptions.""",
        messages=[
            {
                "role": "user",
                "content": f"""Write a professional job description for:
                
Job Title: {job_title}
Company: {company_name}  
Experience Required: {experience_years} years

Include:
- Role summary (2-3 lines)
- Key responsibilities (5 points)
- Required skills (5 points)
- Nice to have skills (3 points)
- What we offer (3 points)

Keep it professional and engaging."""
            }
        ]
    )

    return message.content[0].text


if __name__ == "__main__":
    print("=" * 50)
    print("SmartHire - Job Description Generator")
    print("=" * 50)

    job_title = input("\nEnter job title: ")
    company = input("Enter company name: ")
    experience = input("Years of experience required: ")

    print("\nGenerating job description...\n")

    jd = generate_job_description(job_title, company, experience)

    print(jd)
    print("\n" + "=" * 50)