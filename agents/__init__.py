import os
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Shared LLM instance for all agents
# Returns a structured Groq LLM client.
llm = ChatGroq(
      model="llama-3.3-70b-versatile",
      temperature=0.1, # Low temperature for consistent analysis
      api_key=os.getenv("GROQ_API_KEY"),
      max_tokens=500
)

def safe_parse_json(content: str) -> dict:
    """
    parse llm JSON responses
    handles markdown code fences

    Llama model sometimes wrap JSON in ```...``` even when asked not to
    this function strips those fences before parsing
    """
    content = content.strip()
    if content.startswith("```"):
      for part in content.split("```"):
        part = part.strip()
        if part.startswith("json"):
          part = part[4:].strip()
        if part.startswith("{"):
          content = part
          break
    return json.loads(content.strip())
