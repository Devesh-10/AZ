from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.esg_chat_agent import run_esg_agent

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = await run_esg_agent(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        return ChatResponse(response=f"I encountered an error processing your request. Please make sure the OPENAI_API_KEY environment variable is set. Error: {str(e)}")
