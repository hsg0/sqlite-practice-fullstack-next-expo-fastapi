
"""
WHAT: Start the FastAPI backend.
WHY: Initialize the API, database, routes, and CORS.
HOW: Use FastAPI, SQLModel, Uvicorn, and environment settings.
IMPORTANT: Keep database logic in DBsetup.py and controllers.
"""

import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.DBsetup import createDatabaseTables
from routes.user import userRouter


# Load environment variables from BACKEND/.env.
backendFolder = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(backendFolder, ".env"))


# Read allowed React frontend addresses.
corsOrigins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]


# Manage application startup and shutdown.
@asynccontextmanager
async def applicationLifespan(application: FastAPI):

    createDatabaseTables()
    print("Database initialized successfully.")

    yield

    print("SQLCrashCourse backend shutting down.")


# Create FastAPI application.
app = FastAPI(
    title="SQLCrashCourse API",
    description="Python FastAPI backend using SQLModel and SQLite.",
    version="0.1.0",
    lifespan=applicationLifespan
)


# Allow configured frontend origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=corsOrigins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)


# Register user routes.
app.include_router(userRouter)


# Health check.
@app.get("/")
def home():
    return {
        "message": "SQLCrashCourse backend running",
        "status": "success"
    }


# Run FastAPI.
if __name__ == "__main__":
    print("FastAPI is running on http://localhost:4020")

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=4020,
        reload=True
    )
