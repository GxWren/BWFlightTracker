# Requirements Traceability

| Requirement | Phase | Status | Implementation / tests |
| --- | --- | --- | --- |
| DATA-001 | 2 | Deferred | Provider boundary exists with mock provider; live Airplanes.live pending. |
| DATA-002 | 2 | Partial | `AircraftState` normalizes callsign/ICAO; live payload adapter pending. |
| GEO-001 | 1 | Implemented | `src/bw_flight_tracker/domain/geo.py`, `tests/test_geo.py`. |
| GEO-002 | 1 | Implemented | `src/bw_flight_tracker/domain/geo.py`, `tests/test_geo.py`. |
| GEO-004 | 1 | Implemented | `project_closest_approach`, `tests/test_geo.py`. |
| SEL-001 | 1 | Implemented for mock slice | `eligible_candidates`, `tests/test_selection.py`. |
| SEL-002 | 1 | Implemented baseline | Weighted score in `selection.py`. |
| SEL-003 | 1 | Deferred | Full hysteresis engine planned after persisted polling loop. |
| SEL-004 | 1 | Partial | Manual selection endpoints and UI; session scoping pending. |
| UI-001 | 1 | Implemented | Responsive flight-board-style template and CSS. |
| UI-002 | 1 | Implemented | Local-storage theme toggle. |
| UI-010 | 1 | Implemented for available mock data | Primary card renders ten requested categories when known. |
| API-001 | 1 | Implemented | Public serializer omits exact coordinates; tested. |
| API-002 | 1 | Partial | SSE sends full state; heartbeat/reconnect hardening pending. |
| DEV-001 | 0 | Implemented | README Windows workflow. |
| DEV-002 | 0 | Implemented skeleton | Docker Compose app and MySQL services. |
| DEV-003 | 0 | Implemented skeleton | README, docs, ADRs, pyproject, CI. |
| CI-001 | 0 | Implemented skeleton | `.github/workflows/ci.yml`. |
