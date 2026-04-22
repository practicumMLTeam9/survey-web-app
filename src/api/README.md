## Запуск FastAPI с помощью с помощью совместимого ASGI-сервера `uvicorn`

### Создать и активировать окружение Python

`python3 -m venv .venv`
`source .venv/bin/activate` # Linux/Mac
`.venv\Scripts\activate`    # Windows

### Установка зависимостей из requirements.txt)

`pip install -r requirements.txt`

### Запуск сервера с помощью uvicorn:

`uvicorn src.api.app:app --reload`

### Открыть swagger:

http://localhost:8000/docs
