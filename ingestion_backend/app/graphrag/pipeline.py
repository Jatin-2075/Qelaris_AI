from ....database.database import SessionLocal
from ....database.models.event_model import Event
from ....database.models.graphrag_model import IncidentEmbedding
from ....database.models.incident_model import Incident, IncidentDiagnosis
from ..setting import settings
from .graph import add_incident
from .llm import embed, ask_json
from .prompt import build_prompt
from .retrieve import similar_by_vector, related_by_graph, rank, load_cases


def event_to_dict(event: Event) -> dict:
    return {
        "service_name": event.service_name,
        "environment": event.environment,
        "method": event.method,
        "route": event.route,
        "status_code": event.status_code,
        "duration_ms": event.duration_ms,
        "exception_type": event.exception_type,
        "exception_message": event.exception_message,
    }


def add_suggestion(description: str, diagnosis: dict, cases: list[dict]) -> str:
    lines = [description, "", f"Suggestion: {diagnosis['summary']}"]
    if diagnosis["recommendations"]: lines.append(f"Next step: {diagnosis['recommendations'][0]}")
    fix = next((c["how_solved"] for c in cases if c["how_solved"]), None)
    if fix: lines.append(f"Similar past fix: {fix}")
    return "\n".join(lines)


async def run_graphrag(incident_id, event_id) -> dict:
    with SessionLocal() as db:
        incident = db.get(Incident, incident_id)
        event = db.get(Event, event_id)
        project_id = incident.project_id
        event_data = event_to_dict(event)
        query_text = f"{incident.title}\n{incident.description}\n{event.exception_type or ''}"

    vector = await embed(query_text)

    with SessionLocal() as db:
        incident = db.get(Incident, incident_id)
        event = db.get(Event, event_id)
        incident_node = add_incident(db, incident, event)
        vector_hits = similar_by_vector(db, project_id, vector, incident_id)
        graph_hits = related_by_graph(db, incident_node)
        cases = load_cases(db, rank(vector_hits, graph_hits), graph_hits)
        db.merge(IncidentEmbedding(incident_id=incident_id, project_id=project_id, vector=vector))
        db.commit()

    diagnosis = await ask_json(build_prompt(event_data, cases))
    if not {"summary", "possible_causes", "recommendations"}.issubset(diagnosis): raise ValueError("Gemini returned an invalid diagnosis format")

    with SessionLocal() as db:
        incident = db.get(Incident, incident_id)
        incident.description = add_suggestion(incident.description, diagnosis, cases)
        incident.details = {**incident.details, "graphrag": {"similar_incident_ids": [c["incident_id"] for c in cases]}}
        db.add(IncidentDiagnosis(incident_id=incident_id, summary=diagnosis["summary"], possible_causes=diagnosis["possible_causes"], recommendations=diagnosis["recommendations"], model_name=settings.GEMINI_MODEL))
        db.commit()

    return diagnosis
