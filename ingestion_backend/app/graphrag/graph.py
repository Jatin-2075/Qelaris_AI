from sqlalchemy.orm import Session

from ....database.models.event_model import Event
from ....database.models.graphrag_model import GraphEdge, GraphNode
from ....database.models.incident_model import Incident


def get_node(db: Session, project_id, kind: str, name: str) -> GraphNode:
    name = name[:255]
    node = db.query(GraphNode).filter(GraphNode.project_id == project_id, GraphNode.kind == kind, GraphNode.name == name).first()
    if node: return node
    node = GraphNode(project_id=project_id, kind=kind, name=name)
    db.add(node)
    db.flush()
    return node


def link(db: Session, project_id, source: GraphNode, target: GraphNode, relation: str) -> None:
    found = db.query(GraphEdge).filter(GraphEdge.source_id == source.id, GraphEdge.target_id == target.id, GraphEdge.relation == relation).first()
    if not found: db.add(GraphEdge(project_id=project_id, source_id=source.id, target_id=target.id, relation=relation))


def add_incident(db: Session, incident: Incident, event: Event) -> GraphNode:
    pid = incident.project_id
    incident_node = get_node(db, pid, "incident", str(incident.id))
    service = get_node(db, pid, "service", event.service_name)
    route = get_node(db, pid, "route", f"{event.method} {event.route}")
    error = get_node(db, pid, "error", event.exception_type or f"HTTP {event.status_code}")
    link(db, pid, incident_node, service, "AFFECTS")
    link(db, pid, incident_node, route, "ON_ROUTE")
    link(db, pid, incident_node, error, "HAS_ERROR")
    link(db, pid, service, route, "HAS_ROUTE")
    db.flush()
    return incident_node
