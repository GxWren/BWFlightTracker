# Architecture

The application uses FastAPI with server-rendered Jinja2 templates, vanilla JavaScript, and JSON/SSE endpoints. Provider data is normalized into domain models before scoring or serialization. Geographic calculations and selection are pure Python modules with unit coverage. Phase 1 uses deterministic mock providers only; live Airplanes.live and ADSBDB adapters are deferred to later phases.
