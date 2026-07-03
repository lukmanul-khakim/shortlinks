from sqlalchemy import Column, DateTime, Integer, String, func

from .db import Base


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True)
    short_code = Column(String(16), unique=True, nullable=False, index=True)
    original_url = Column(String(2048), nullable=False)
    clicks = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
