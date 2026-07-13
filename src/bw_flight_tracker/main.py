import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from bw_flight_tracker.config import get_settings
from bw_flight_tracker.services.state import StateService

settings = get_settings()
app = FastAPI(title="BW Flight Tracker", version="0.1.0")
app.mount("/static", StaticFiles(directory="src/bw_flight_tracker/web/static"), name="static")
templates = Jinja2Templates(directory="src/bw_flight_tracker/web/templates")
state_service = StateService(settings)


@app.middleware("http")
async def security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; connect-src 'self'; "
        "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
        "frame-ancestors 'none'"
    )
    return response


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "live"}


@app.get("/health/ready")
async def ready() -> dict[str, object]:
    return {
        "status": "ready",
        "database": "not-required-phase-1",
        "provider": settings.aircraft_provider,
        "scheduler": settings.scheduler_enabled,
    }


@app.get("/api/v1/state")
async def api_state() -> dict[str, object]:
    return await state_service.current_state()


@app.get("/api/v1/events")
async def events(request: Request) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        while not await request.is_disconnected():
            yield f"event: state\ndata: {json.dumps(await state_service.current_state())}\n\n"
            for _ in range(10):
                if await request.is_disconnected():
                    return
                await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/v1/manual-selection")
async def manual_selection(payload: dict[str, str]) -> dict[str, str]:
    state_service.select_manual(payload["icao_hex"])
    return {"status": "manual"}


@app.delete("/api/v1/manual-selection")
async def clear_manual_selection() -> dict[str, str]:
    state_service.resume_auto()
    return {"status": "automatic"}
