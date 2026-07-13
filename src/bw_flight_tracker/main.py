import asyncio
import json
from collections.abc import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from bw_flight_tracker.config import get_settings
from bw_flight_tracker.services.state import StateService

SESSION_COOKIE = "bwft_session"
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
async def index(request: Request, response: Response) -> HTMLResponse:
    session_id = _session_id(request, response)
    return templates.TemplateResponse("index.html", {"request": request, "session_id": session_id})


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
async def api_state(request: Request, response: Response) -> dict[str, object]:
    return await state_service.current_state(_session_id(request, response))


@app.get("/api/v1/events")
async def events(request: Request, response: Response) -> StreamingResponse:
    session_id = _session_id(request, response)

    async def event_stream() -> AsyncIterator[str]:
        elapsed = 0
        while True:
            if elapsed >= settings.sse_heartbeat_seconds:
                yield "event: heartbeat\ndata: {}\n\n"
                elapsed = 0
            payload = json.dumps(await state_service.current_state(session_id))
            yield f"event: state\ndata: {payload}\n\n"
            await asyncio.sleep(10)
            elapsed += 10

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/v1/manual-selection")
async def manual_selection(
    request: Request,
    response: Response,
    payload: dict[str, str],
) -> dict[str, str]:
    state_service.select_manual(_session_id(request, response), payload["icao_hex"])
    return {"status": "manual"}


@app.delete("/api/v1/manual-selection")
async def clear_manual_selection(request: Request, response: Response) -> dict[str, str]:
    state_service.resume_auto(_session_id(request, response))
    return {"status": "automatic"}


def _session_id(request: Request, response: Response) -> str:
    session_id = request.cookies.get(SESSION_COOKIE)
    if isinstance(session_id, str):
        return session_id
    session_id = uuid4().hex
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        httponly=True,
        samesite="lax",
        secure=settings.app_env == "production",
        max_age=60 * 60 * 24,
    )
    return session_id
