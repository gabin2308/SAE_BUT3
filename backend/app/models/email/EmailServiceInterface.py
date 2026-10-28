from abc import ABC, abstractmethod
from typing import Optional


class EmailEnvoyeInterface(ABC):

    @abstractmethod
    def journaliser(
        self,
        type_email: str,
        destinataire: str,
        sujet: str,
        statut: str,
        erreur: Optional[str] = None,
    ) -> None:
        """Enregistre le résultat d'un envoi dans email_envoye. Le corps de l'email
        n'est jamais stocké : il contient un lien secret.
        statut vaut 'envoye' ou 'echec' (contrainte CHECK en base)."""

    @abstractmethod
    def supprimer_anciens(self, jours: int = 90) -> int:
        """Supprime les entrées plus vieilles que `jours` (le journal contient des
        adresses email : on ne les garde pas indéfiniment). Renvoie le nombre supprimé."""