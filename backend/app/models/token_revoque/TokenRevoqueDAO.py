# app/models/token_revoque/TokenRevoqueDAO.py
from datetime import datetime
from typing import Literal
from uuid import UUID

from app.database.initdb import get_db_cursor
from app.models.token_revoque.TokenRevoqueInterface import TokenRevoqueInterface


class TokenRevoqueDAO(TokenRevoqueInterface):

    def est_revoque(self, jti: str) -> bool:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM tokens_revoques WHERE jti = %s LIMIT 1;",
                (jti,),
            )
            return cursor.fetchone() is not None

    def revoquer(
        self,
        jti: str,
        utilisateur_id: UUID,
        type_token: Literal["access", "refresh"],
        expire_le: datetime,
    ) -> bool:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO tokens_revoques (jti, utilisateur_id, type, expire_le)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (jti) DO NOTHING;
                """,
                (jti, utilisateur_id, type_token, expire_le),
            )
            # rowcount = 1 si inséré, 0 si le jti était déjà révoqué
            return cursor.rowcount == 1

    def supprimer_expires(self) -> int:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM tokens_revoques WHERE expire_le < NOW();")
            return cursor.rowcount