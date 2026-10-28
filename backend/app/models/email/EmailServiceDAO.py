from typing import Optional

from app.database.initdb import get_db_cursor
from app.models.email.EmailServiceInterface import EmailEnvoyeInterface


class EmailEnvoyeDAO(EmailEnvoyeInterface):

    def journaliser(
        self,
        type_email: str,
        destinataire: str,
        sujet: str,
        statut: str,
        erreur: Optional[str] = None,
    ) -> None:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO email_envoye (type, destinataire, sujet, statut, erreur)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (type_email, destinataire, sujet, statut, erreur),
            )

    def supprimer_anciens(self, jours: int = 90) -> int:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "DELETE FROM email_envoye WHERE cree_le < NOW() - make_interval(days => %s);",
                (jours,),
            )
            return cursor.rowcount