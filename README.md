# BW Flight Tracker

BW Flight Tracker is a Python 3.12+ FastAPI web application for identifying aircraft passing near one configured location. Phase 0/1 currently provides the project structure, mock aircraft vertical slice, responsive flight-board UI, sanitized JSON state, SSE updates, and health endpoints.

## Local Windows PowerShell workflow

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn bw_flight_tracker.main:app --reload
```

Open <http://localhost:8000>. Use `AIRCRAFT_PROVIDER=mock` until Phase 2 live provider work begins. Set `MOCK_SCENARIO` to exercise the deterministic scenarios documented in `docs/mock-scenarios.md`.

To test live telemetry, set `AIRCRAFT_PROVIDER=airplanes_live` in `.env` and restart Uvicorn. The app calls Airplanes.live's point endpoint near the configured home coordinates, then applies the local distance, freshness, altitude, and commercial-aircraft filters before rendering public state.

## Docker workflow

```bash
docker compose up --build
```

The compose file runs the app in mock-provider mode and includes a MySQL service for later repository integration.

## Quality gate

```bash
ruff format --check .
ruff check .
mypy src
pytest
```

## Privacy

Public HTML and `/api/v1/state` expose distances, bearings, altitude, speed, and route details, but not the configured address or exact home/aircraft coordinates.
