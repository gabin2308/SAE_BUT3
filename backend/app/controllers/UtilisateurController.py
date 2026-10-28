from fastapi import APIRouter, Depends, Request, status

from app.utils.limiter import limiter
from app.models.utilisateur.Utilisateur import Utilisateur
from app.utils.auth import get_current_utilisateur
from app.utils.dependencies import utilisateur_service
from app.models.utilisateur.UtilisateurSchema import (
    ActivationCompte,
    ConsentementsOut,
    ConsentementUpdate,
    DemandeReinitialisation,
    Inscription,
    MessageOut,
    RenvoiActivation,
    ReinitialisationMotDePasse,
    UtilisateurOut,
    UtilisateurUpdate,
)


class UtilisateurController:

    def __init__(self):
        self.router = APIRouter(prefix="/utilisateurs", tags=["Utilisateurs"])
        # Service partagé, assemblé une seule fois dans app/utils/dependencies.py.
        self.utilisateur_service = utilisateur_service
        self._register_routes()

    # ------------------------------------------------------------------
    # Routes
    # Aucun try/except ici : EmailDejaUtiliseError, ValidationError,
    # UtilisateurIntrouvableError… sont levées par le Service/DAO et catchées
    # globalement par les exception_handler enregistrés dans main.py.
    # Les routes sont en `def` (et non `async def`) : psycopg2 est synchrone,
    # FastAPI les exécute dans un thread sans bloquer la boucle d'événements.
    # ------------------------------------------------------------------
    def _register_routes(self):

        # ---- Routes publiques (pas de cookie, donc pas de CSRF) ----

        @limiter.limit("5/minute")
        def inscription(request: Request, payload: Inscription):
            self.utilisateur_service.inscrire(
                payload.nom,
                payload.prenom,
                payload.email,
                payload.mot_de_passe,
                payload.consentement_personnalisation,
                payload.consentement_localisation,
            )
            return MessageOut(message="Compte créé. Consultez votre email pour l'activer.")

        @limiter.limit("10/minute")
        def activation(request: Request, payload: ActivationCompte):
            self.utilisateur_service.activer_compte(payload.jeton)
            return MessageOut(message="Compte activé. Vous pouvez vous connecter.")

        @limiter.limit("3/minute")
        def renvoyer_activation(request: Request, payload: RenvoiActivation):
            self.utilisateur_service.renvoyer_activation(payload.email)
            # Réponse identique que l'email existe ou non.
            return MessageOut(message="Si ce compte existe et n'est pas activé, un email vient d'être envoyé.")

        @limiter.limit("3/minute")
        def mot_de_passe_oublie(request: Request, payload: DemandeReinitialisation):
            self.utilisateur_service.demander_reinitialisation(payload.email)
            # Réponse identique que l'email existe ou non.
            return MessageOut(message="Si ce compte existe, un email de réinitialisation vient d'être envoyé.")

        @limiter.limit("5/minute")
        def reinitialisation(request: Request, payload: ReinitialisationMotDePasse):
            self.utilisateur_service.reinitialiser_mot_de_passe(payload.jeton, payload.nouveau_mot_de_passe)
            return MessageOut(message="Mot de passe modifié. Vous pouvez vous connecter.")

        # ---- Routes authentifiées (cookie + CSRF sur les écritures) ----

        @limiter.limit("20/minute")
        def modifier_profil(
            request: Request,
            payload: UtilisateurUpdate,
            utilisateur: Utilisateur = Depends(get_current_utilisateur),
        ):
            # exclude_unset : seuls les champs réellement envoyés sont modifiés
            return self.utilisateur_service.modifier_profil(
                utilisateur.id, payload.model_dump(exclude_unset=True)
            )

        @limiter.limit("30/minute")
        def lire_consentements(
            request: Request,
            utilisateur: Utilisateur = Depends(get_current_utilisateur),
        ):
            return ConsentementsOut(**self.utilisateur_service.lire_consentements(utilisateur.id))

        @limiter.limit("20/minute")
        def modifier_consentement(
            request: Request,
            payload: ConsentementUpdate,
            utilisateur: Utilisateur = Depends(get_current_utilisateur),
        ):
            consentements = self.utilisateur_service.modifier_consentement(
                utilisateur.id, payload.type, payload.accorde
            )
            return ConsentementsOut(**consentements)

        @limiter.limit("10/minute")
        def terminer_onboarding(
            request: Request,
            utilisateur: Utilisateur = Depends(get_current_utilisateur),
        ):
            self.utilisateur_service.terminer_onboarding(utilisateur.id)
            return MessageOut(message="Onboarding terminé.")

        # ---- routes ----

        self.router.add_api_route(
            "/inscription", inscription, methods=["POST"],
            response_model=MessageOut, status_code=status.HTTP_201_CREATED,
        )
        self.router.add_api_route(
            "/activation", activation, methods=["POST"],
            response_model=MessageOut,
        )
        self.router.add_api_route(
            "/activation/renvoyer", renvoyer_activation, methods=["POST"],
            response_model=MessageOut,
        )
        self.router.add_api_route(
            "/mot-de-passe-oublie", mot_de_passe_oublie, methods=["POST"],
            response_model=MessageOut,
        )
        self.router.add_api_route(
            "/reinitialisation", reinitialisation, methods=["POST"],
            response_model=MessageOut,
        )
        self.router.add_api_route(
            "/moi", modifier_profil, methods=["PATCH"],
            response_model=UtilisateurOut,
        )
        self.router.add_api_route(
            "/moi/consentements", lire_consentements, methods=["GET"],
            response_model=ConsentementsOut,
        )
        self.router.add_api_route(
            "/moi/consentements", modifier_consentement, methods=["PUT"],
            response_model=ConsentementsOut,
        )
        self.router.add_api_route(
            "/moi/onboarding", terminer_onboarding, methods=["POST"],
            response_model=MessageOut,
        )


ctrl = UtilisateurController()