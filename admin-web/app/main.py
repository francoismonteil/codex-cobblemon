from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from . import auth
from .actions import (
    ActionError,
    AppSettings,
    add_player,
    op_player,
    deop_player,
    get_status,
    read_logs,
    read_whitelist,
    remove_player,
    restart_container,
    run_backup,
    run_onboard,
    start_container,
    stop_container,
)
from .jobs import JobQueue
from .models import JobListResponse, JobResponse, LogResponse, OnboardRequest, PlayerActionRequest, PlayerAddRequest, StatusResponse, WhitelistResponse

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = AppSettings.from_env()
    if not settings.password:
        raise RuntimeError("MC_ADMIN_WEB_PASSWORD must be configured")
    if not settings.session_secret:
        raise RuntimeError("MC_ADMIN_WEB_SESSION_SECRET must be configured")

    app.state.settings = settings
    app.state.jobs = JobQueue(history_limit=settings.job_history)
    app.state.jobs.start()
    try:
        yield
    finally:
        app.state.jobs.stop()


app = FastAPI(title="Minecraft Admin Web", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=AppSettings.from_env().session_secret or "dev-session-secret",
    same_site="strict",
    https_only=AppSettings.from_env().cookie_secure,
    session_cookie="mc_admin_session",
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def get_settings(request: Request) -> AppSettings:
    return request.app.state.settings


def get_jobs(request: Request) -> JobQueue:
    return request.app.state.jobs


def require_api_login(request: Request) -> None:
    auth.require_login(request)


def enqueue_job(jobs: JobQueue, action: str, func) -> JobResponse:
    record = jobs.enqueue(action, func)
    return JobResponse(job_id=record.id, status=record.status)


@app.exception_handler(ActionError)
async def action_error_handler(_: Request, exc: ActionError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/login")
async def login_page(request: Request):
    redirect = auth.require_login_redirect(request)
    if redirect:
        return TEMPLATES.TemplateResponse(
            request=request,
            name="login.html",
            context=auth.inject_template_context(request, {"error": None, "password_missing": False}),
        )
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/login")
async def login_submit(request: Request, password: str = Form(default=""), settings: AppSettings = Depends(get_settings)):
    if auth.verify_password(password, settings.password):
        auth.login(request)
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    return TEMPLATES.TemplateResponse(
        request=request,
        name="login.html",
        context=auth.inject_template_context(request, {"error": "Mot de passe invalide", "password_missing": False}),
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@app.post("/logout")
async def logout(request: Request):
    auth.require_login(request)
    auth.verify_csrf(request)
    auth.logout(request)
    return JSONResponse({"status": "ok"})


@app.get("/")
async def dashboard(request: Request):
    redirect = auth.require_login_redirect(request)
    if redirect:
        return redirect
    return TEMPLATES.TemplateResponse(request=request, name="index.html", context=auth.inject_template_context(request))


@app.get("/api/status", response_model=StatusResponse)
async def api_status(
    request: Request,
    _: None = Depends(require_api_login),
    settings: AppSettings = Depends(get_settings),
):
    return get_status(settings.repo_root)


@app.get("/api/logs", response_model=LogResponse)
async def api_logs(
    request: Request,
    tail: int = Query(default=200, ge=50, le=1000),
    _: None = Depends(require_api_login),
):
    return LogResponse(lines=read_logs(tail=tail))


@app.get("/api/whitelist", response_model=WhitelistResponse)
async def api_whitelist(
    request: Request,
    _: None = Depends(require_api_login),
    settings: AppSettings = Depends(get_settings),
):
    return WhitelistResponse(names=read_whitelist(settings.repo_root))


@app.post("/api/players/add", response_model=JobResponse)
async def api_player_add(
    payload: PlayerAddRequest,
    request: Request,
    _: None = Depends(require_api_login),
    settings: AppSettings = Depends(get_settings),
    jobs: JobQueue = Depends(get_jobs),
):
    auth.verify_csrf(request)
    return enqueue_job(jobs, "player.add", lambda: add_player(settings.repo_root, payload.name, payload.op))


@app.post("/api/players/remove", response_model=JobResponse)
async def api_player_remove(
    payload: PlayerActionRequest,
    request: Request,
    _: None = Depends(require_api_login),
    settings: AppSettings = Depends(get_settings),
    jobs: JobQueue = Depends(get_jobs),
):
    auth.verify_csrf(request)
    return enqueue_job(jobs, "player.remove", lambda: remove_player(settings.repo_root, payload.name))


@app.post("/api/players/op", response_model=JobResponse)
async def api_player_op(
    payload: PlayerActionRequest,
    request: Request,
    _: None = Depends(require_api_login),
    settings: AppSettings = Depends(get_settings),
    jobs: JobQueue = Depends(get_jobs),
):
    auth.verify_csrf(request)
    return enqueue_job(jobs, "player.op", lambda: op_player(settings.repo_root, payload.name))


@app.post("/api/players/deop", response_model=JobResponse)
async def api_player_deop(
    payload: PlayerActionRequest,
    request: Request,
    _: None = Depends(require_api_login),
    settings: AppSettings = Depends(get_settings),
    jobs: JobQueue = Depends(get_jobs),
):
    auth.verify_csrf(request)
    return enqueue_job(jobs, "player.deop", lambda: deop_player(settings.repo_root, payload.name))


@app.post("/api/onboard", response_model=JobResponse)
async def api_onboard(
    payload: OnboardRequest,
    request: Request,
    _: None = Depends(require_api_login),
    settings: AppSettings = Depends(get_settings),
    jobs: JobQueue = Depends(get_jobs),
):
    auth.verify_csrf(request)
    return enqueue_job(jobs, "player.onboard", lambda: run_onboard(settings.repo_root, payload.name, payload.op))


@app.post("/api/actions/start", response_model=JobResponse)
async def api_action_start(
    request: Request,
    _: None = Depends(require_api_login),
    jobs: JobQueue = Depends(get_jobs),
):
    auth.verify_csrf(request)
    return enqueue_job(jobs, "server.start", start_container)


@app.post("/api/actions/stop", response_model=JobResponse)
async def api_action_stop(
    request: Request,
    _: None = Depends(require_api_login),
    jobs: JobQueue = Depends(get_jobs),
):
    auth.verify_csrf(request)
    return enqueue_job(jobs, "server.stop", stop_container)


@app.post("/api/actions/restart", response_model=JobResponse)
async def api_action_restart(
    request: Request,
    _: None = Depends(require_api_login),
    jobs: JobQueue = Depends(get_jobs),
):
    auth.verify_csrf(request)
    return enqueue_job(jobs, "server.restart", restart_container)


@app.post("/api/actions/backup", response_model=JobResponse)
async def api_action_backup(
    request: Request,
    _: None = Depends(require_api_login),
    settings: AppSettings = Depends(get_settings),
    jobs: JobQueue = Depends(get_jobs),
):
    auth.verify_csrf(request)
    return enqueue_job(jobs, "server.backup", lambda: run_backup(settings.repo_root))


@app.get("/api/jobs", response_model=JobListResponse)
async def api_jobs(
    request: Request,
    _: None = Depends(require_api_login),
    jobs: JobQueue = Depends(get_jobs),
):
    return JobListResponse(jobs=[record.to_dict() for record in jobs.list()])


@app.get("/api/jobs/{job_id}")
async def api_job_details(
    job_id: str,
    request: Request,
    _: None = Depends(require_api_login),
    jobs: JobQueue = Depends(get_jobs),
):
    record = jobs.get(job_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return record.to_dict()
