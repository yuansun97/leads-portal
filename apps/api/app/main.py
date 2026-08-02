import asyncio
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, leads
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.outbox import OutboxWorker

logger = logging.getLogger(__name__)


async def _outbox_poll_loop(stop_event: asyncio.Event) -> None:
    settings = get_settings()
    worker = OutboxWorker(settings)
    logger.info("outbox.poller.started interval=%s", settings.outbox_poll_interval_seconds)
    while not stop_event.is_set():
        try:
            async with AsyncSessionLocal() as session:
                processed = await worker.process_batch(session)
                if processed:
                    logger.info("outbox.poller.processed count=%s", processed)
        except Exception:  # noqa: BLE001
            logger.exception("outbox.poller.error")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=settings.outbox_poll_interval_seconds)
        except TimeoutError:
            continue
    logger.info("outbox.poller.stopped")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    stop_event = asyncio.Event()
    task = asyncio.create_task(_outbox_poll_loop(stop_event))
    yield
    stop_event.set()
    await task


def create_app() -> FastAPI:
    settings = get_settings()
    settings.validate_runtime_guards()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(leads.router, prefix="/api/v1")
    return app


app = create_app()
