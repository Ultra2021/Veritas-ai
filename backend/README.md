# Veritas AI Backend

Evidence-Driven AI Interview Platform Backend.

## Overview

This is Module 1 of the Veritas AI project: the backend foundation. It
bootstraps the FastAPI application, configuration loading, routing, and
documentation. Interview logic and AI/Gemini integrations arrive in later
modules.

## Tech Stack

- Python 3.11
- FastAPI
- Pydantic
- python-dotenv
- Uvicorn
- orjson
- google-generativeai

## Project Structure

```
backend/
├── agents/        # (future) AI agents
├── services/      # (future) business logic
├── models/        # (future) Pydantic / DB models
├── routes/        # API routes (health, root)
├── prompts/       # (future) prompt templates
├── database/      # (future) database connections
├── utils/         # (future) shared utilities
├── config.py      # environment configuration
├── main.py        # FastAPI application entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy the example environment file and set your API key:

```bash
cp .env.example .env
```

| Variable         | Description           | Default       |
| ---------------- | --------------------- | ------------- |
| `GEMINI_API_KEY` | Google Gemini API key | `None` (empty) |

`config.py` loads the `.env` file via `python-dotenv` and falls back to a
`None` default when `GEMINI_API_KEY` is not set.

## Running the Server

```bash
uvicorn main:app --reload
```

- Interactive docs (Swagger): http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Endpoints

### `GET /`

```json
{
  "status": "running",
  "project": "Veritas AI Backend"
}
```

### `GET /health`

```json
{
  "status": "healthy"
}
```
