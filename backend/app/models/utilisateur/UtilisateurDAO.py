from typing import Optional
from uuid import UUID

from psycopg2.errors import UniqueViolation

from app.database.initdb import get_db_cursor
from app.models.utilisateur.Utilisateur import NouvelUtilisateur, Utilisateur
from app.models.utilisateur.UtilisateurInterface import UtilisateurInterface
from app.utils.exceptions import EmailDejaUtiliseError

# Colonnes renvoyées par toutes les méthodes, sauf find_for_authentication.
# Le hash est présent mais à NULL, pour que Utilisateur.from_row garde la même
# forme de ligne sans jamais recevoir le mot de passe haché.
COLONNES_SANS_SECRETS = """
    id, email, nom, prenom, role, actif, onboarding_termine, simule, demo,
    derniere_connexion, mot_de_passe_change_le, cree_le, modifie_le,
    NULL::text AS mot_de_passe_hash
"""

# Réservé à l'authentification : colonnes explicites (pas de SELECT *),
# pour ne rien exposer si une colonne est ajoutée plus tard.
COLONNES_AUTHENTIFICATION = """
    id, email, nom, prenom, role, actif, onboarding_termine, simule, demo,
    derniere_connexion, mot_de_passe_change_le, cree_le, modifie_le, mot_de_passe_hash
"""

TYPES_CONSENTEMENT = ("politique", "personnalisation", "localisation")


class UtilisateurDAO(UtilisateurInterface):

    def create(self, nouvel: NouvelUtilisateur, consentements: dict[str, bool]) -> Utilisateur:
        # Un seul with : utilisateur + consentements sont validés ou annulés ensemble.
        # id, actif, cree_le... viennent des valeurs par défaut de la base.
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe_hash, role)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING {COLONNES_SANS_SECRETS};
                    """,
                    (
                        nouvel.nom,
                        nouvel.prenom,
                        nouvel.email,
                        nouvel.mot_de_passe_hash,
                        nouvel.role.value,
                    ),
                )
                row = cursor.fetchone()

                cursor.executemany(
                    """
                    INSERT INTO consentements (utilisateur_id, type, accorde)
                    VALUES (%s, %s::type_consentement, %s);
                    """,
                    [(row["id"], type_c, accorde) for type_c, accorde in consentements.items()],
                )
                return Utilisateur.from_row(row)
        except UniqueViolation:
            raise EmailDejaUtiliseError("Cet email est déjà utilisé.")

    def find_by_id(self, utilisateur_id: UUID) -> Optional[Utilisateur]:
        with get_db_cursor() as cursor:
            cursor.execute(
                f"SELECT {COLONNES_SANS_SECRETS} FROM utilisateurs WHERE id = %s;",
                (utilisateur_id,),
            )
            row = cursor.fetchone()
            return Utilisateur.from_row(row) if row else None

    def find_by_email(self, email: str) -> Optional[Utilisateur]:
        # LOWER(email) = LOWER(%s) : utilise l'index uq_utilisateurs_email
        with get_db_cursor() as cursor:
            cursor.execute(
                f"SELECT {COLONNES_SANS_SECRETS} FROM utilisateurs WHERE LOWER(email) = LOWER(%s);",
                (email,),
            )
            row = cursor.fetchone()
            return Utilisateur.from_row(row) if row else None

    def find_for_authentication(self, email: str) -> Optional[Utilisateur]:
        with get_db_cursor() as cursor:
            cursor.execute(
                f"SELECT {COLONNES_AUTHENTIFICATION} FROM utilisateurs WHERE LOWER(email) = LOWER(%s);",
                (email,),
            )
            row = cursor.fetchone()
            return Utilisateur.from_row(row) if row else None

    def email_existe(self, email: str) -> bool:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM utilisateurs WHERE LOWER(email) = LOWER(%s) LIMIT 1;",
                (email,),
            )
            return cursor.fetchone() is not None

    def update(self, utilisateur_id: UUID, donnees: dict) -> Utilisateur:
        # Construction dynamique mais sûre : seules les clés autorisées (whitelist)
        # peuvent devenir des colonnes, les valeurs restent toujours en paramètres.
        colonnes_autorisees = {"nom", "prenom"}
        champs = {cle: valeur for cle, valeur in donnees.items() if cle in colonnes_autorisees}

        if not champs:
            existant = self.find_by_id(utilisateur_id)
            if existant is None:
                raise ValueError("Utilisateur introuvable.")
            return existant

        set_clause = ", ".join(f"{cle} = %s" for cle in champs)
        valeurs = list(champs.values())
        valeurs.append(utilisateur_id)

        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                f"""
                UPDATE utilisateurs
                SET {set_clause}
                WHERE id = %s
                RETURNING {COLONNES_SANS_SECRETS};
                """,
                valeurs,
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError("Utilisateur introuvable.")
            return Utilisateur.from_row(row)

    def update_mot_de_passe(self, utilisateur_id: UUID, mot_de_passe_hash: str) -> Utilisateur:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                f"""
                UPDATE utilisateurs
                SET mot_de_passe_hash = %s, mot_de_passe_change_le = NOW()
                WHERE id = %s
                RETURNING {COLONNES_SANS_SECRETS};
                """,
                (mot_de_passe_hash, utilisateur_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError("Utilisateur introuvable.")
            return Utilisateur.from_row(row)

    def activer(self, utilisateur_id: UUID) -> Utilisateur:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                f"""
                UPDATE utilisateurs
                SET actif = TRUE
                WHERE id = %s
                RETURNING {COLONNES_SANS_SECRETS};
                """,
                (utilisateur_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError("Utilisateur introuvable.")
            return Utilisateur.from_row(row)

    def marquer_onboarding_termine(self, utilisateur_id: UUID) -> None:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE utilisateurs SET onboarding_termine = TRUE WHERE id = %s;",
                (utilisateur_id,),
            )

    def update_derniere_connexion(self, utilisateur_id: UUID) -> None:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE utilisateurs SET derniere_connexion = NOW() WHERE id = %s;",
                (utilisateur_id,),
            )

    def find_consentements(self, utilisateur_id: UUID) -> dict[str, bool]:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT type, accorde FROM consentements WHERE utilisateur_id = %s;",
                (utilisateur_id,),
            )
            accordes = {row["type"]: row["accorde"] for row in cursor.fetchall()}
        # Un type absent de la table vaut False
        return {type_c: accordes.get(type_c, False) for type_c in TYPES_CONSENTEMENT}

    def upsert_consentement(self, utilisateur_id: UUID, type_consentement: str, accorde: bool) -> None:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO consentements (utilisateur_id, type, accorde)
                VALUES (%s, %s::type_consentement, %s)
                ON CONFLICT (utilisateur_id, type)
                DO UPDATE SET accorde = EXCLUDED.accorde, modifie_le = NOW();
                """,
                (utilisateur_id, type_consentement, accorde),
            )

    def delete(self, utilisateur_id: UUID) -> None:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM utilisateurs WHERE id = %s;", (utilisateur_id,))
            if cursor.rowcount == 0:
                raise ValueError("Utilisateur introuvable.")