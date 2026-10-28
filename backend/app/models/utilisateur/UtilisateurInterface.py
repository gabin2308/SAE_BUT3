from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.models.utilisateur.Utilisateur import NouvelUtilisateur, Utilisateur


class UtilisateurInterface(ABC):

    @abstractmethod
    def create(self, nouvel: NouvelUtilisateur, consentements: dict[str, bool]) -> Utilisateur:
        """Insère l'utilisateur (actif=FALSE) et ses consentements dans UNE seule
        transaction (un seul get_db_cursor(commit=True)), puis renvoie la ligne créée.
        `consentements` : {"politique": True, "personnalisation": bool, "localisation": bool}.
        Lève EmailDejaUtiliseError (app.utils.exceptions) si l'email existe
        (violation de uq_utilisateurs_email)."""

    @abstractmethod
    def find_by_id(self, utilisateur_id: UUID) -> Optional[Utilisateur]:
        """Sans mot_de_passe_hash."""

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Utilisateur]:
        """Email comparé en minuscules (LOWER(email) = %s). Sans mot_de_passe_hash."""

    @abstractmethod
    def find_for_authentication(self, email: str) -> Optional[Utilisateur]:
        """Comme find_by_email, mais avec mot_de_passe_hash. Réservé au module
        d'authentification."""

    @abstractmethod
    def email_existe(self, email: str) -> bool:
        pass

    @abstractmethod
    def update(self, utilisateur_id: UUID, donnees: dict) -> Utilisateur:
        """Met à jour uniquement nom et prenom (liste blanche de colonnes, jamais de
        clés du dict injectées telles quelles dans le SQL)."""

    @abstractmethod
    def update_mot_de_passe(self, utilisateur_id: UUID, mot_de_passe_hash: str) -> Utilisateur:
        """Met à jour le hash et mot_de_passe_change_le = NOW() (invalide les JWT
        émis avant cette date). Sert au changement de mot de passe."""

    @abstractmethod
    def activer(self, utilisateur_id: UUID) -> Utilisateur:
        """actif = TRUE (activation par email, US2)."""

    @abstractmethod
    def marquer_onboarding_termine(self, utilisateur_id: UUID) -> None:
        """onboarding_termine = TRUE (page de préférences remplie ou passée, US5)."""

    @abstractmethod
    def update_derniere_connexion(self, utilisateur_id: UUID) -> None:
        """derniere_connexion = NOW()."""

    @abstractmethod
    def find_consentements(self, utilisateur_id: UUID) -> dict[str, bool]:
        """{"politique": ..., "personnalisation": ..., "localisation": ...}.
        Un type absent de la table vaut False."""

    @abstractmethod
    def upsert_consentement(self, utilisateur_id: UUID, type_consentement: str, accorde: bool) -> None:
        """INSERT ... ON CONFLICT (utilisateur_id, type) DO UPDATE (modifie_le = NOW())."""

    @abstractmethod
    def delete(self, utilisateur_id: UUID) -> None:
        """Supprime le compte (droit à l'effacement). Les tables liées partent en
        ON DELETE CASCADE ; les mesures de executions_recommandation sont conservées
        (ON DELETE SET NULL)."""