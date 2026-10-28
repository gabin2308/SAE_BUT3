"""
Schémas Pydantic : module Utilisateur
Contrats de validation entrée/sortie pour l'API FastAPI.
Ne pas confondre avec models/utilisateur/Utilisateur.py (représentation interne,
utilisée par le DAO/Service, jamais exposée telle quelle).
"""

import re
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.utilisateur.Utilisateur import RoleUtilisateur


def _valider_complexite_mdp(v: str) -> str:
    if not re.search(r"[A-Z]", v):
        raise ValueError("Le mot de passe doit contenir au moins une majuscule.")
    if not re.search(r"[0-9]", v):
        raise ValueError("Le mot de passe doit contenir au moins un chiffre.")
    if not re.search(r"[!@#$%^&*()\-_=+\[\]{};:,.<>?/\\|`~\"']", v):
        raise ValueError("Le mot de passe doit contenir au moins un caractère spécial.")
    # bcrypt ne traite que 72 octets (et la lib récente lève une erreur au-delà)
    if len(v.encode("utf-8")) > 72:
        raise ValueError("Le mot de passe est trop long (72 octets maximum).")
    return v


def _valider_nom(v: str) -> str:
    v = re.sub(r"\s+", " ", v).strip()
    if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ\s\-']+", v):
        raise ValueError("Ne doit contenir que des lettres, espaces, tirets et apostrophes.")
    return v


def _normaliser_email(v: str) -> str:
    return v.strip().lower()


# ----------------------------------------------------------------------------
# Entrée : inscription (US1). Le rôle n'est jamais fourni par le client :
# le service crée toujours un compte « utilisateur », inactif jusqu'à
# l'activation par email (US2).
# Les consentements sont écrits dans la table consentements par le service.
# ----------------------------------------------------------------------------
class Inscription(BaseModel):
    nom: str = Field(..., min_length=2, max_length=100)
    prenom: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    mot_de_passe: str = Field(..., min_length=8, max_length=128)
    consentement_politique: bool                    # obligatoire
    consentement_personnalisation: bool = False     # facultatif
    consentement_localisation: bool = False         # facultatif

    @field_validator("nom", "prenom")
    @classmethod
    def valider_nom(cls, v: str) -> str:
        return _valider_nom(v)

    @field_validator("email")
    @classmethod
    def normaliser_email(cls, v: str) -> str:
        return _normaliser_email(v)

    @field_validator("mot_de_passe")
    @classmethod
    def valider_mot_de_passe(cls, v: str) -> str:
        return _valider_complexite_mdp(v)

    @field_validator("consentement_politique")
    @classmethod
    def valider_consentement(cls, v: bool) -> bool:
        if not v:
            raise ValueError("L'acceptation de la politique de confidentialité est obligatoire.")
        return v


# ----------------------------------------------------------------------------
# Entrée : jetons à usage unique (table jetons)
# Le jeton en clair vient du lien envoyé par email ; seul son hash est en base.
# ----------------------------------------------------------------------------
class ActivationCompte(BaseModel):
    jeton: str = Field(..., min_length=20, max_length=200)


class DemandeReinitialisation(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normaliser_email(cls, v: str) -> str:
        return _normaliser_email(v)


class ReinitialisationMotDePasse(BaseModel):
    jeton: str = Field(..., min_length=20, max_length=200)
    nouveau_mot_de_passe: str = Field(..., min_length=8, max_length=128)

    @field_validator("nouveau_mot_de_passe")
    @classmethod
    def valider_nouveau_mot_de_passe(cls, v: str) -> str:
        return _valider_complexite_mdp(v)


# ----------------------------------------------------------------------------
# Entrée : connexion (US3)
# ----------------------------------------------------------------------------
class UtilisateurLogin(BaseModel):
    email: EmailStr
    mot_de_passe: str = Field(..., min_length=1)

    @field_validator("email")
    @classmethod
    def normaliser_email(cls, v: str) -> str:
        return _normaliser_email(v)


# ----------------------------------------------------------------------------
# Entrée : mise à jour de son propre profil (ni email, ni rôle, ni statut)
# ----------------------------------------------------------------------------
class UtilisateurUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=2, max_length=100)
    prenom: Optional[str] = Field(None, min_length=2, max_length=100)

    @field_validator("nom", "prenom")
    @classmethod
    def valider_nom(cls, v: Optional[str]) -> str:
        # Un champ absent du JSON n'est pas validé (valeur par défaut) ; si on
        # arrive ici avec None, le client a envoyé un null explicite : on le refuse,
        # sinon le DAO ferait SET nom = NULL et la colonne NOT NULL lèverait une erreur 500.
        if v is None:
            raise ValueError("Ce champ ne peut pas être null.")
        return _valider_nom(v)

    @model_validator(mode="after")
    def verifier_au_moins_un_champ(self):
        if not self.model_fields_set:
            raise ValueError("Au moins un champ à modifier est requis.")
        return self


# ----------------------------------------------------------------------------
# Entrée : changement de mot de passe
# ----------------------------------------------------------------------------
class ChangerMotDePasse(BaseModel):
    ancien_mot_de_passe: str = Field(..., min_length=1)
    nouveau_mot_de_passe: str = Field(..., min_length=8, max_length=128)

    @field_validator("nouveau_mot_de_passe")
    @classmethod
    def valider_nouveau_mot_de_passe(cls, v: str) -> str:
        return _valider_complexite_mdp(v)

    @model_validator(mode="after")
    def verifier_nouveau_different(self):
        if self.nouveau_mot_de_passe == self.ancien_mot_de_passe:
            raise ValueError("Le nouveau mot de passe doit être différent de l'ancien.")
        return self


# ----------------------------------------------------------------------------
# Entrée : modification d'un consentement facultatif
# « politique » est volontairement exclu : il est obligatoire, on ne le retire
# pas via l'API (retirer la politique = supprimer son compte).
# ----------------------------------------------------------------------------
class ConsentementUpdate(BaseModel):
    type: Literal["personnalisation", "localisation"]
    accorde: bool


# ----------------------------------------------------------------------------
# Sorties : jamais de mot_de_passe_hash
# ----------------------------------------------------------------------------
class UtilisateurOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    nom: str
    prenom: str
    role: RoleUtilisateur
    actif: bool
    onboarding_termine: bool
    derniere_connexion: Optional[datetime] = None
    cree_le: Optional[datetime] = None


class ConsentementsOut(BaseModel):
    politique: bool
    personnalisation: bool
    localisation: bool


# ----------------------------------------------------------------------------
# Sortie : authentification par cookies HttpOnly
# Les JWT transitent uniquement par Set-Cookie, jamais dans le corps JSON.
# Le corps ne contient que l'utilisateur et le jeton CSRF (double-submit
# cookie), renvoyé par le front dans l'en-tête X-CSRF-Token.
# ----------------------------------------------------------------------------
class LoginOut(BaseModel):
    utilisateur: UtilisateurOut
    csrf_token: str


class RefreshOut(BaseModel):
    message: str = "Token rafraîchi"
    csrf_token: str


class MessageOut(BaseModel):
    message: str

class RenvoiActivation(DemandeReinitialisation):
    """Même contenu (un email normalisé), mais un nom qui dit ce que fait la route."""