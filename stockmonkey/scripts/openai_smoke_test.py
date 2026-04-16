import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from app.llm.model_config import summary_model  # noqa: E402

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.responses.create(
    model=summary_model(),
    input="Reply with exactly: OpenAI connection successful."
)

print(response.output_text)
