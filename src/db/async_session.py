from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не задан в переменных окружения или .env файле")

# ⚠️ ВАЖНО: Для async SQLAlchemy URL должен использовать асинхронный драйвер!
# Примеры:
# PostgreSQL: postgresql+asyncpg://user:password@host/dbname


engine = create_async_engine(
    DATABASE_URL,
    echo=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  
    autocommit=False,
    autoflush=False
)

async def get_db():
    """Асинхронная зависимость для получения сессии БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()  # Откат при ошибке в эндпоинте
            raise
