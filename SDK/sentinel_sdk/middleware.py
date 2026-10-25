import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("sentinel")

class SentinelMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        client,
        service_name: str,
        environment: str = "development",
    ) -> None:
        super().__init__(app)
        self.client = client
        self.service_name = service_name
        self.environment = environment

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        start_time = time.perf_counter()
        request_id = str(uuid4())
        exception_type = None
        exception_message = None
        timestamp = datetime.now(timezone.utc)
        response = None
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            exception_type = type(exc).__name__
            exception_message = str(exc)
            raise
        finally:
            duration_ms = (
                time.perf_counter() - start_time
            ) * 1000

            route_object = request.scope.get("route")
            route = getattr(route_object, "path", "<unmatched>")

            event = build_event(
                request_id=request_id,
                timestamp=timestamp,
                api_key_id=self.client.api_key_id,
                project_id=self.client.project_id,
                service_name=self.service_name,
                method=request.method,
                route=route,
                status_code=status_code,
                duration_ms=duration_ms,
                environment=self.environment,
                exception_type=exception_type,
                exception_message=exception_message,
            )

            try:
                await self.client.send_event(event)
            except Exception:
                logger.debug(
                    "Sentinel telemetry delivery failed",
                    exc_info=True,
                )

        if response is not None:
            response.headers["X-Request-ID"] = request_id
            return response

        raise RuntimeError("Request ended without a response")
