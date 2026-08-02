from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import LeadStatus


class LeadCreateForm(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class LeadUpdate(BaseModel):
    status: LeadStatus


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    resume_filename: str
    resume_content_type: str
    status: LeadStatus
    created_at: datetime
    updated_at: datetime
    resume_url: str | None = None
    reached_out_by: str | None = None
    reached_out_by_email: str | None = None
    reached_out_at: datetime | None = None


class LeadListResponse(BaseModel):
    items: list[LeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class HealthResponse(BaseModel):
    status: str
    environment: str
