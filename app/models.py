from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.database import Base

class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    sample_code = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    operator = Column(String, nullable=False)
    status = Column(String, default="created", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)