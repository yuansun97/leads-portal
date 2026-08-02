import logging
from abc import ABC, abstractmethod

import resend

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class EmailSender(ABC):
    @abstractmethod
    async def send(
        self,
        *,
        to_email: str,
        subject: str,
        body_text: str,
        idempotency_key: str,
    ) -> str:
        """Send an email and return a provider message id."""


class LogEmailSender(EmailSender):
    async def send(
        self,
        *,
        to_email: str,
        subject: str,
        body_text: str,
        idempotency_key: str,
    ) -> str:
        logger.info(
            "email.disabled to=%s subject=%s idempotency_key=%s body=%s",
            to_email,
            subject,
            idempotency_key,
            body_text[:200],
        )
        return f"log-{idempotency_key}"


class ResendEmailSender(EmailSender):
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        resend.api_key = self.settings.resend_api_key

    async def send(
        self,
        *,
        to_email: str,
        subject: str,
        body_text: str,
        idempotency_key: str,
    ) -> str:
        response = resend.Emails.send(
            {
                "from": self.settings.resend_from,
                "to": [to_email],
                "subject": subject,
                "text": body_text,
                "headers": {"Idempotency-Key": idempotency_key},
            }
        )
        message_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)
        if not message_id:
            raise RuntimeError(f"Resend did not return a message id: {response!r}")
        return str(message_id)


def build_email_sender(settings: Settings | None = None) -> EmailSender:
    settings = settings or get_settings()
    if not settings.email_enabled or not settings.resend_api_key:
        return LogEmailSender()
    return ResendEmailSender(settings)
