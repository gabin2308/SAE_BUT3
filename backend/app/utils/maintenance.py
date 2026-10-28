# app/utils/maintenance.py
import logging

from app.utils.dependencies import jeton_dao, token_revoque_dao, email_dao

logger = logging.getLogger(__name__)


def nettoyer_donnees_expirees() -> None:
    """Appelée au démarrage. Un échec de nettoyage ne doit jamais empêcher
    l'appli de démarrer : chaque étape est isolée."""
    etapes = (
        ("jetons", jeton_dao.supprimer_expires),
        ("tokens_revoques", token_revoque_dao.supprimer_expires),
        ("email_envoye", email_dao.supprimer_anciens),
    )
    for nom, supprimer in etapes:
        try:
            nb = supprimer()
            logger.info("Nettoyage %s : %s ligne(s) supprimée(s)", nom, nb)
        except Exception:
            logger.exception("Échec du nettoyage de %s", nom)