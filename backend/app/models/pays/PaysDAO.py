# app/models/pays/PaysDAO.py
from typing import Optional

from app.database.initdb import get_db_cursor
from app.models.pays.Pays import Pays
from app.models.pays.PaysInterface import PaysInterface

COLONNES = "code_pays, nom, cree_le"


class PaysDAO(PaysInterface):

    def find_all(self) -> list[Pays]:
        with get_db_cursor() as cursor:
            cursor.execute(f"SELECT {COLONNES} FROM pays ORDER BY nom;")
            return [Pays.from_row(row) for row in cursor.fetchall()]

    def find_by_code(self, code_pays: str) -> Optional[Pays]:
        with get_db_cursor() as cursor:
            cursor.execute(
                f"SELECT {COLONNES} FROM pays WHERE code_pays = UPPER(%s);",
                (code_pays.strip(),),
            )
            row = cursor.fetchone()
            return Pays.from_row(row) if row else None