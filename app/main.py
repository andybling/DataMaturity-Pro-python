"""Point d'entrée de l'application DataMaturity Pro."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config import BASE_DIR, settings
from app.database import init_db
from app.routers import admin, api, checkout, public
from app.templating import render

logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("datamaturity")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    logger.info("Base initialisée (%s)", settings.database_url.split("://")[0])
    logger.info(
        "Paiements — Stripe: %s · CinetPay: %s",
        "actif" if settings.stripe_enabled else "inactif",
        "actif" if settings.cinetpay_enabled else "inactif",
    )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.brand_name,
        description="Plateforme de diagnostic de maturité data — API et interface web.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="dmp_session",
        https_only=settings.is_production,
        same_site="lax",
        max_age=60 * 60 * 12,
    )

    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    app.include_router(public.router)
    app.include_router(checkout.router)
    app.include_router(admin.router)
    app.include_router(api.router)

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict:
        return {"status": "ok", "env": settings.app_env}

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        if exc.status_code in {404, 403, 410}:
            return render(
                request,
                "error.html",
                {"code": exc.status_code, "message": exc.detail},
                status_code=exc.status_code,
            )
        return render(
            request,
            "error.html",
            {"code": exc.status_code, "message": exc.detail},
            status_code=exc.status_code,
        )

    return app


app = create_app()
