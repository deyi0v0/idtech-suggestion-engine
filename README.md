# IDTECH Suggestion Engine

An AI-powered and rule-based product recommendation chatbot for IDTECH payment terminals. 

## Tech Stack

- **Frontend**: React (Vite), JavaScript
- **Backend**: Python 3.11+, FastAPI
- **Database**: SQLite via SQLAlchemy
- **LLM**: OpenAI API (gpt-4o-mini)
- **PDF Generation**: fpdf2
- **Testing**: Pytest (backend), Jest (frontend)
- **Deployment**: Docker + docker-compose

## Project Structure

```
├── docker-compose.yml
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── db/                   # Database models, engine, seed script
│   ├── schemas/              # Pydantic request/response models
│   ├── routers/              # API endpoints (chat, compare, compatibility, pdf)
│   ├── engine/               # Rule engine & compatibility logic
│   ├── llm/                  # OpenAI client, prompt builders, privacy filters
│   └── pdf/                  # PDF report generator
├── frontend/
│   └── src/
│       ├── api/              # Backend API client functions
│       ├── components/       # Chat, ComparisonTable, PDFDownload
│       └── pages/            # Home page
└── tests/
    ├── backend/              # Pytest tests
    └── frontend/             # Jest tests
```

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- An OpenAI API key

### 1. Clone the repo

```bash
git clone <repo-url>
cd idtech-suggestion-engine
```

### 2. Set up environment variables

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-key
DATABASE_URL=sqlite:///./db/products.db
```

### 3. Run with Docker

```bash
docker-compose up --build
```

This starts both services:
- **Backend** at http://localhost:8000
- **Frontend** at http://localhost:5173

### Running without Docker

**Backend:**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Seeding the Database

Once the data team provides `data/products.csv`, run the seed script:

```bash
cd backend
python -m db.seed
```

## Running Tests

**Backend:**

```bash
cd backend
pytest ../tests/backend
```

**Frontend:**

```bash
cd frontend
npm test
```