import uuid

from sqlalchemy.orm import Session

from ....database.models.graphrag_model import GraphEdge, GraphNode, IncidentEmbedding
from ....database.models.incident_model import Incident, IncidentDiagnosis

MIN_SIMILARITY = 0.6
GRAPH_BONUS = 0.15
TOP_K = 5


def similar_by_vector(db: Session, project_id, vector: list[float], exclude_id) -> list[tuple[str, float]]:
    rows = db.query(IncidentEmbedding).filter(IncidentEmbedding.project_id == project_id, IncidentEmbedding.incident_id != exclude_id).order_by(IncidentEmbedding.created_at.desc()).limit(2000).all()
    scored = [(str(r.incident_id), sum(a * b for a, b in zip(vector, r.vector))) for r in rows]
    return sorted([s for s in scored if s[1] >= MIN_SIMILARITY], key=lambda s: s[1], reverse=True)[:TOP_K]


def related_by_graph(db: Session, incident_node: GraphNode) -> dict[str, list[str]]:
    mine = {e.target_id for e in db.query(GraphEdge).filter(GraphEdge.source_id == incident_node.id)}
    if not mine: return {}
    edges = db.query(GraphEdge).filter(GraphEdge.target_id.in_(mine), GraphEdge.source_id != incident_node.id).all()
    node_ids = {e.source_id for e in edges} | mine
    nodes = {n.id: n for n in db.query(GraphNode).filter(GraphNode.id.in_(node_ids))}
    found: dict[str, list[str]] = {}
    for e in edges:
        if nodes[e.source_id].kind != "incident": continue
        found.setdefault(nodes[e.source_id].name, []).append(f"{nodes[e.target_id].kind}: {nodes[e.target_id].name}")
    return found


def rank(vector_hits: list[tuple[str, float]], graph_hits: dict[str, list[str]]) -> list[str]:
    scores = dict(vector_hits)
    for incident_id, facts in graph_hits.items(): scores[incident_id] = scores.get(incident_id, 0) + GRAPH_BONUS * len(facts)
    return sorted(scores, key=scores.get, reverse=True)[:TOP_K]


def load_cases(db: Session, ids: list[str], graph_hits: dict[str, list[str]]) -> list[dict]:
    cases = []
    for incident_id in ids:
        incident = db.get(Incident, uuid.UUID(incident_id))
        if incident is None: continue
        diagnosis = db.query(IncidentDiagnosis).filter(IncidentDiagnosis.incident_id == incident.id).order_by(IncidentDiagnosis.created_at.desc()).first()
        cases.append({
            "incident_id": incident_id,
            "title": incident.title,
            "status": incident.status,
            "description": incident.description,
            "summary": diagnosis.summary if diagnosis else None,
            "how_solved": diagnosis.howsolved if diagnosis else None,
            "shared_with_current": graph_hits.get(incident_id, []),
        })
    return cases
