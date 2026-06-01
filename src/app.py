from fastapi import FastAPI
from src.api import polls, health, auth, polls_ai, benchmarks
from fastapi.security import HTTPBearer
app = FastAPI(
    title="Poll Application",
    description="API для управления опросами",
    version="1.0.0",
)

app.include_router(polls.router)
app.include_router(health.router)
app.include_router(auth.router)

app.include_router(polls_ai.router)

app.include_router(benchmarks.router)

# 🔑 Добавляем схему безопасности для Swagger
security = HTTPBearer(auto_error=False)
app.openapi_schema = None  # Сброс кэша схемы, если меняете на лету

# Явно регистрируем security scheme для OpenAPI
app.openapi_tags = [{"name": "Polls", "description": "Управление опросами"}]

