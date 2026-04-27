from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DATABASE_URL = "postgresql://user:password@host/dbname"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    , echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Функция для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()