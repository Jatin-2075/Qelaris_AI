import asyncio
import uuid
import redis.asyncio as redis

from sqlalchemy.orm import Session

from ....database.database import SessionLocal
from ....database.models.event_model import Event
from ....database.models.incident_model import Incident
from ..setting import settings
from ..graphrag.pipeline import run_graphrag


STREAM = "sentinel:events"
GROUP = "sentinel-workers"
CONSUMER = "worker-1"

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


async def setup_consumer_group():
    try:
        await redis_client.xgroup_create(
            STREAM, GROUP, id="0", mkstream=True
        )
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def process_event(event_id: str) -> str:
    db: Session = SessionLocal()

    try:
        event = db.query(Event).filter(Event.id == event_id).first()

        if event is None:
            raise ValueError(f"Event {event_id} not found")

        failed = (
            event.status_code >= 400
            or event.exception_type is not None
        )

        if not failed:
            event.processing_status = "processed"
            db.commit()
            return "passed"

        event.processing_status = "failed"

        incident = Incident(
            project_id=event.project_id,
            title=f"Request failure: {event.method} {event.route}",
            description=(
                event.exception_message
                or f"HTTP status code {event.status_code}"
            ),
            severity="high" if event.status_code >= 500 else "medium",
            status="open",
            first_seen_at=event.timestamp,
            last_seen_at=event.timestamp,
            details={
                "service_name": event.service_name,
                "route": event.route,
                "status_code": event.status_code,
            },
        )

        db.add(incident)
        db.commit()
        db.refresh(incident)

        event.incident_id = incident.id
        db.commit()

        incident_id = incident.id
        event_pk = event.id

        db.close()
        db = None

        await run_graphrag(incident_id, event_pk)

        return "failed: incident, graph and graphrag diagnosis saved"

    except Exception:
        if db is not None:
            db.rollback()
        raise

    finally:
        if db is not None:
            db.close()


async def run_worker():
    await setup_consumer_group()

    while True:
        messages = await redis_client.xreadgroup(
            groupname=GROUP,
            consumername=CONSUMER,
            streams={STREAM: ">"},
            count=1,
            block=5000,
        )

        for _, entries in messages:
            for message_id, data in entries:
                try:
                    result = await process_event(data["event_id"])
                    print(f"Event {data['event_id']}: {result}")

                    await redis_client.xack(
                        STREAM, GROUP, message_id
                    )

                except Exception as exc:
                    print(f"Failed to process {message_id}: {exc}")


if __name__ == "__main__":
    asyncio.run(run_worker())
