## Запуск FastAPI с помощью с помощью совместимого ASGI-сервера `uvicorn`

### Создать и активировать окружение Python

`python3 -m venv .venv`
`source .venv/bin/activate` # Linux/Mac
`.venv\Scripts\activate`    # Windows

### Установка зависимостей из requirements.txt)

`pip install -r requirements.txt

### Создайте в корне приложения `.env` - файл с содержимым:

SECRET_KEY= # Секреты — сгенерируйте  python3 -c "import secrets; print(secrets.token_urlsafe(32))"

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30

REFRESH_TOKEN_EXPIRE_DAYS=7

DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname


### Запуск сервера с помощью uvicorn:

`uvicorn src.app:app --reload`

### Открыть swagger:

http://localhost:8000/docs


