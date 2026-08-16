import app.env  # noqa: F401  (loads .env before anything reads os.getenv)
import os
from openai import AsyncOpenAI


x_api_key = os.getenv("GROK_API_KEY")

x_api_client = AsyncOpenAI(
  api_key=x_api_key,
  base_url="https://api.x.ai/v1",
)
