from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
from app.config import settings
import asyncio

# Create engine with improved connection pooling for cloud databases
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,           # Smaller pool for cloud DB
    max_overflow=0,        # No overflow for stability
    pool_pre_ping=True,    # Validates connections before use
    pool_recycle=300,      # Recycle connections every 5 minutes
    echo=False
)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

async def check_db_connection():
    """Test database connectivity"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

async def ensure_db_connection():
    """Ensure database connection is available with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with AsyncSessionLocal() as session:
                await session.execute("SELECT 1")
                return session
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(1)  # Wait 1 second before retry