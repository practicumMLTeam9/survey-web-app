from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не задан в переменных окружения или .env файле")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    , echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Функция для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()