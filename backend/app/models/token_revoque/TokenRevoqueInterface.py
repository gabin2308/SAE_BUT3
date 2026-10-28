# app/models/token_revoque/TokenRevoqueInterface.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Literal
from uuid import UUID


class TokenRevoqueInterface(ABC):

    @abstractmethod
    def est_revoque(self, jti: str) -> bool:
        """True si ce jti figure dans tokens_revoques."""

    @abstractmethod
    def revoquer(
        self,
        jti: str,
        utilisateur_id: UUID,
        type_token: Literal["access", "refresh"],
        expire_le: datetime,
    ) -> bool:
        """Ajoute le jti à la liste. Renvoie True si CE appel l'a révoqué, False s'il
        l'était déjà. Ce retour sert à rendre la rotation du refresh token atomique."""

    @abstractmethod
    def supprimer_expires(self) -> int:
        """Supprime les lignes dont le token a expiré (il est de toute façon refusé
        par sa signature). Renvoie le nombre de lignes supprimées."""