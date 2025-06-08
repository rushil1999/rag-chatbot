import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

x_api_key = os.getenv("GROK_API_KEY")

x_api_client = OpenAI(
  api_key=x_api_key,
  base_url="https://api.x.ai/v1",
)
