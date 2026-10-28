# app/models/jeton/jeton_interface.py
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional
from uuid import UUID

from app.models.jeton.Jeton import TypeJeton


class JetonInterface(ABC):

    @abstractmethod
    def create(
        self, utilisateur_id: UUID, type_jeton: TypeJeton, hash_jeton: str, duree: timedelta
    ) -> None:
        """Invalide les jetons non utilisés du même type pour cet utilisateur, puis
        insère le nouveau (expire_le = NOW() + duree), dans une seule transaction.
        Un seul jeton valide à la fois : « renvoyer l'email » annule le précédent."""

    @abstractmethod
    def activer_compte(self, hash_jeton: str) -> Optional[UUID]:
        """Consomme un jeton d'activation valide ET passe actif = TRUE, en une seule
        instruction SQL. Renvoie l'id de l'utilisateur, ou None si le jeton est
        inconnu, expiré ou déjà utilisé (le service ne doit pas distinguer ces cas)."""

    @abstractmethod
    def reinitialiser_mot_de_passe(self, hash_jeton: str, nouveau_hash_mdp: str) -> Optional[UUID]:
        """Consomme un jeton de réinitialisation valide ET remplace le hash du mot de
        passe, en une seule instruction SQL. Même contrat de retour qu'activer_compte."""

    @abstractmethod
    def supprimer_expires(self) -> int:
        """Supprime les jetons expirés ou utilisés (nettoyage). Renvoie le nombre supprimé."""