from functools import lru_cache
from pathlib import Path

from supabase import Client, create_client

from app.core.config import Settings, get_settings


@lru_cache
def get_supabase_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("Supabase is not configured")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


class StorageService:
    """Uploads resumes to Supabase Storage, or local disk when Supabase is unset."""

    def __init__(self, settings: Settings | None = None, client: Client | None = None):
        self.settings = settings or get_settings()
        self._client = client
        self.local_root = Path(self.settings.local_upload_dir)

    @property
    def use_supabase(self) -> bool:
        return bool(self.settings.supabase_url and self.settings.supabase_service_role_key)

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    def upload_resume(
        self,
        *,
        object_path: str,
        content: bytes,
        content_type: str,
    ) -> str:
        if self.use_supabase:
            bucket = self.settings.supabase_resumes_bucket
            self.client.storage.from_(bucket).upload(
                path=object_path,
                file=content,
                file_options={"content-type": content_type, "upsert": "false"},
            )
            return object_path

        destination = self.local_root / object_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return object_path

    def create_signed_url(self, object_path: str, expires_in: int = 3600) -> str:
        if self.use_supabase:
            bucket = self.settings.supabase_resumes_bucket
            result = self.client.storage.from_(bucket).create_signed_url(object_path, expires_in)
            signed = result.get("signedURL") or result.get("signedUrl")
            if not signed:
                raise RuntimeError("Failed to create signed URL for resume")
            if signed.startswith("http"):
                return signed
            return f"{self.settings.supabase_url.rstrip('/')}/storage/v1{signed}"

        return f"/api/v1/leads/files/{object_path}"
