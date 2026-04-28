from fastapi import FastAPI
from src.api import polls, health, auth

app = FastAPI(
    title="Poll Application",
    version="1.0.0",
)

app.include_router(polls.router)
app.include_router(health.router)
app.include_router(auth.router)


