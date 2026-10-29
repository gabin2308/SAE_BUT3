# app/models/aeroport/AeroportDAO.py
from typing import Optional

from app.database.initdb import get_db_cursor
from app.models.aeroport.Aeroport import Aeroport
from app.models.aeroport.AeroportInterface import AeroportInterface

# Colonnes explicites + nom du pays (alias nom_pays attendu par Aeroport.from_row)
COLONNES = """
    a.code_iata, a.nom, a.ville, a.code_pays, a.latitude, a.longitude,
    p.nom AS nom_pays
"""
JOINTURE = "FROM aeroports a LEFT JOIN pays p ON p.code_pays = a.code_pays"


def _echapper_like(s: str) -> str:
    """% et _ ont un sens dans LIKE : on les neutralise (échappement par \\)."""
    return s.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")


class AeroportDAO(AeroportInterface):

    def rechercher(self, q: str, limite: int = 10) -> list[Aeroport]:
        # Si l'extension unaccent est active, remplace chaque champ par unaccent(champ)
        # et chaque paramètre par unaccent(%s) (voir la note après le code).
        propre = _echapper_like(q.strip())
        contient = f"%{propre}%"
        debut = f"{propre}%"

        with get_db_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT {COLONNES}
                {JOINTURE}
                WHERE a.code_iata ILIKE %s
                   OR a.nom       ILIKE %s
                   OR a.ville     ILIKE %s
                   OR p.nom       ILIKE %s
                ORDER BY
                    (UPPER(a.code_iata) = UPPER(%s)) DESC,
                    (a.ville ILIKE %s) DESC,
                    a.ville NULLS LAST,
                    a.nom
                LIMIT %s;
                """,
                (propre, contient, contient, contient, q.strip(), debut, limite),
            )
            return [Aeroport.from_row(row) for row in cursor.fetchall()]

    def find_by_code(self, code_iata: str) -> Optional[Aeroport]:
        with get_db_cursor() as cursor:
            cursor.execute(
                f"SELECT {COLONNES} {JOINTURE} WHERE a.code_iata = UPPER(%s);",
                (code_iata.strip(),),
            )
            row = cursor.fetchone()
            return Aeroport.from_row(row) if row else None

    def find_plus_proche(self, latitude: float, longitude: float) -> Optional[Aeroport]:
        # Distance approximative (sans PostGIS) : suffisante pour proposer un
        # aéroport que l'utilisateur confirme (US10).
        with get_db_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT {COLONNES}
                {JOINTURE}
                WHERE a.latitude IS NOT NULL AND a.longitude IS NOT NULL
                ORDER BY POWER(a.latitude - %s, 2)
                       + POWER((a.longitude - %s) * COS(RADIANS(%s)), 2)
                LIMIT 1;
                """,
                (latitude, longitude, latitude),
            )
            row = cursor.fetchone()
            return Aeroport.from_row(row) if row else None