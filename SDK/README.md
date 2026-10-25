# Sentinel SDK

Sentinel SDK is a lightweight Python telemetry SDK for Starlette-compatible
applications. It records request information and sends telemetry events to a
Sentinel backend.

The middleware records:

- HTTP method
- Request route
- Response status code
- Request duration
- A unique request ID
- Application service name
- Deployment environment
- Exception type and message when a request fails

## Requirements

- Python 3.10 or later
- A Starlette-compatible application
- A Sentinel backend with a `POST /v1/telemetry` endpoint

FastAPI applications are supported through Starlette middleware compatibility.

## Installation

From the `SDK` directory, install the package:

```bash
pip install .
```

For FastAPI applications, install the optional dependency:

```bash
pip install ".[fastapi]"
```

During development, use an editable install:

```bash
pip install -e ".[fastapi]"
```

## Quick start with FastAPI

Create one telemetry client using the URL of your Sentinel backend, then add
the middleware to your application:

```python
from fastapi import FastAPI

from sentinel_sdk.client import Sentinel_client
from sentinel_sdk.middleware import SentinelMiddleware

app = FastAPI()

telemetry_client = Sentinel_client(
    backend_url="http://localhost:8000",
    api_key="your-api-key",
)

app.add_middleware(
    SentinelMiddleware,
    client=telemetry_client,
    service_name="checkout",
    environment="development",
)
```

For a deployed backend, replace the local URL:

```python
telemetry_client = Sentinel_client(
    backend_url="https://api.example.com",
    api_key="your-api-key",
)
```

## Where telemetry is sent

`backend_url` is the backend host. The SDK posts telemetry to:

```text
backend_url + /v1/telemetry
```

Examples:

```text
http://localhost:8000/v1/telemetry
https://api.example.com/v1/telemetry
```

The middleware builds an event for each request and passes it to the client:

```python
await client.send_event(event)
```

The client sends that event as a JSON `POST` request to `/v1/telemetry`.

## Configuration

### `Sentinel_client`

```python
Sentinel_client(
    backend_url="http://localhost:8000",
    api_key="your-api-key",
    timeout=5.0,
)
```

- `backend_url`: Required backend host URL. Trailing slashes are removed.
- `api_key`: Required API key used for backend authentication.
- `timeout`: HTTP request timeout in seconds. The default is `5.0`.

### `SentinelMiddleware`

```python
SentinelMiddleware(
    app,
    client=telemetry_client,
    service_name="checkout",
    environment="production",
)
```

- `client`: Required `Sentinel_client`, or another client exposing
  `send_event(event)`.
- `service_name`: Required name of the application or service.
- `environment`: Optional deployment environment. Defaults to
  `"development"`.

## Client lifecycle

The client supports asynchronous context-manager usage:

```python
async with Sentinel_client(
    backend_url="http://localhost:8000",
    api_key="your-api-key",
) as telemetry_client:
    await telemetry_client.send_event({"example": "event"})
```

For long-running applications, create one client during startup and close it
during shutdown:

```python
telemetry_client = Sentinel_client(
    backend_url="http://localhost:8000",
    api_key="your-api-key",
)

# Use telemetry_client while the application is running.

await telemetry_client.close()
```

Do not create a new telemetry client for every request.

## Event format

The middleware sends events with this structure:

```json
{
  "event_id": "generated-uuid",
  "timestamp": "2026-10-11T07:15:00+00:00",
  "service_name": "checkout",
  "environment": "production",
  "sdk_version": "0.1.0",
  "request_id": "generated-request-id",
  "request": {
    "method": "GET",
    "route": "/orders/{order_id}",
    "status_code": 200,
    "duration_ms": 12.35
  },
  "error": null
}
```

For a failed request, `error` contains exception details:

```json
{
  "type": "ValueError",
  "message": "invalid order"
}
```

Every successful response also receives the request ID in the
`X-Request-ID` response header.

## Backend endpoint

The backend should expose:

```text
POST /v1/telemetry
```

It should accept the event JSON payload and return a successful HTTP status
code, such as `202 Accepted`.

A minimal FastAPI endpoint can look like this:

```python
from typing import Any

from fastapi import FastAPI, Header, HTTPException

app = FastAPI()


@app.post("/v1/telemetry")
async def ingest_telemetry(
    event: dict[str, Any],
    authorization: str | None = Header(default=None),
):
    if authorization != "your-expected-authorization-value":
        raise HTTPException(status_code=401, detail="Invalid API key")

    print("Received telemetry:", event)
    return {"accepted": True}
```

The backend authentication value must match the authentication configuration
used by the SDK client.

## Error handling

- Invalid or empty `backend_url` raises `ValueError`.
- Invalid or empty `api_key` raises `ValueError`.
- Sending an event after closing the client raises `RuntimeError`.
- HTTP errors while sending telemetry return `False`.
- Telemetry delivery failures are logged by the middleware and do not replace
  the application's response.

## Running the tests

From the project root:

```bash
venv\Scripts\python.exe SDK\test\test.py
```
