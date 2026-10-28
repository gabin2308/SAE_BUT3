# app/utils/jetons.py
import hashlib
import secrets


def generer_jeton() -> tuple[str, str]:
    """Renvoie (jeton_en_clair, hash). Le clair part dans l'email, seul le hash va en base."""
    jeton = secrets.token_urlsafe(32)
    return jeton, hacher_jeton(jeton)


def hacher_jeton(jeton: str) -> str:
    # SHA-256 suffit : le jeton a 256 bits d'entropie, pas besoin de bcrypt.
    # 64 caractères hexadécimaux = CHAR(64) de la table jetons.
    return hashlib.sha256(jeton.encode("utf-8")).hexdigest()