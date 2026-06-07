from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional

ALLOWED_STATUSES = ["created", "measured", "approved", "rejected"]

class SampleCreate(BaseModel):
    sample_code: str = Field(..., min_length=1, description="Код пробы не может быть пустым")
    weight: float = Field(..., gt=0, description="Вес должен быть больше нуля")
    operator: str = Field(..., min_length=1, description="Оператор не может быть пустым")

    @field_validator("sample_code")
    def not_empty_code(cls, v):
        if not v or not v.strip():
            raise ValueError("Код пробы не может быть пустым")
        return v.strip()

    @field_validator("operator")
    def not_empty_operator(cls, v):
        if not v or not v.strip():
            raise ValueError("Оператор не может быть пустым")
        return v.strip()

class SampleResponse(BaseModel):
    id: int
    sample_code: str
    weight: float
    operator: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SampleStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    def validate_status(cls, v):
        if v not in ALLOWED_STATUSES:
            raise ValueError(f"Статус должен быть одним из: {ALLOWED_STATUSES}")
        return v