import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langgraph.prebuilt import create_react_agent
from app.tools.esg_tools import ALL_TOOLS

load_dotenv()

SYSTEM_PROMPT = """You are an ESG (Environmental, Social, Governance) sustainability expert assistant.
You help users explore and understand ESG scores, ratings, and sustainability metrics for companies across various sectors.

You have access to a database of 100 companies with ESG data including:
- Environmental, Social, and Governance scores (0-100)
- Total ESG Score and ESG Rating (AAA to B)
- Carbon emissions and revenue data
- Sector and country information

When answering questions:
- Use the available tools to look up real data before answering
- Provide specific numbers and rankings when possible
- Explain what ESG metrics mean when relevant
- Be concise but informative
- Format responses with markdown for readability
"""


def create_esg_agent():
    llm = ChatBedrock(
        model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"),
        region_name=os.getenv("BEDROCK_REGION", "us-east-1"),
        model_kwargs={"temperature": 0},
    )
    return create_react_agent(llm, ALL_TOOLS, prompt=SYSTEM_PROMPT)


async def run_esg_agent(message: str) -> str:
    agent = create_esg_agent()
    result = await agent.ainvoke({"messages": [{"role": "user", "content": message}]})
    messages = result["messages"]
    # Return the last AI message content
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.content and msg.type == "ai":
            return msg.content
    return "I couldn't generate a response. Please try again."
