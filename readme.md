<div align="center">

# Qelaris

### See the signal. Trace the cause. Understand the system.

**AI-powered developer observability for teams that want more than dashboards.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Data-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-Streams-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Status](https://img.shields.io/badge/Status-In%20Development-8B5CF6?style=for-the-badge)](#-project-status)

<br/>

<!-- Replace this placeholder with a real optimized GIF committed to the repository. -->
<img src="docs/assets/repopilot-demo.gif" alt="RepoPilot demo: telemetry flows into anomaly detection, historical incident retrieval, and AI-assisted investigation" width="900" />

<sub>Demo animation placeholder — add your GIF at <code>docs/assets/repopilot-demo.gif</code>.</sub>

<br/>

[Overview](#-overview) · [Architecture](#-architecture) · [Features](#-core-capabilities) · [Quick Start](#-quick-start) · [Roadmap](#-roadmap)

</div>

---

## ✦ Overview

**RepoPilot** is a developer-observability platform designed to turn raw application telemetry into actionable incident intelligence.

A lightweight SDK captures request-level signals from an application. The ingestion service validates and stores events, then publishes work to Redis Streams. Background workers aggregate telemetry, identify abnormal behavior, and prepare incidents for investigation. The planned RAG pipeline retrieves relevant historical incidents so an AI analysis agent can generate evidence-backed hypotheses and debugging recommendations.

> **The goal:** move from *“something is wrong”* to *“here is what may be wrong, why we think so, and what to investigate next.”*

### The idea

```text
Application → SDK → Ingestion API → PostgreSQL + Redis Streams
                                      ↓
                              Background Worker
                                      ↓
                         Metrics + Anomaly Detection
                                      ↓
                               Incident Record
                                      ↓
                         RAG → AI Investigation
                                      ↓
                         Evidence + Recommendations
                                      ↓
                               Live Dashboard
```

## ◈ Core capabilities

### Telemetry collection
- Python SDK for FastAPI/Starlette applications.
- Capture request duration, route template, response status, and exception type.
- Send structured telemetry to the ingestion API using HTTPX.
- Keep telemetry focused on useful operational signals.

### Event ingestion and processing
- FastAPI ingestion service authenticates SDK requests using project API keys.
- Validate incoming telemetry before storing it.
- Persist raw events in PostgreSQL.
- Enqueue event identifiers into a Redis Stream.
- Process events asynchronously with Redis Consumer Groups and bounded batches.

### Metrics and anomaly detection
- Aggregate request counts, error rates, and p95 latency over time windows.
- Detect candidate incidents such as:
  - **High latency** compared with a project's or route's baseline.
  - **Application errors** such as HTTP 5xx responses and unhandled exceptions.
  - **Error-rate spikes** across a rolling time window.
  - **Resource or dependency saturation** when those signals are instrumented.
- Group related failures so one ongoing problem does not create a separate incident for every request.

### RAG-powered incident investigation *(planned)*
- Generate embeddings for searchable historical incident content.
- Store and search vectors with PostgreSQL + `pgvector`.
- Retrieve similar incidents and relevant evidence for a new incident.
- Pass retrieved context alongside current telemetry to the AI analysis agent.
- Save the resulting analysis separately from raw telemetry.

### AI incident analysis *(planned)*
The investigation agent is intended to produce:
- Root-cause hypotheses, not unverified claims.
- Supporting telemetry and historical evidence.
- Relevant previous incidents.
- Recommended debugging steps and possible fixes.
- A confidence estimate with clear limitations.

### Dashboard and project management
- Project and API-key management.
- Incident timeline, severity, and lifecycle status.
- Metrics and trends for latency, errors, and request volume.
- AI analysis and supporting evidence surfaced alongside each incident.

> Feature availability changes as development progresses. See [Project Status](#-project-status) for the current implementation boundary.

## ⌘ Architecture

RepoPilot is organized around separate ingestion, analysis, and dashboard responsibilities.

```mermaid
flowchart TD
    APP["Instrumented Application"] --> SDK["Python SDK"]
    SDK --> INGEST["Ingestion API · FastAPI"]
    INGEST --> DB[("PostgreSQL")]
    INGEST --> STREAM[("Redis Stream")]
    STREAM --> WORKER["Background Worker"]
    WORKER --> METRICS["Windowed Metrics"]
    METRICS --> DETECT["Anomaly / Incident Detection"]
    DETECT --> INCIDENT["Incident Records"]
    INCIDENT --> RETRIEVAL["RAG Retrieval · planned"]
    RETRIEVAL --> AGENT["AI Investigation Agent · planned"]
    AGENT --> EVIDENCE[("Incident Evidence · planned")]
    DB --> DASHAPI["Dashboard / Platform API"]
    INCIDENT --> DASHAPI
    EVIDENCE --> DASHAPI
    DASHAPI --> UI["Web Dashboard"]
```

### Event processing lifecycle

1. **Capture:** the SDK observes a request and builds a structured telemetry event.
2. **Ingest:** the ingestion API authenticates the project key, validates the event, and stores it.
3. **Enqueue:** the event ID and project context are published to Redis Streams.
4. **Process:** a background worker consumes events in batches and calculates windowed metrics.
5. **Detect:** detection rules flag abnormal latency, errors, or error-rate changes.
6. **Investigate:** the planned RAG pipeline retrieves relevant historical incidents and supplies them to the AI agent.
7. **Persist and display:** analysis evidence is saved against the incident and surfaced in the dashboard.

### Why Redis Streams?

Redis Streams provides a queue-like processing layer with consumer groups, batching, and acknowledgement semantics. PostgreSQL remains the durable source of truth for events and incident records; Redis helps coordinate asynchronous processing.

### Why PostgreSQL + pgvector?

PostgreSQL keeps operational records and searchable incident metadata in one system. `pgvector` can add similarity search over embeddings, while ordinary SQL filters restrict retrieval to the correct project and relevant incident types.

## ⛭ Technology stack

| Layer | Technology | Responsibility |
|---|---|---|
| SDK | Python, HTTPX | Capture and transmit telemetry |
| Ingestion API | FastAPI | Authenticate, validate, and store events |
| Platform API | FastAPI | Users, projects, API keys, dashboard APIs |
| Durable storage | PostgreSQL, SQLAlchemy | Events, metrics, incidents, evidence |
| Queue / batching | Redis Streams | Asynchronous event processing |
| Vector retrieval | pgvector *(planned)* | Similar-incident search |
| Embeddings | Embedding model *(to be configured)* | Convert incident text to vectors |
| AI investigation | LLM-backed agent *(planned)* | Explain evidence and suggest next steps |
| Frontend | Existing web dashboard | Visualize telemetry and incidents |

## 🚀 Quick start

> **Before you begin:** this README describes the intended project architecture. The exact repository layout, environment variable names, migration commands, and service startup commands may differ in your current branch. Confirm them against the actual code before running in production.

### Prerequisites

- Python 3.11 or newer
- PostgreSQL
- Redis with Streams support
- Git
- Optional for the planned RAG layer: PostgreSQL `pgvector` extension and credentials for the chosen embedding/LLM provider

### 1. Clone the repository

```bash
git clone <YOUR_REPO_URL>
cd <YOUR_REPO_DIRECTORY>
```

Replace the placeholders with your repository URL and directory name.

### 2. Create a virtual environment

**Linux / macOS**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

Use the dependency file already maintained by your project:

```bash
pip install -r requirements.txt
```

If the repository uses separate requirements files for the SDK, ingestion service, or dashboard backend, install the appropriate one for the service you are running.

### 4. Configure environment variables

Create a local `.env` file from the project's example if one exists. Typical configuration categories include:

```dotenv
# Database
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/repopilot

# Redis
REDIS_URL=redis://localhost:6379/0

# Application security
# Generate a strong, unique secret locally. Never commit real secrets.
SECRET_KEY=replace-with-a-local-secret
```

Use the **actual names expected by your application**. These are illustrative examples, not a claim that every variable is already wired into the code.

For the planned RAG/AI integration, configure the selected provider's API key and embedding model only in the backend environment. Do not expose provider secrets in frontend variables or commit them to Git.

### 5. Start dependencies

Start PostgreSQL and Redis using your local installation or the deployment setup provided by the repository. Ensure both are reachable from the backend.

If your PostgreSQL installation supports `pgvector`, enable it only after installing the extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

This step is needed for the planned vector-search functionality, not for ordinary telemetry ingestion.

### 6. Apply database migrations

If the repository uses Alembic, apply its existing migrations:

```bash
alembic upgrade head
```

Run this only if Alembic is configured in the relevant backend. Otherwise, follow the project's existing schema initialization process.

### 7. Run the backend

Start the relevant FastAPI application using its actual import path. For example, if its entry point is `main.py`:

```bash
uvicorn main:app --reload
```

For a multi-service setup, start the ingestion API, platform/dashboard API, and background worker according to their respective entry points. Do not assume they share one `main.py`.

### 8. Instrument an application

Install the SDK from the repository using the project's documented installation method, configure the ingestion URL and project API key, then add the middleware to a supported FastAPI/Starlette application. See the SDK package documentation for its exact API.

## 🧭 Incident detection model

RepoPilot's initial detection rules focus on signals that can be derived from request telemetry.

| Signal | Example detection strategy |
|---|---|
| High latency | Compare route/project latency against a baseline or rolling p95 |
| HTTP errors / exceptions | Record 5xx responses and unhandled exceptions |
| Error-rate spike | Compare failures over a time window with a baseline or threshold |
| Resource overload | Add CPU, memory, queue, or connection-pool metrics when instrumented |
| Dependency failure | Detect repeated failures/timeouts for databases or external services when observed |

**Detection is not diagnosis.** A rule can identify suspicious behavior; the investigation pipeline gathers context and proposes explanations. Thresholds should be tuned to traffic patterns, and a single failed request should not automatically become a high-severity incident.

## 🧠 RAG and AI investigation

The planned retrieval flow:

```text
New incident
    ↓
Build a searchable incident description
    ↓
Generate an embedding
    ↓
Search historical incident vectors
    ↓
Filter by project and relevance
    ↓
Provide current telemetry + retrieved evidence to the agent
    ↓
Generate hypotheses and recommended investigation steps
    ↓
Persist a versioned analysis in incident_evidence
```

### Evidence design principles

- Keep raw telemetry, incident state, and AI-generated evidence as distinct records.
- Include the project boundary in retrieval filters to prevent cross-project data leakage.
- Save the IDs of retrieved incidents so an analysis can be traced back to its context.
- Treat AI explanations as hypotheses until corroborated by telemetry or a human.
- Store analysis timestamps and model/version metadata to support debugging and reproducibility.
- Re-index an incident when its searchable content changes; avoid embedding unchanged content repeatedly.

## 🔐 Security and reliability

- Keep API keys and model-provider credentials server-side.
- Authenticate SDKs with project-scoped keys.
- Validate payload sizes and field types at ingestion.
- Enforce project-level authorization on every dashboard and retrieval query.
- Avoid storing request bodies, credentials, authorization headers, or other sensitive data unless explicitly required and safely redacted.
- Use bounded batches, retry policies, and observable worker failures.
- Make incident creation and evidence writes idempotent where possible.
- Never automatically execute AI-recommended fixes against production systems without explicit controls and authorization.

## 🗺️ Roadmap

- [x] Python telemetry SDK foundation
- [x] FastAPI ingestion architecture
- [x] PostgreSQL persistence and Redis Stream processing design
- [x] Windowed request metrics design
- [ ] Finalize incident detection thresholds and grouping
- [ ] Implement incident lifecycle and deduplication
- [ ] Add PostgreSQL `pgvector` schema and embedding pipeline
- [ ] Implement project-scoped similar-incident retrieval
- [ ] Integrate the AI investigation agent
- [ ] Persist structured, traceable incident evidence
- [ ] Surface incident investigation in the dashboard
- [ ] Add end-to-end tests, load tests, and deployment hardening

> Update the checkboxes to reflect the current branch. Items above describe the known project direction; they are not a CI-verified release checklist.

## 📊 Project status

RepoPilot is under active development. The architecture separates telemetry ingestion, asynchronous processing, incident detection, and dashboard functionality. RAG-powered retrieval and AI incident investigation are planned additions and should be considered incomplete until implemented and tested end to end.

## 🤝 Contributing

Contributions, bug reports, and architecture feedback are welcome.

1. Open an issue describing the problem or proposed improvement.
2. Keep pull requests focused and include tests where practical.
3. Document configuration changes and migration requirements.
4. Never include real credentials, production telemetry, or customer secrets in issues or commits.

Add your preferred contribution guidelines and license before accepting external contributions.

## 📄 License

No license has been specified here. Add a `LICENSE` file and update this section before publicly distributing the project.

---

<div align="center">

**RepoPilot**  
*From telemetry to understanding.*

<sub>Built for developers who want to understand not only what failed, but what to investigate next.</sub>

</div>
