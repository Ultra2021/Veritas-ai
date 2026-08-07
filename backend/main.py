"""Veritas AI Backend entry point.

Evidence-Driven AI Interview Platform Backend.

Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI

from routes import health

app = FastAPI(
    title="Veritas AI Backend",
    version="1.0.0",
    description="Evidence-Driven AI Interview Platform Backend",
)

app.include_router(health.router)
