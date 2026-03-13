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
    system="You are a senior financial advisor at Charles Schwab.Answer everything in the context of financial services.",
    messages=[{
        "role": "user",
        "content": "What was Charles Schwab's stock price yesterday?"
    }]
)
print(response.content[0].text)
print(f"\n--- Token Usage ---")
print(f"Input tokens:  {response.usage.input_tokens}")
print(f"Output tokens: {response.usage.output_tokens}")
print(f"Total tokens:  {response.usage.input_tokens + response.usage.output_tokens}")