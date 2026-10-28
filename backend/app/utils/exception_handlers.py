from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.utils.exceptions import (
    AccesRefuseError,
    ConflitError,
    IdentifiantsInvalidesError,
    RessourceIntrouvableError,
    ValidationError,
    JetonExpireError,
)


def enregistrer_handlers(app: FastAPI) -> None:
    """Handlers d'exceptions métier globaux : évite un try/except répété dans chaque route.

    Les handlers sont résolus par la hiérarchie de classes :
    ConsentementRequisError -> ValidationError, EmailDejaUtiliseError -> ConflitError,
    UtilisateurIntrouvableError -> RessourceIntrouvableError.
    """

    @app.exception_handler(ValidationError)
    async def _validation(request: Request, exc: ValidationError):
        return JSONResponse(status_code=400, content={"detail": exc.erreurs})

    @app.exception_handler(IdentifiantsInvalidesError)
    async def _identifiants(request: Request, exc: IdentifiantsInvalidesError):
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(AccesRefuseError)
    async def _acces_refuse(request: Request, exc: AccesRefuseError):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(RessourceIntrouvableError)
    async def _introuvable(request: Request, exc: RessourceIntrouvableError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflitError)
    async def _conflit(request: Request, exc: ConflitError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(JetonExpireError)
    async def _jeton_expire(request: Request, exc: JetonExpireError):
        # La page « lien expiré » (maquette 08) propose d'en demander un nouveau
        return JSONResponse(status_code=410, content={"detail": str(exc)})
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)