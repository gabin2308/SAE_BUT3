from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class RoleUtilisateur(str, Enum):
    # Les valeurs doivent correspondre exactement au type SQL role_utilisateur
    UTILISATEUR = "utilisateur"
    EVALUATEUR = "evaluateur"


@dataclass
class Utilisateur:
    """Compte de l'application (utilisateur ou évaluateur).

    Un compte est créé inactif (actif=False) puis activé par email (US2).
    mot_de_passe_hash est NOT NULL en base ; il est Optional ici uniquement
    pour les SELECT qui ne le ramènent pas (listes, profil).
    """

    id: UUID
    email: str
    nom: str
    prenom: str
    role: RoleUtilisateur = RoleUtilisateur.UTILISATEUR
    # repr=False : jamais dans les logs ni dans un print()
    mot_de_passe_hash: Optional[str] = field(default=None, repr=False)
    actif: bool = False
    onboarding_termine: bool = False
    simule: bool = False   # utilisateur fictif (US36)
    demo: bool = False     # compte de démonstration (US32)
    derniere_connexion: Optional[datetime] = None
    mot_de_passe_change_le: Optional[datetime] = None
    cree_le: Optional[datetime] = None
    modifie_le: Optional[datetime] = None

    @property
    def nom_complet(self) -> str:
        return f"{self.prenom} {self.nom}"

    @property
    def est_evaluateur(self) -> bool:
        return self.role == RoleUtilisateur.EVALUATEUR

    @classmethod
    def from_row(cls, row: dict) -> "Utilisateur":
        """Construit l'objet depuis une ligne RealDictCursor.

        Les colonnes inconnues (jointure, autre module) sont ignorées ;
        les colonnes absentes du SELECT prennent leur valeur par défaut.
        """
        noms = {f.name for f in fields(cls)}
        donnees = {cle: valeur for cle, valeur in row.items() if cle in noms}
        if "role" in donnees:
            donnees["role"] = RoleUtilisateur(donnees["role"])
        return cls(**donnees)

    def to_public_dict(self) -> dict:
        """Champs publics uniquement : jamais de hash de mot de passe."""
        return {
            "id": str(self.id),
            "email": self.email,
            "nom": self.nom,
            "prenom": self.prenom,
            "role": self.role.value,
            "actif": self.actif,
            "onboarding_termine": self.onboarding_termine,
            "derniere_connexion": (
                self.derniere_connexion.isoformat() if self.derniere_connexion else None
            ),
            "cree_le": self.cree_le.isoformat() if self.cree_le else None,
            "mot_de_passe_change_le": (
                self.mot_de_passe_change_le.isoformat() if self.mot_de_passe_change_le else None
            ),
        }


@dataclass(frozen=True)
class NouvelUtilisateur:
    """Ce que le Service transmet au DAO pour créer un compte (id généré par la base).

    Le compte naît inactif : l'activation passe par un jeton (table jetons).
    Le mot de passe est déjà haché. Le consentement « politique » est obligatoire
    mais vit dans la table consentements : le service le vérifie et le DAO l'insère
    dans la même transaction que l'utilisateur.
    """

    email: str
    nom: str
    prenom: str
    mot_de_passe_hash: str = field(repr=False)
    role: RoleUtilisateur = RoleUtilisateur.UTILISATEUR

    def __post_init__(self) -> None:
        # L'unicité en base porte sur LOWER(email) : on normalise dès l'entrée.
        object.__setattr__(self, "email", self.email.strip().lower())