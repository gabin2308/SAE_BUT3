from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware
import asyncio
from app.settings import settings
from app.database.initdb import init_db_pool, close_db_pool
from app.controllers import register_all
from app.utils.exception_handlers import enregistrer_handlers
from app.utils.limiter import limiter
import contextlib
from app.utils.taches_periodiques import demarrer


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_pool()
    tache = demarrer()
    try:
        yield
    finally:
        tache.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await tache
        close_db_pool()

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    app.state.limiter = limiter
    # Sans ce middleware, les default_limits de limiter.py (1000/jour, 300/heure)
    # ne s'appliquent pas : seuls les @limiter.limit explicites des routes comptent.
    app.add_middleware(SlowAPIMiddleware)

    # -- CORS (équivalent flask_cors.CORS) ---
    # Ajouté APRÈS SlowAPIMiddleware : le dernier middleware ajouté est le plus externe,
    # donc les réponses 429 portent bien les en-têtes CORS.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
        expose_headers=["Content-Type", "X-CSRF-Token"],
    )

    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.ENV == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # Handlers d'exceptions métier + dépassement de quota (429), centralisés
    enregistrer_handlers(app)

    # --- Enregistrement des routes ---
    register_all(app, url_prefix="/api")

    # --- Debug : liste des routes enregistrées ---
    if settings.DEBUG:
        print("\n--- ROUTES ENREGISTRÉES ---")
        for path, methods in app.openapi()["paths"].items():
            print(f"Route : {path:30s} | {', '.join(m.upper() for m in methods)}")
        print("---------------------------\n")

    return app