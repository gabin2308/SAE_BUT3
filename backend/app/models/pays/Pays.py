from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
from typing import Optional


@dataclass
class Pays:
    """Pays du référentiel (table pays, US33). Code ISO 3166-1 alpha-2."""

    code_pays: str
    nom: str
    cree_le: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: dict) -> "Pays":
        """Construit l'objet depuis une ligne RealDictCursor.

        Les colonnes inconnues (jointure, autre module) sont ignorées ;
        les colonnes absentes du SELECT prennent leur valeur par défaut.
        """
        noms = {f.name for f in fields(cls)}
        donnees = {cle: valeur for cle, valeur in row.items() if cle in noms}
        return cls(**donnees)

    def to_public_dict(self) -> dict:
        return {"code_pays": self.code_pays, "nom": self.nom}