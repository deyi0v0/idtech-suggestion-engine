"""
This file is a simple test endpoint using fastapi
that can be used to get completions in 

use the same env from backend/ and export OPENAI_API_KEY and you should be good!
run with `uvicorn api:app --reload`
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import client

app = FastAPI()

# 1. FIX CORS: This allows your React app to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Define the schema to match your React 'Message' type
class Message(BaseModel):
    content: str
    author: str # 'client', 'server', or 'system'

class ChatRequest(BaseModel):
    messages: List[Message]

def get_role(client_role) -> str:
    if client_role == "client":
        return "user"
    elif client_role == "server":
        return "assistant"
    else:
        return "system"

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Convert Pydantic models back to dicts for OpenAI if needed
    formatted_messages = [
        {"role": get_role(m.author), "content": m.content}
        for m in request.messages
    ]

    response_text = await client.get_completion_from_messages(formatted_messages)
    
    return {"content": response_text, "author": "server"}

