from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI

load_dotenv()

OPENAI_MODEL = "gpt-4.1"
DATE_FMT = "%Y-%m-%d"
REQUIRED_FIELDS = ["location", "checkin", "checkout", "adults", "rooms"]


input_llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

validator_llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)
