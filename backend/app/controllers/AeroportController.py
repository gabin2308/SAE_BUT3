# app/controllers/AeroportController.py
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.models.utilisateur.Utilisateur import Utilisateur
from app.utils.auth import get_current_utilisateur
from app.utils.dependencies import aeroport_service, pays_service
from app.utils.limiter import limiter
from app.models.aeroport.AeroportSchema import AeroportOut, PaysOut


class AeroportController:

    def __init__(self):
        self.router = APIRouter(prefix="/aeroports", tags=["Aéroports"])
        # Services partagés, assemblés une seule fois dans app/utils/dependencies.py.
        self.aeroport_service = aeroport_service
        self.pays_service = pays_service
        self._register_routes()

    # ------------------------------------------------------------------
    # Routes en lecture seule : GET donc pas de CSRF.
    # Les erreurs métier (ValidationError…) sont catchées globalement
    # par les exception_handler de main.py.
    # ------------------------------------------------------------------
    def _register_routes(self):

        @limiter.limit("60/minute")
        def rechercher(
            request: Request,
            q: Annotated[str, Query(min_length=2, max_length=100)],
            limite: Annotated[int, Query(ge=1, le=20)] = 10,
            utilisateur: Utilisateur = Depends(get_current_utilisateur),
        ):
            return [a.to_public_dict() for a in self.aeroport_service.rechercher(q, limite)]

        @limiter.limit("30/minute")
        def lister_pays(
            request: Request,
            utilisateur: Utilisateur = Depends(get_current_utilisateur),
        ):
            return [p.to_public_dict() for p in self.pays_service.lister()]

        # ---- routes ----
        # /pays est déclarée avant toute route /{code_iata} future.

        self.router.add_api_route(
            "", rechercher, methods=["GET"],
            response_model=list[AeroportOut],
        )
        self.router.add_api_route(
            "/pays", lister_pays, methods=["GET"],
            response_model=list[PaysOut],
        )


ctrl = AeroportController()