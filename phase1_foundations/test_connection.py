import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("")
)

message = client.messages.create(
    model=os.getenv("CLAUDE_MODEL"),
    max_tokens=256,
    messages=[
        {"role": "user", "content": "Say hello and confirm you are working!"}
    ]
)

print(message.content[0].text)
