
import os
from typing import Any

import httpx


class SentinelClient:
    def __init__(self, timeout: float = 5.0) -> None:
        backend_url = os.getenv("SENTINEL_BACKEND_URL")

        if not backend_url or not backend_url.strip():
            raise ValueError("SENTINEL_BACKEND_URL is not set")

        self.backend_url = backend_url.rstrip("/")
        self._closed = False

        self.http_client = httpx.AsyncClient(
            base_url=self.backend_url,
            timeout=httpx.Timeout(timeout),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "sentinel-sdk/0.1.0",
            },
        )

    async def send_event(self, event: dict[str, Any]) -> bool:
        if self._closed:
            raise RuntimeError("SentinelClient is closed")

        try:
            response = await self.http_client.post(
                "/v1/telemetry",
                json=event,
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False

    async def close(self) -> None:
        if self._closed:
            return

        await self.http_client.aclose()
        self._closed = True

    async def __aenter__(self) -> "SentinelClient":
        if self._closed:
            raise RuntimeError("SentinelClient is closed")
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc: Any,
        tb: Any,
    ) -> None:
        await self.close()
