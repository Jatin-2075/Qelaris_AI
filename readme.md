import secrets
import hashlib

api = "sn_" + secrets.token_urlsafe(32)
key_prefix = api[:10]
key_hash = hashlib.sha256(api.encode()).hexdigest()


|sentinel/
│
├── sdk/
│   ├── sentinel_sdk/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── events.py
│   │   └── middleware.py
│   ├── tests/
│   │   └── test_middleware.py
│   ├── pyproject.toml
│   └── README.md
│
├── ingestion_backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── ingestion.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   └── telemetry_service.py
│   │   └── pipeline/
│   │       ├── worker.py
│   │       ├── processor.py
│   │       ├── metrics.py
│   │       └── anomaly_detection.py
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
│
├── platform_backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── projects.py
│   │   │   ├── api_keys.py
│   │   │   ├── dashboard.py
│   │   │   └── incidents.py
│   │   ├── services/
│   │   │   └── auth_service.py
│   │   └── websocket/
│   │       └── manager.py
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
│
├── database/
│   ├── __init__.py
│   ├── DataBase.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── auth_user.py
│   │   ├── project_data.py
│   │   ├── api_key.py
│   │   ├── event.py
│   │   ├── metrics.py
│   │   ├── incident.py
│   │   ├── incident_evidence.py
│   │   └── incident_diagnosis.py
│   └── migrations/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml
├── .gitignore
└── README.md