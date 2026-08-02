import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models import EmailOutbox, EmailTemplate, Lead, OutboxStatus
from app.services.email import EmailSender, build_email_sender

logger = logging.getLogger(__name__)


def build_prospect_email(lead: Lead) -> tuple[str, str]:
    subject = "We received your application"
    body = (
        f"Hi {lead.first_name},\n\n"
        "Thank you for submitting your information. An attorney on our team will review "
        "your application and reach out soon.\n\n"
        "Best regards,\n"
        "Leads Portal"
    )
    return subject, body


def build_attorney_email(lead: Lead) -> tuple[str, str]:
    subject = f"New lead: {lead.first_name} {lead.last_name}"
    body = (
        f"A new lead was submitted.\n\n"
        f"Name: {lead.first_name} {lead.last_name}\n"
        f"Email: {lead.email}\n"
        f"Resume: {lead.resume_filename}\n"
        f"Lead ID: {lead.id}\n"
        f"Status: {lead.status.value}\n"
    )
    return subject, body


def enqueue_lead_emails(
    session: AsyncSession,
    lead: Lead,
    settings: Settings | None = None,
) -> list[EmailOutbox]:
    settings = settings or get_settings()
    prospect_subject, prospect_body = build_prospect_email(lead)
    attorney_subject, attorney_body = build_attorney_email(lead)

    rows = [
        EmailOutbox(
            lead_id=lead.id,
            template=EmailTemplate.PROSPECT_CONFIRMATION,
            to_email=lead.email,
            subject=prospect_subject,
            body_text=prospect_body,
            status=OutboxStatus.PENDING,
            idempotency_key=f"lead:{lead.id}:prospect",
        ),
        EmailOutbox(
            lead_id=lead.id,
            template=EmailTemplate.ATTORNEY_NOTIFICATION,
            to_email=settings.attorney_notify_email,
            subject=attorney_subject,
            body_text=attorney_body,
            status=OutboxStatus.PENDING,
            idempotency_key=f"lead:{lead.id}:attorney",
        ),
    ]
    session.add_all(rows)
    return rows


def _backoff_seconds(attempts: int) -> int:
    return min(60 * (2 ** max(attempts - 1, 0)), 3600)


class OutboxWorker:
    def __init__(
        self,
        settings: Settings | None = None,
        sender: EmailSender | None = None,
    ):
        self.settings = settings or get_settings()
        self.sender = sender or build_email_sender(self.settings)

    def _claim_query(self) -> Select[tuple[EmailOutbox]]:
        now = datetime.now(timezone.utc)
        return (
            select(EmailOutbox)
            .where(
                EmailOutbox.status.in_([OutboxStatus.PENDING, OutboxStatus.FAILED]),
                EmailOutbox.attempts < self.settings.outbox_max_attempts,
                EmailOutbox.next_attempt_at <= now,
            )
            .order_by(EmailOutbox.created_at.asc())
            .limit(self.settings.outbox_batch_size)
            .with_for_update(skip_locked=True)
        )

    async def process_batch(self, session: AsyncSession) -> int:
        result = await session.execute(self._claim_query())
        rows = list(result.scalars().all())
        if not rows:
            return 0

        for row in rows:
            row.status = OutboxStatus.SENDING
        await session.commit()

        processed = 0
        for row in rows:
            try:
                message_id = await self.sender.send(
                    to_email=row.to_email,
                    subject=row.subject,
                    body_text=row.body_text,
                    idempotency_key=row.idempotency_key,
                )
                row.provider_message_id = message_id
                row.status = OutboxStatus.SENT
                row.last_error = None
                row.attempts += 1
                processed += 1
            except Exception as exc:  # noqa: BLE001 - record and continue batch
                row.attempts += 1
                row.last_error = str(exc)[:2000]
                if row.attempts >= self.settings.outbox_max_attempts:
                    row.status = OutboxStatus.FAILED
                else:
                    row.status = OutboxStatus.PENDING
                    row.next_attempt_at = datetime.now(timezone.utc) + timedelta(
                        seconds=_backoff_seconds(row.attempts)
                    )
                logger.exception("outbox.send_failed id=%s", row.id)
            await session.commit()
        return processed

    async def process_lead(self, session: AsyncSession, lead_id: UUID) -> int:
        result = await session.execute(
            select(EmailOutbox)
            .where(
                EmailOutbox.lead_id == lead_id,
                EmailOutbox.status.in_([OutboxStatus.PENDING, OutboxStatus.FAILED]),
            )
            .with_for_update(skip_locked=True)
        )
        rows = list(result.scalars().all())
        if not rows:
            return 0
        for row in rows:
            row.status = OutboxStatus.SENDING
        await session.commit()

        processed = 0
        for row in rows:
            try:
                message_id = await self.sender.send(
                    to_email=row.to_email,
                    subject=row.subject,
                    body_text=row.body_text,
                    idempotency_key=row.idempotency_key,
                )
                row.provider_message_id = message_id
                row.status = OutboxStatus.SENT
                row.last_error = None
                row.attempts += 1
                processed += 1
            except Exception as exc:  # noqa: BLE001
                row.attempts += 1
                row.last_error = str(exc)[:2000]
                if row.attempts >= self.settings.outbox_max_attempts:
                    row.status = OutboxStatus.FAILED
                else:
                    row.status = OutboxStatus.PENDING
                    row.next_attempt_at = datetime.now(timezone.utc) + timedelta(
                        seconds=_backoff_seconds(row.attempts)
                    )
                logger.exception("outbox.send_failed id=%s", row.id)
            await session.commit()
        return processed
