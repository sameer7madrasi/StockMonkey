import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.responses.create(
    model="gpt-5.4",
    input="Reply with exactly: OpenAI connection successful."
)

print(response.output_text)
