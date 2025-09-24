from dotenv import load_dotenv
import os
import sys
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

def ask_llm(query: str, system: str = "You are a concise, helpful assistant.") -> str:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
    res = llm.invoke([SystemMessage(content=system), HumanMessage(content=query)])
    return res.content

if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    print(ask_llm(query))
