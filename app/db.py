from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# pool_pre_ping=True -> cek koneksi mati sebelum dipakai (penting di prod,
# misal DB di-restart, koneksi lama nggak nyangkut).
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
