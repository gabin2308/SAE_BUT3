import hmac
from typing import Optional
from uuid import UUID

import jwt
from fastapi import Cookie, Depends, HTTPException, Request, status

from app.models.utilisateur.Utilisateur import Utilisateur, RoleUtilisateur
from app.utils.exceptions import UtilisateurIntrouvableError
from app.utils.dependencies import utilisateur_service, token_revoque_dao
from app.utils.jwt_utils import decoder_token, token_valide_apres_changement_mdp


def get_current_utilisateur(
    request: Request,
    access_token: Optional[str] = Cookie(default=None),
) -> Utilisateur:
    """
    Site web uniquement : authentification par cookie httpOnly, jamais par
    Authorization: Bearer (pas de client mobile/API à gérer). Le token est
    donc toujours accompagné d'un cookie, et la vérification CSRF (double
    submit : X-CSRF-Token doit correspondre au claim `csrf` du JWT) s'applique
    systématiquement sur les méthodes qui modifient l'état — jamais de mode
    conditionnel comme s'il pouvait y avoir un client hors cookie.

    Deux mécanismes de révocation, complémentaires :
      - token_revoque (par jti) : révocation ciblée d'une session précise
        (déconnexion).
      - mot_de_passe_change_le (comparé à iat) : révocation en masse de
        toutes les sessions d'un coup, y compris celles dont on ne connaît
        pas le jti (autres appareils) — déclenché au changement de mdp.
    """
    if access_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentification requise.")

    try:
        payload = decoder_token(access_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expirée.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide.")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide.")

    # Un token sans jti ne peut pas être révoqué : on le refuse.
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide.")

    if token_revoque_dao.est_revoque(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session révoquée.")

    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        csrf_header = request.headers.get("X-CSRF-Token")
        csrf_attendu = payload.get("csrf")
        # Comparaison en temps constant ; .encode() évite une TypeError sur un en-tête non ASCII.
        if (
            not csrf_header
            or not csrf_attendu
            or not hmac.compare_digest(csrf_header.encode(), csrf_attendu.encode())
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Jeton CSRF invalide ou manquant.")

    utilisateur_id = payload.get("sub")
    if utilisateur_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide.")

    try:
        utilisateur = utilisateur_service.find_by_id(UUID(utilisateur_id))
    except (UtilisateurIntrouvableError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable.")

    if not utilisateur.actif:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé.")

    if not token_valide_apres_changement_mdp(payload.get("iat"), utilisateur.mot_de_passe_change_le):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée suite à un changement de mot de passe.",
        )

    return utilisateur


def require_role(*roles_autorises: RoleUtilisateur):
    def verifier(utilisateur: Utilisateur = Depends(get_current_utilisateur)) -> Utilisateur:
        if utilisateur.role not in roles_autorises:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé pour ce rôle.")
        return utilisateur
    return verifier

require_evaluateur = require_role(RoleUtilisateur.EVALUATEUR)