from fastapi import FastAPI, status, HTTPException
from api import polls

app = FastAPI(
    title="Poll Application",
    version="1.0.0",
)

app.include_router(polls.router)


