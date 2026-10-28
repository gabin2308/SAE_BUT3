from datetime import datetime, timezone
from uuid import UUID

import jwt

from app.models.utilisateur.Utilisateur import Utilisateur
from app.models.utilisateur.UtilisateurInterface import UtilisateurInterface
from app.models.token_revoque.TokenRevoqueInterface import TokenRevoqueInterface
from app.utils.exceptions import (
    IdentifiantsInvalidesError,
    UtilisateurIntrouvableError,
    ValidationError,
)
from app.utils.jwt_utils import (
    decoder_token,
    generer_access_token,
    generer_refresh_token,
    generer_csrf_token,
    token_valide_apres_changement_mdp,
)
from app.utils.mot_de_passe import (
    HASH_FACTICE,
    hasher_mot_de_passe,
    verifier_mot_de_passe,
)


class AuthService:

    def __init__(self, utilisateur_dao: UtilisateurInterface, token_revoque_dao: TokenRevoqueInterface):
        self.utilisateur_dao = utilisateur_dao
        self.token_revoque_dao = token_revoque_dao

    # ------------------------------------------------------------------
    # Connexion
    # ------------------------------------------------------------------
    def authentifier(self, email: str, mot_de_passe: str) -> tuple[Utilisateur, str, str, str]:
        email_normalise = email.strip().lower()
        # Seule lecture qui ramène le hash du mot de passe
        utilisateur = self.utilisateur_dao.find_for_authentication(email_normalise)

        # Email inconnu : on vérifie quand même contre un hash factice, pour que
        # le temps de réponse ne révèle pas quels emails sont enregistrés.
        if utilisateur is None:
            verifier_mot_de_passe(mot_de_passe, HASH_FACTICE)
            raise IdentifiantsInvalidesError("Email ou mot de passe incorrect.")

        mot_de_passe_ok = verifier_mot_de_passe(mot_de_passe, utilisateur.mot_de_passe_hash)

        # Message volontairement identique dans tous les cas d'échec
        # (mauvais mot de passe, compte non activé).
        if not mot_de_passe_ok or not utilisateur.actif:
            raise IdentifiantsInvalidesError("Email ou mot de passe incorrect.")

        self.utilisateur_dao.update_derniere_connexion(utilisateur.id)
        return self._ouvrir_session(utilisateur)

    # ------------------------------------------------------------------
    # Changement de mot de passe (réémet la session en cours)
    # ------------------------------------------------------------------
    def changer_mot_de_passe(
        self, utilisateur_id: UUID, ancien_mdp: str, nouveau_mdp: str
    ) -> tuple[Utilisateur, str, str, str]:
        complet = self._lire_avec_hash(utilisateur_id)

        if not verifier_mot_de_passe(ancien_mdp, complet.mot_de_passe_hash):
            raise IdentifiantsInvalidesError("Ancien mot de passe incorrect.")

        # Le nouveau mot de passe doit différer de l'ancien : sans ce contrôle,
        # un "changement" pour le même mot de passe invaliderait quand même les
        # autres sessions (mot_de_passe_change_le) sans rotation réelle.
        if verifier_mot_de_passe(nouveau_mdp, complet.mot_de_passe_hash):
            raise ValidationError({"nouveau_mot_de_passe": ["Le nouveau mot de passe doit différer de l'ancien."]})

        utilisateur = self.utilisateur_dao.update_mot_de_passe(
            utilisateur_id, hasher_mot_de_passe(nouveau_mdp)
        )

        # Session en cours réémise avec un iat frais, pour ne pas déconnecter
        # l'utilisateur suite à son propre changement volontaire de mot de passe.
        return self._ouvrir_session(utilisateur)

    # ------------------------------------------------------------------
    # Rafraîchissement et révocation
    # ------------------------------------------------------------------
    def rafraichir_session(self, refresh_token: str) -> tuple[Utilisateur, str, str, str]:
        try:
            payload = decoder_token(refresh_token)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise IdentifiantsInvalidesError("Session expirée, veuillez vous reconnecter.")

        if payload.get("type") != "refresh":
            raise IdentifiantsInvalidesError("Token invalide.")

        # Un token sans jti ne peut pas être révoqué : on le refuse.
        jti = payload.get("jti")
        if not jti:
            raise IdentifiantsInvalidesError("Token invalide.")

        # Contrôle rapide avant le travail de rotation
        if self.token_revoque_dao.est_revoque(jti):
            raise IdentifiantsInvalidesError("Session révoquée, veuillez vous reconnecter.")

        utilisateur = self.utilisateur_dao.find_by_id(UUID(payload["sub"]))
        if utilisateur is None:
            raise IdentifiantsInvalidesError("Session invalide.")
        if not utilisateur.actif:
            raise IdentifiantsInvalidesError("Compte désactivé.")

        if not token_valide_apres_changement_mdp(payload.get("iat"), utilisateur.mot_de_passe_change_le):
            raise IdentifiantsInvalidesError("Session expirée suite à un changement de mot de passe.")

        # Rotation atomique : revoquer() renvoie False si une requête simultanée a
        # déjà consommé ce refresh token. Dans ce cas on refuse, sinon deux
        # requêtes parallèles obtiendraient chacune une session.
        expire_le = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        if not self.token_revoque_dao.revoquer(jti, utilisateur.id, "refresh", expire_le):
            raise IdentifiantsInvalidesError("Session révoquée, veuillez vous reconnecter.")

        return self._ouvrir_session(utilisateur)

    def revoquer_token(self, jti: str, utilisateur_id: UUID, type_token: str, exp_unix: int) -> None:
        """Déconnexion : appelé pour l'access token et le refresh token du cookie.
        Idempotent : révoquer deux fois le même jti n'est pas une erreur."""
        expire_le = datetime.fromtimestamp(exp_unix, tz=timezone.utc)
        self.token_revoque_dao.revoquer(jti, utilisateur_id, type_token, expire_le)

    # ------------------------------------------------------------------
    # Helpers internes
    # ------------------------------------------------------------------
    def _lire_avec_hash(self, utilisateur_id: UUID) -> Utilisateur:
        """find_by_id ne ramène pas le hash : relecture réservée à l'authentification."""
        utilisateur = self.utilisateur_dao.find_by_id(utilisateur_id)
        if utilisateur is None:
            raise UtilisateurIntrouvableError("Utilisateur introuvable.")
        complet = self.utilisateur_dao.find_for_authentication(utilisateur.email)
        if complet is None:
            raise UtilisateurIntrouvableError("Utilisateur introuvable.")
        return complet

    @staticmethod
    def _ouvrir_session(utilisateur: Utilisateur) -> tuple[Utilisateur, str, str, str]:
        csrf_token = generer_csrf_token()
        access_token = generer_access_token(utilisateur.id, utilisateur.role.value, csrf_token)
        refresh_token = generer_refresh_token(utilisateur.id, utilisateur.role.value)
        return utilisateur, access_token, refresh_token, csrf_token