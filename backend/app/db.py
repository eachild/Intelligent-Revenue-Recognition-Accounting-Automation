
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
engine=create_engine("sqlite+pysqlite:///./accruesmart.db", echo=False, future=True)
SessionLocal=sessionmaker(bind=engine, autoflush=False, autocommit=False)
class Base(DeclarativeBase): pass
