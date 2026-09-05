# EdiBuddy

EdiBuddy is an AI-powered adaptive learning platform that acts as a personalized AI teacher. It teaches students through explanations, questions, evaluation, visual demonstrations, and adaptive learning. It can also use uploaded PDF materials as supporting context while keeping the student's chosen topic as the primary learning focus.

## Table of Contents

- [How to Run EdiBuddy](#how-to-run-edibuddy)
  - [Backend](#backend)
  - [Frontend](#frontend)
- [EdiBuddy Architecture](#edibuddy-architecture)
- [How EdiBuddy Works](#how-edibuddy-works)
- [Technologies Used](#technologies-used)
  - [Backend](#backend-1)
  - [Frontend](#frontend-1)
- [Core Features](#core-features)

## How to Run EdiBuddy

### Backend

From the project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend will be available at:

```
http://127.0.0.1:8000
```

### Frontend

Open another terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open the local URL displayed by Vite.

# Root Environment Variables

Before running the backend or frontend, create a .env file in the project root (outside both the backend and frontend folders). This file holds the API keys shared across the project, such as Simli and Groq:

powershell
From the project root
New-Item .env -ItemType File

Add the following keys to the root .env file:

DATABASE_URL=postgresql://username:password@localhost:5432/edibuddy
SIMLI_API_KEY=your_simli_api_key_here
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL — PostgreSQL connection string used by the backend (SQLAlchemy) to connect to the database. Update the username, password, host, port, and database name to match your local PostgreSQL setup.
SIMLI_API_KEY — required for the live AI Teacher avatar (Simli WebRTC).
GROQ_API_KEY — required for Groq-powered model inference.

Make sure .env is listed in .gitignore so your keys are never committed to the repository.

## EdiBuddy Architecture

The architecture diagram is stored directly inside this repository.

![EdiBuddy Architecture](architecture.png)

## How EdiBuddy Works

EdiBuddy follows an adaptive AI teaching loop:

**Understand → Plan → Explain → Demonstrate → Question → Evaluate → Adapt → Continue → Assess → Remember**

1. The student selects a topic to learn.
2. EdiBuddy creates a lesson plan based on the selected topic.
3. If a PDF is uploaded, relevant information is retrieved using RAG and used as supporting context.
4. The AI Teacher explains the concept in a structured and understandable way.
5. Visual teaching such as equations, diagrams, and PDF-based visuals supports the explanation.
6. The AI Teacher asks questions to check the student's understanding.
7. The backend evaluates the student's answer.
8. Misconceptions and learning difficulties are detected.
9. The teaching strategy is adapted according to the student's performance.
10. The student's learning state, mastery, lesson progress, and session information are persisted in the database.
11. Previous sessions can be recovered without regenerating the original teaching events.
12. Voice, multilingual support, and live AI Teacher presentation provide a more human-like learning experience.

## Technologies Used

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- pgvector
- RAG (Retrieval-Augmented Generation)
- LLM-->DEFAULT_MODEL = "openai/gpt-oss-120b"
- PyPDF
- Embeddings-->MODEL_NAME = "all-MiniLM-L6-v2"
- Edge TTS
- Simli WebRTC
- Pydantic
- Pytest

### Frontend

- React
- TypeScript
- Vite
- CSS
- Web Audio API
- Simli Client SDK
- REST API
- Local Storage

## Core Features

- Topic-based AI teaching
- Adaptive learning
- Personalized teaching
- PDF upload and document-grounded learning
- RAG-based semantic retrieval
- AI-generated lesson structure
- Question and answer evaluation
- Misconception detection
- Learning-state and mastery tracking
- Session persistence and recovery
- Visual and diagram-based teaching
- PDF diagram support
- AI Teacher voice
- Multilingual teaching support
- Live AI Teacher avatar
- Learning history and progress tracking
