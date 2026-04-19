from fastapi import FastAPI

app = FastAPI(
    title="Poll Application",
    version="1.0.0",
)

@app.get("/")
async def root():
    return {"message": "Hello from src/api/app.py!"}

@app.get("/health")
async def health():
    return {"status": "OK"}