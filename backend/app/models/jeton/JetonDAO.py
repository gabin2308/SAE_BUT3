# app/models/jeton/jeton_dao.py
from datetime import timedelta
from typing import Optional
from uuid import UUID

from app.database.initdb import get_db_cursor
from app.models.jeton.Jeton import TypeJeton
from app.models.jeton.JetonInterface import JetonInterface


class JetonDAO(JetonInterface):

    def create(
        self, utilisateur_id: UUID, type_jeton: TypeJeton, hash_jeton: str, duree: timedelta
    ) -> None:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                UPDATE jetons
                SET utilise_le = NOW()
                WHERE utilisateur_id = %s AND type = %s::type_jeton AND utilise_le IS NULL;
                """,
                (utilisateur_id, type_jeton.value),
            )
            cursor.execute(
                """
                INSERT INTO jetons (utilisateur_id, type, hash_jeton, expire_le)
                VALUES (%s, %s::type_jeton, %s, NOW() + %s);
                """,
                (utilisateur_id, type_jeton.value, hash_jeton, duree),
            )

    def activer_compte(self, hash_jeton: str) -> Optional[UUID]:
        # Une seule instruction : le jeton ne peut pas être « brûlé » sans que le
        # compte soit activé, ni servir deux fois en cas de requêtes simultanées.
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                WITH jeton AS (
                    UPDATE jetons
                    SET utilise_le = NOW()
                    WHERE hash_jeton = %s
                      AND type = 'activation'
                      AND utilise_le IS NULL
                      AND expire_le > NOW()
                    RETURNING utilisateur_id
                )
                UPDATE utilisateurs u
                SET actif = TRUE
                FROM jeton
                WHERE u.id = jeton.utilisateur_id
                RETURNING u.id;
                """,
                (hash_jeton,),
            )
            row = cursor.fetchone()
            return row["id"] if row else None

    def reinitialiser_mot_de_passe(self, hash_jeton: str, nouveau_hash_mdp: str) -> Optional[UUID]:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                WITH jeton AS (
                    UPDATE jetons
                    SET utilise_le = NOW()
                    WHERE hash_jeton = %s
                      AND type = 'reinitialisation_mdp'
                      AND utilise_le IS NULL
                      AND expire_le > NOW()
                    RETURNING utilisateur_id
                )
                UPDATE utilisateurs u
                SET mot_de_passe_hash = %s, mot_de_passe_change_le = NOW()
                FROM jeton
                WHERE u.id = jeton.utilisateur_id
                RETURNING u.id;
                """,
                (hash_jeton, nouveau_hash_mdp),
            )
            row = cursor.fetchone()
            return row["id"] if row else None

    def supprimer_expires(self) -> int:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "DELETE FROM jetons WHERE expire_le < NOW() OR utilise_le IS NOT NULL;"
            )
            return cursor.rowcount