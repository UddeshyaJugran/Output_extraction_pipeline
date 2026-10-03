from datetime import date
from pydantic import BaseModel, Field, field_validator


class Invoice(BaseModel):
    invoice_number: str = Field(min_length=1)
    vendor: str = Field(min_length=1)
    invoice_date: date
    total_amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    due_days: int | None = Field(default=None, ge=0)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, v: str) -> str:
        return v.upper()

    @field_validator("invoice_number", "vendor")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()