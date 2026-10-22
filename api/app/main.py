from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from .config import Settings, get_settings
from .db.repos import DatabaseUnavailable
from .routers import calculate, health, scenarios
from .schemas.errors import ApiError, ErrorItem, ErrorResponse

API_PREFIX = "/api/v1"


def _errors(status: int, items: list[ErrorItem]) -> JSONResponse:
    return JSONResponse(status_code=status, content=ErrorResponse(errors=items).model_dump())


def _field_name(loc: tuple[object, ...]) -> str | None:
    # loc vyzerá ako ("body", "price") alebo ("header", "x-log")
    return str(loc[-1]) if len(loc) > 1 else None


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Hypotekárna kalkulačka API", version="0.1.0")

    app.state.limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "X-Client-Id", "X-Log", "X-Log-Source"],
        expose_headers=["Content-Disposition"],
    )

    @app.exception_handler(ApiError)
    def api_error(_: Request, exc: ApiError) -> JSONResponse:
        return _errors(exc.status, exc.items)

    @app.exception_handler(RequestValidationError)
    def request_invalid(_: Request, exc: RequestValidationError) -> JSONResponse:
        items = [
            ErrorItem(field=_field_name(tuple(e["loc"])), code="invalid", message=e["msg"])
            for e in exc.errors()
        ]
        return _errors(422, items)

    @app.exception_handler(DatabaseUnavailable)
    def db_unavailable(_: Request, exc: DatabaseUnavailable) -> JSONResponse:
        return _errors(
            503, [ErrorItem(code="db_unavailable", message="Databáza je dočasne nedostupná.")]
        )

    @app.exception_handler(RateLimitExceeded)
    def rate_limited(_: Request, exc: RateLimitExceeded) -> JSONResponse:
        return _errors(429, [ErrorItem(code="rate_limited", message="Príliš veľa požiadaviek.")])

    app.include_router(health.router, prefix=API_PREFIX)
    app.include_router(calculate.router, prefix=API_PREFIX)
    app.include_router(scenarios.router, prefix=API_PREFIX)
    return app


app = create_app()
