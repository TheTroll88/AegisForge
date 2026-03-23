# kratos_core/routes/ai_chat.py

from fastapi import APIRouter, Request
from pydantic import BaseModel
import openai
from dotenv import load_dotenv
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter()

class ChatRequest(BaseModel):
    prompt: str

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or "gpt-3.5-turbo" to save tokens
            messages=[
                {"role": "system", "content": "You are a helpful assistant named Aegis."},
                {"role": "user", "content": request.prompt}
            ]
        )
        answer = response['choices'][0]['message']['content']
        return {"response": answer}
    except Exception as e:
        return {"error": str(e)}
