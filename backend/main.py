import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables before importing routers
load_dotenv()

from .routers import chat, pdf
from .routers.maintenance import hardware, software, prompts, docs

app = FastAPI(title="ID TECH Suggestion Engine")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Vite frontend default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Customer Routes
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(pdf.router, prefix="/api/pdf", tags=["PDF"])

# Maintenance Routes
app.include_router(hardware.router, prefix="/api/maintenance/hardware", tags=["Maintenance Hardware"])
app.include_router(software.router, prefix="/api", tags=["Maintenance Software"]) # router in software.py contains "maintenance" prefix
app.include_router(prompts.router, prefix="/api/maintenance/prompts", tags=["Maintenance Prompts"])
app.include_router(docs.router, prefix="/api/maintenance/docs", tags=["Maintenance Docs"])

@app.get("/")
async def root():
    return {"message": "ID TECH Suggestion Engine API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
