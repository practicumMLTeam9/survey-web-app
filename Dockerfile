FROM python:3.10-slim
WORKDIR /app

# Копируем только зависимости (кэш слоёв)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY src/ ./src/

EXPOSE 8000
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]