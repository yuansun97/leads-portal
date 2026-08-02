import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models import Lead, LeadStatus
from app.schemas.leads import LeadCreateForm, LeadResponse
from app.services.outbox import enqueue_lead_emails
from app.services.storage import StorageService


class LeadService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
        storage: StorageService | None = None,
    ):
        self.session = session
        self.settings = settings or get_settings()
        self.storage = storage or StorageService(self.settings)

    async def create_lead(self, form: LeadCreateForm, resume: UploadFile) -> Lead:
        content_type = resume.content_type or "application/octet-stream"
        if content_type not in self.settings.allowed_content_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported resume type: {content_type}",
            )

        content = await resume.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume file is empty")
        if len(content) > self.settings.max_resume_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Resume exceeds {self.settings.max_resume_bytes} bytes",
            )

        lead_id = uuid.uuid4()
        original_name = Path(resume.filename or "resume.pdf").name
        object_path = f"{lead_id}/{original_name}"

        try:
            self.storage.upload_resume(
                object_path=object_path,
                content=content,
                content_type=content_type,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to upload resume: {exc}",
            ) from exc

        lead = Lead(
            id=lead_id,
            first_name=form.first_name.strip(),
            last_name=form.last_name.strip(),
            email=str(form.email).lower(),
            resume_path=object_path,
            resume_filename=original_name,
            resume_content_type=content_type,
            status=LeadStatus.PENDING,
        )
        self.session.add(lead)
        enqueue_lead_emails(self.session, lead, self.settings)
        await self.session.commit()
        await self.session.refresh(lead)
        return lead

    async def list_leads(
        self,
        page: int,
        page_size: int,
        *,
        status: LeadStatus | None = None,
    ) -> tuple[list[Lead], int]:
        filters = []
        if status is not None:
            filters.append(Lead.status == status)

        count_stmt = select(func.count()).select_from(Lead)
        list_stmt = select(Lead).order_by(Lead.created_at.desc())
        if filters:
            count_stmt = count_stmt.where(*filters)
            list_stmt = list_stmt.where(*filters)

        total = await self.session.scalar(count_stmt) or 0
        result = await self.session.execute(
            list_stmt.offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_lead(self, lead_id: uuid.UUID) -> Lead:
        lead = await self.session.get(Lead, lead_id)
        if lead is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        return lead

    async def update_status(
        self,
        lead_id: uuid.UUID,
        new_status: LeadStatus,
        *,
        actor_id: str,
        actor_email: str | None = None,
    ) -> Lead:
        """Claim PENDING → REACHED_OUT atomically for a shared attorney inbox.

        Idempotent for the same attorney. Concurrent/other attorney gets 409.
        """
        if new_status != LeadStatus.REACHED_OUT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only status REACHED_OUT is supported",
            )

        lead = await self.get_lead(lead_id)

        if lead.status == LeadStatus.REACHED_OUT:
            if lead.reached_out_by == actor_id:
                return lead
            who = lead.reached_out_by_email or lead.reached_out_by or "another attorney"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Lead already marked reached out by {who}",
            )

        if lead.status != LeadStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only PENDING → REACHED_OUT transitions are allowed",
            )

        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            update(Lead)
            .where(Lead.id == lead_id, Lead.status == LeadStatus.PENDING)
            .values(
                status=LeadStatus.REACHED_OUT,
                reached_out_by=actor_id,
                reached_out_by_email=actor_email,
                reached_out_at=now,
                updated_at=now,
            )
            .returning(Lead)
        )
        claimed = result.scalar_one_or_none()
        if claimed is None:
            await self.session.rollback()
            current = await self.get_lead(lead_id)
            if current.status == LeadStatus.REACHED_OUT and current.reached_out_by == actor_id:
                return current
            who = current.reached_out_by_email or current.reached_out_by or "another attorney"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Lead already marked reached out by {who}",
            )

        await self.session.commit()
        await self.session.refresh(claimed)
        return claimed

    def to_response(self, lead: Lead, *, include_resume_url: bool = False) -> LeadResponse:
        resume_url = None
        if include_resume_url:
            try:
                resume_url = self.storage.create_signed_url(lead.resume_path)
            except Exception:  # noqa: BLE001
                resume_url = None
        return LeadResponse(
            id=lead.id,
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            resume_filename=lead.resume_filename,
            resume_content_type=lead.resume_content_type,
            status=lead.status,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
            resume_url=resume_url,
            reached_out_by=lead.reached_out_by,
            reached_out_by_email=lead.reached_out_by_email,
            reached_out_at=lead.reached_out_at,
        )
