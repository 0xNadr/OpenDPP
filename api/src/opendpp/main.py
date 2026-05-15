from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from opendpp import __version__
from opendpp.config import get_settings
from opendpp.routers import (
    anchor,
    chat,
    digital_link,
    dpp,
    qr,
    translate,
    validate_semantic,
    vc,
)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="OpenDPP — open-source reference Digital Product Passport API.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    app.include_router(dpp.router)
    app.include_router(qr.router)
    app.include_router(chat.router)
    app.include_router(translate.router)
    app.include_router(validate_semantic.router)
    app.include_router(vc.router)
    app.include_router(anchor.router)
    app.include_router(digital_link.router)

    return app


app = create_app()
