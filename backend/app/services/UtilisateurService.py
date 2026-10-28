from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.models.jeton.Jeton import TypeJeton
from app.models.jeton.JetonInterface import JetonInterface
from app.models.utilisateur.Utilisateur import NouvelUtilisateur, Utilisateur
from app.models.utilisateur.UtilisateurInterface import UtilisateurInterface
from app.settings import settings
from app.utils.exceptions import UtilisateurIntrouvableError, ValidationError
from app.utils.jetons import generer_jeton, hacher_jeton
from app.utils.mot_de_passe import hasher_mot_de_passe
from service_externe.smtp.email_smtp import (
    envoyer_email_activation,
    envoyer_email_reinitialisation,
)

DUREE_JETON_ACTIVATION = timedelta(hours=24)
DUREE_JETON_REINITIALISATION = timedelta(hours=1)


class UtilisateurService:

    def __init__(self, utilisateur_dao: UtilisateurInterface, jeton_dao: JetonInterface):
        self.utilisateur_dao = utilisateur_dao
        self.jeton_dao = jeton_dao

    # ------------------------------------------------------------------
    # Inscription et activation (US1, US2)
    # ------------------------------------------------------------------
    def inscrire(
        self,
        nom: str,
        prenom: str,
        email: str,
        mot_de_passe: str,
        consentement_personnalisation: bool = False,
        consentement_localisation: bool = False,
    ) -> Utilisateur:
        """Crée un compte « utilisateur » inactif, puis envoie le lien d'activation.
        Le rôle n'est jamais choisi par le client. Le consentement « politique »
        est déjà validé par le schéma Inscription.
        Lève EmailDejaUtiliseError (venue du DAO) si l'email existe."""
        nouvel = NouvelUtilisateur(
            email=email,
            nom=nom,
            prenom=prenom,
            mot_de_passe_hash=hasher_mot_de_passe(mot_de_passe),
        )
        consentements = {
            "politique": True,
            "personnalisation": consentement_personnalisation,
            "localisation": consentement_localisation,
        }
        utilisateur = self.utilisateur_dao.create(nouvel, consentements)
        self._envoyer_lien_activation(utilisateur)
        return utilisateur

    def activer_compte(self, jeton: str) -> None:
        # Même erreur pour inconnu, expiré ou déjà utilisé : on ne distingue pas.
        if self.jeton_dao.activer_compte(hacher_jeton(jeton)) is None:
            raise ValidationError({"jeton": ["Lien invalide ou expiré."]})

    def renvoyer_activation(self, email: str) -> None:
        """Ne révèle jamais si l'email existe : la réponse est identique dans tous les cas."""
        utilisateur = self.utilisateur_dao.find_by_email(email.strip().lower())
        if utilisateur is not None and not utilisateur.actif:
            self._envoyer_lien_activation(utilisateur)

    # ------------------------------------------------------------------
    # Mot de passe oublié
    # ------------------------------------------------------------------
    def demander_reinitialisation(self, email: str) -> None:
        """Ne révèle jamais si l'email existe."""
        utilisateur = self.utilisateur_dao.find_by_email(email.strip().lower())
        if utilisateur is None or not utilisateur.actif:
            return
        jeton, hash_jeton = generer_jeton()
        self.jeton_dao.create(
            utilisateur.id, TypeJeton.REINITIALISATION_MDP, hash_jeton, DUREE_JETON_REINITIALISATION
        )
        lien = f"{settings.frontend_url}/reinitialisation?jeton={jeton}"
        envoyer_email_reinitialisation(
            utilisateur.email,
            utilisateur.prenom,
            lien,
            datetime.now(timezone.utc) + DUREE_JETON_REINITIALISATION,
        )

    def reinitialiser_mot_de_passe(self, jeton: str, nouveau_mdp: str) -> None:
        """Consomme le jeton et change le mot de passe en une seule opération SQL.
        Le DAO pose aussi mot_de_passe_change_le : toutes les sessions existantes sont invalidées."""
        resultat = self.jeton_dao.reinitialiser_mot_de_passe(
            hacher_jeton(jeton), hasher_mot_de_passe(nouveau_mdp)
        )
        if resultat is None:
            raise ValidationError({"jeton": ["Lien invalide ou expiré."]})

    # ------------------------------------------------------------------
    # Profil, onboarding, consentements
    # ------------------------------------------------------------------
    def find_by_id(self, utilisateur_id: UUID) -> Utilisateur:
        utilisateur = self.utilisateur_dao.find_by_id(utilisateur_id)
        if utilisateur is None:
            raise UtilisateurIntrouvableError("Utilisateur introuvable.")
        return utilisateur

    def modifier_profil(self, utilisateur_id: UUID, donnees: dict) -> Utilisateur:
        try:
            return self.utilisateur_dao.update(utilisateur_id, donnees)
        except ValueError:
            raise UtilisateurIntrouvableError("Utilisateur introuvable.")

    def terminer_onboarding(self, utilisateur_id: UUID) -> None:
        self.utilisateur_dao.marquer_onboarding_termine(utilisateur_id)

    def lire_consentements(self, utilisateur_id: UUID) -> dict[str, bool]:
        return self.utilisateur_dao.find_consentements(utilisateur_id)

    def modifier_consentement(
        self, utilisateur_id: UUID, type_consentement: str, accorde: bool
    ) -> dict[str, bool]:
        # Le schéma n'autorise que personnalisation et localisation ; on le
        # revérifie ici pour que « politique » ne puisse jamais être retiré.
        if type_consentement not in ("personnalisation", "localisation"):
            raise ValidationError({"type": ["Consentement non modifiable."]})
        self.utilisateur_dao.upsert_consentement(utilisateur_id, type_consentement, accorde)
        return self.utilisateur_dao.find_consentements(utilisateur_id)

    # ------------------------------------------------------------------
    # Helpers internes
    # ------------------------------------------------------------------
    def _envoyer_lien_activation(self, utilisateur: Utilisateur) -> None:
        jeton, hash_jeton = generer_jeton()
        self.jeton_dao.create(utilisateur.id, TypeJeton.ACTIVATION, hash_jeton, DUREE_JETON_ACTIVATION)
        lien = f"{settings.frontend_url}/activation?jeton={jeton}"
        # Ne lève jamais : un échec d'envoi est journalisé par smtp_email et
        # n'empêche pas la création du compte (l'utilisateur peut redemander l'email).
        envoyer_email_activation(
            utilisateur.email,
            utilisateur.prenom,
            lien,
            datetime.now(timezone.utc) + DUREE_JETON_ACTIVATION,
        )