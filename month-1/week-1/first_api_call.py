import anthropic
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load API key from environment variable for security
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=512,
    messages=[{
        "role": "user",
        "content": "Explain RAG to a Java backend engineer in simple terms"
    }]
)
print(response.content[0].text)