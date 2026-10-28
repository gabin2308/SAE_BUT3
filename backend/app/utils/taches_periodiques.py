# app/utils/taches_periodiques.py
import asyncio
import logging

from app.utils.maintenance import nettoyer_donnees_expirees

logger = logging.getLogger(__name__)

INTERVALLE_NETTOYAGE_SECONDES = 3600


async def _boucle() -> None:
    while True:
        try:
            # Les DAO sont synchrones (psycopg2) : un thread évite de bloquer la boucle d'événements.
            await asyncio.to_thread(nettoyer_donnees_expirees)
        except Exception:
            # Une erreur ponctuelle (base indisponible) ne doit jamais arrêter la boucle.
            logger.exception("Échec du nettoyage périodique")
        await asyncio.sleep(INTERVALLE_NETTOYAGE_SECONDES)


def demarrer() -> "asyncio.Task[None]":
    return asyncio.create_task(_boucle())