import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .routers import chat, pdf

# Load environment variables
load_dotenv()

app = FastAPI(title="ID TECH Suggestion Engine")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Vite frontend default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(pdf.router, prefix="/api/pdf", tags=["PDF"])

@app.get("/")
async def root():
    return {"message": "ID TECH Suggestion Engine API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
