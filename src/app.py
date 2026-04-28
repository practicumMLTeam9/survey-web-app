from fastapi import FastAPI
from api import polls, health

app = FastAPI(
    title="Poll Application",
    version="1.0.0",
)

app.include_router(polls.router)
app.include_router(health.router)


