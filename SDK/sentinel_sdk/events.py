from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


SDK_VERSION = "0.1.0"


def build_event(
    *,
    service_name: str,
    method: str,
    route: str,
    status_code: int,
    duration_ms: float,
    request_id: str,
    environment: str = "development",
    exception_type: str | None = None,
    exception_message: str | None = None,
) -> dict[str, Any]:
    return {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service_name": service_name,
        "environment": environment,
        "sdk_version": SDK_VERSION,
        "request_id": request_id,
        "method": method,
        "route": route,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "exception_type": exception_type,
        "exception_message": exception_message,
    }