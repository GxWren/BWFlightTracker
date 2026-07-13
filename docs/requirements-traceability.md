# Requirements Traceability

| Requirement | Phase | Status | Implementation / tests |
| --- | --- | --- | --- |
| DATA-001 | 2 | Deferred | Provider boundary exists with mock provider; live Airplanes.live pending. |
| DATA-002 | 2 | Partial | `AircraftState` normalizes callsign/ICAO; live payload adapter pending. |
| DATA-010 | 3 | Deferred | Mock enrichment exists; ADSBDB adapter pending. |
| DATA-011 | 1 | Partial | `classify_commercial` has baseline airline-prefix heuristic; configurable data source pending. |
| DATA-020 | 4 | Deferred | Address/coordinate settings UI pending. |
| GEO-001 | 1 | Implemented | `src/bw_flight_tracker/domain/geo.py`, `tests/test_geo.py`. |
| GEO-002 | 1 | Implemented | `src/bw_flight_tracker/domain/geo.py`, `tests/test_geo.py`. |
| GEO-003 | 1 | Partial | Closest-approach-derived state exists; rolling distance smoothing remains pending. |
| GEO-004 | 1 | Implemented | `project_closest_approach`, `tests/test_geo.py`. |
| SEL-001 | 1 | Implemented for mock slice | `eligible_candidates`, stale-position filtering, `tests/test_selection.py`, `tests/test_state_service.py`. |
| SEL-002 | 1 | Implemented baseline | Weighted score in `selection.py`; diagnostics detail still pending. |
| SEL-003 | 1 | Implemented | `PrimarySelectionEngine` hold time, switch threshold, challenger cycles; `tests/test_primary_selection.py`. |
| SEL-004 | 1 | Implemented for mock slice | Session-scoped manual override with expiry, resume endpoint, and UI control; `tests/test_state_service.py`. |
| UI-001 | 1 | Implemented | Responsive flight-board-style template and CSS. |
| UI-002 | 1 | Implemented | Local-storage theme toggle. |
| UI-010 | 1 | Implemented for available mock data | Primary card renders ten requested categories when known. |
| API-001 | 1 | Implemented | Public serializer omits exact coordinates; `tests/test_api.py`. |
| API-002 | 1 | Partial | SSE sends full state and heartbeat; robust browser fallback exists; proxy-level testing pending. |
| OPS-003 | 2 | Deferred | Live-provider circuit breaker and retry controls pending. |
| DEV-001 | 0 | Implemented | README Windows workflow. |
| DEV-002 | 0 | Implemented skeleton | Docker Compose app and MySQL services. |
| DEV-003 | 0 | Implemented skeleton | README, docs, ADRs, pyproject, CI. |
| TEST-001 | 0-5 | Partial | Ruff and pure unit tests pass locally; full FastAPI/mypy gate requires installable dependencies. |
| CI-001 | 0 | Implemented skeleton | `.github/workflows/ci.yml`. |
| CI-002 | 0 | Partial | App version is `0.1.0`; build commit injection pending. |
