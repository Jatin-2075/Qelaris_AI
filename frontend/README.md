# RepoPilot Frontend

A React + TypeScript + Vite frontend for the RepoPilot/Sentinel observability platform.

## Run locally
1. Install Node.js 20+.
2. Copy `.env.example` to `.env`.
3. Run `npm install`
4. Run `npm run dev`

## API configuration
Set `VITE_API_BASE_URL` to your FastAPI server URL. Set `VITE_DEMO_MODE=false` to require live API responses.

Expected endpoints:
- `POST /auth/signup`
- `POST /auth/login`
- `GET/POST /projects`
- `GET/POST /api-keys`, `DELETE /api-keys/{key_id}`
- `GET /projects/{project_id}/events`
- `GET /projects/{project_id}/incidents`
- `GET /projects/{project_id}/incidents/{incident_id}/evidence`
- `PATCH /projects/{project_id}/incidents/{incident_id}/status`

## Backend integration note
The uploaded backend snapshot currently only includes `incident_router` in `app/main.py`; the auth, project and event routers need to be included there. The backend snapshot also has route/schema inconsistencies (for example login schema expects `username` while login handler reads `email`; project router imports `project_schema.py` but the uploaded file is named `project_schemas.py`; some model/database import paths differ). Fix those before setting `VITE_DEMO_MODE=false`.

The UI includes a demo mode so all screens can be explored without a live API. Demo data is clearly local/sample data and is not sent to your backend.
