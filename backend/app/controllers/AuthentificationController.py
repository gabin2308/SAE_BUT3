import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status

from app.settings import settings
from app.utils.limiter import limiter
from app.models.utilisateur.Utilisateur import Utilisateur
from app.utils.auth import get_current_utilisateur
from app.utils.dependencies import auth_service
from app.models.utilisateur.UtilisateurSchema import (
    ChangerMotDePasse,
    LoginOut,
    MessageOut,
    UtilisateurLogin,
    UtilisateurOut,
)
from app.utils.jwt_utils import (
    ACCESS_TOKEN_DUREE,
    REFRESH_TOKEN_DUREE,
    decoder_token,
)


class AuthentificationController:

    def __init__(self):
        self.router = APIRouter(prefix="/auth", tags=["Authentification"])
        # Service partagé, assemblé une seule fois dans app/utils/dependencies.py.
        self.auth_service = auth_service
        self._secure = settings.ENV == "production"
        self._register_routes()

    # ------------------------------------------------------------------
    # Cookies : les JWT ne transitent jamais en JSON, seulement via cookies
    # HttpOnly. Le csrf_token est lisible par le JS (double-submit cookie).
    # ------------------------------------------------------------------
    def _poser_cookies(self, response: Response, access_token: str, refresh_token: str, csrf_token: str) -> None:
        cookie_kwargs = dict(httponly=True, secure=self._secure, samesite="lax", path="/")
        response.set_cookie(
            "access_token", access_token,
            max_age=int(ACCESS_TOKEN_DUREE.total_seconds()), **cookie_kwargs,
        )
        response.set_cookie(
            "refresh_token", refresh_token,
            max_age=int(REFRESH_TOKEN_DUREE.total_seconds()), **cookie_kwargs,
        )
        response.set_cookie(
            "csrf_token", csrf_token,
            max_age=int(ACCESS_TOKEN_DUREE.total_seconds()),
            path="/", httponly=False, secure=self._secure, samesite="lax",
        )

    def _supprimer_cookies(self, response: Response) -> None:
        for nom in ("access_token", "refresh_token", "csrf_token"):
            response.delete_cookie(nom, path="/", secure=self._secure, samesite="lax")

    # ------------------------------------------------------------------
    # Routes
    # Aucun try/except ici : IdentifiantsInvalidesError, ValidationError,
    # UtilisateurIntrouvableError… sont levées par le Service et catchées
    # globalement par les exception_handler enregistrés dans main.py.
    # ------------------------------------------------------------------
    def _register_routes(self):

        @limiter.limit("10/minute")
        def connexion(request: Request, response: Response, payload: UtilisateurLogin):
            utilisateur, access_token, refresh_token, csrf_token = self.auth_service.authentifier(
                payload.email, payload.mot_de_passe
            )
            self._poser_cookies(response, access_token, refresh_token, csrf_token)
            return LoginOut(utilisateur=UtilisateurOut.model_validate(utilisateur), csrf_token=csrf_token)

        @limiter.limit("30/minute")
        def get_mon_profil(request: Request, utilisateur: Utilisateur = Depends(get_current_utilisateur)):
            return utilisateur

        @limiter.limit("20/minute")
        def deconnexion(
            request: Request,
            response: Response,
            access_token: str = Cookie(default=None),
            refresh_token: str = Cookie(default=None),
            utilisateur: Utilisateur = Depends(get_current_utilisateur),
        ):
            for token, type_attendu in ((access_token, "access"), (refresh_token, "refresh")):
                if not token:
                    continue
                try:
                    payload = decoder_token(token)
                except jwt.InvalidTokenError:  # inclut ExpiredSignatureError : déjà inutilisable
                    continue
                if (
                    payload.get("type") == type_attendu
                    and payload.get("jti")
                    and payload.get("sub") == str(utilisateur.id)
                ):
                    self.auth_service.revoquer_token(
                        payload["jti"], utilisateur.id, type_attendu, payload["exp"]
                    )
            self._supprimer_cookies(response)
            return MessageOut(message="Déconnexion réussie.")

        @limiter.limit("30/minute")
        def rafraichir(
            request: Request,
            response: Response,
            refresh_token: str = Cookie(default=None),
        ):
            if refresh_token is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token manquant.")

            utilisateur, access_token, nouveau_refresh_token, csrf_token = self.auth_service.rafraichir_session(
                refresh_token
            )
            self._poser_cookies(response, access_token, nouveau_refresh_token, csrf_token)
            return LoginOut(utilisateur=UtilisateurOut.model_validate(utilisateur), csrf_token=csrf_token)

        @limiter.limit("5/minute")
        def changer_mot_de_passe(
            request: Request,
            response: Response,
            payload: ChangerMotDePasse,
            utilisateur: Utilisateur = Depends(get_current_utilisateur),
        ):
            utilisateur, access_token, refresh_token, csrf_token = self.auth_service.changer_mot_de_passe(
                utilisateur.id, payload.ancien_mot_de_passe, payload.nouveau_mot_de_passe
            )
            # Les autres sessions sont invalidées par mot_de_passe_change_le ; celle-ci est réémise.
            self._poser_cookies(response, access_token, refresh_token, csrf_token)
            return LoginOut(utilisateur=UtilisateurOut.model_validate(utilisateur), csrf_token=csrf_token)

        # ---- routes ----

        self.router.add_api_route(
            "/moi", get_mon_profil, methods=["GET"],
            response_model=UtilisateurOut,
        )
        self.router.add_api_route(
            "/connexion", connexion, methods=["POST"],
            response_model=LoginOut,
        )
        self.router.add_api_route(
            "/deconnexion", deconnexion, methods=["POST"],
            response_model=MessageOut,
        )
        self.router.add_api_route(
            "/rafraichir", rafraichir, methods=["POST"],
            response_model=LoginOut,
        )
        self.router.add_api_route(
            "/changer-mot-de-passe", changer_mot_de_passe, methods=["POST"],
            response_model=LoginOut,
        )


ctrl = AuthentificationController()