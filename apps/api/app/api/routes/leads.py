from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import require_attorney
from app.db.session import AsyncSessionLocal, get_db
from app.schemas.leads import LeadListResponse, LeadResponse, LeadUpdate
from app.services.leads import LeadService
from app.services.outbox import OutboxWorker

router = APIRouter(prefix="/leads", tags=["leads"])


async def _kick_outbox(lead_id: UUID) -> None:
    worker = OutboxWorker()
    async with AsyncSessionLocal() as session:
        await worker.process_lead(session, lead_id)


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    first_name: Annotated[str, Form(min_length=1, max_length=100)],
    last_name: Annotated[str, Form(min_length=1, max_length=100)],
    email: Annotated[str, Form()],
    resume: Annotated[UploadFile, File()],
) -> LeadResponse:
    from app.schemas.leads import LeadCreateForm

    form = LeadCreateForm(first_name=first_name, last_name=last_name, email=email)
    service = LeadService(db)
    lead = await service.create_lead(form, resume)
    background_tasks.add_task(_kick_outbox, lead.id)
    return service.to_response(lead)


@router.get("", response_model=LeadListResponse)
async def list_leads(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[dict, Depends(require_attorney)],
    page: int = 1,
    page_size: int = 20,
) -> LeadListResponse:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    service = LeadService(db)
    items, total = await service.list_leads(page, page_size)
    return LeadListResponse(
        items=[service.to_response(item, include_resume_url=True) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/files/{lead_id}/{filename}")
async def download_local_resume(
    lead_id: UUID,
    filename: str,
    _user: Annotated[dict, Depends(require_attorney)],
) -> FileResponse:
    """Serve resumes from local disk when Supabase Storage is not configured."""
    settings = get_settings()
    if settings.supabase_url and settings.supabase_service_role_key:
        raise HTTPException(status_code=404, detail="Not found")

    safe_name = Path(filename).name
    path = Path(settings.local_upload_dir) / str(lead_id) / safe_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[dict, Depends(require_attorney)],
) -> LeadResponse:
    service = LeadService(db)
    lead = await service.get_lead(lead_id)
    return service.to_response(lead, include_resume_url=True)


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    payload: LeadUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[dict, Depends(require_attorney)],
) -> LeadResponse:
    service = LeadService(db)
    lead = await service.update_status(lead_id, payload.status)
    return service.to_response(lead, include_resume_url=True)
