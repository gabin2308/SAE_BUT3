import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Optional

import jwt
import secrets

from app.settings import settings

SECRET_KEY = settings.JWT_SECRET
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError("JWT_SECRET n'est pas défini dans l'environnement")

ALGORITHM = "HS256"
ACCESS_TOKEN_DUREE = timedelta(minutes=30)
REFRESH_TOKEN_DUREE = timedelta(days=7)


def _generer_token(utilisateur_id: UUID, role: str, duree: timedelta, type_token: str, csrf_token: str = None) -> str:
    maintenant = datetime.now(timezone.utc)
    payload = {
        "sub": str(utilisateur_id),
        "role": role,
        "type": type_token,
        "iat": maintenant,
        "exp": maintenant + duree,
        "jti": str(uuid.uuid4()),
    }
    if csrf_token:
        payload["csrf"] = csrf_token
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def generer_access_token(utilisateur_id: UUID, role: str, csrf_token: str) -> str:
    return _generer_token(utilisateur_id, role, ACCESS_TOKEN_DUREE, "access", csrf_token)


def generer_refresh_token(utilisateur_id: UUID, role: str) -> str:
    return _generer_token(utilisateur_id, role, REFRESH_TOKEN_DUREE, "refresh")


def generer_csrf_token() -> str:
    return secrets.token_urlsafe(32)  # 32 octets -> 43 caractères URL-safe

def decoder_token(token: str) -> dict:
    """Lève jwt.ExpiredSignatureError ou jwt.InvalidTokenError si invalide,
    à intercepter explicitement à l'appel, pas ici."""
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"require": ["exp", "iat", "jti", "sub", "type"]},
    )

def token_valide_apres_changement_mdp(iat: Optional[int], mot_de_passe_change_le: Optional[datetime]) -> bool:
    """
    Détermine si un JWT émis à `iat` (claim, epoch seconds) reste valide compte
    tenu d'un éventuel changement de mot de passe.

    Utilisée à la fois par auth.py (vérification à chaque requête) et par
    UtilisateurService.rafraichir_session (vérification à chaque refresh) :
    centralisée ici pour que les deux ne puissent pas diverger.

    `iat` est tronqué à la seconde par le standard JWT : on tronque aussi
    `mot_de_passe_change_le` avant de comparer, sinon un token émis juste
    après le changement de mot de passe serait rejeté à tort (iat antérieur
    de quelques millisecondes à change_le).
    """
    if mot_de_passe_change_le is None:
        return True
    if iat is None:
        return False
    return datetime.fromtimestamp(iat, tz=timezone.utc) >= mot_de_passe_change_le.replace(microsecond=0)