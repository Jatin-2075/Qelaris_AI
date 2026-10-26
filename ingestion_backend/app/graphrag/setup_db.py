from ....database.database import engine, Base
from ....database.models.graphrag_model import GraphEdge, GraphNode, IncidentEmbedding

if __name__ == "__main__":
    Base.metadata.create_all(engine, tables=[GraphNode.__table__, GraphEdge.__table__, IncidentEmbedding.__table__])
    print("graphrag tables created")
