# app/services/PaysService.py
from app.models.pays.Pays import Pays
from app.models.pays.PaysInterface import PaysInterface
from app.utils.exceptions import ValidationError


class PaysService:

    def __init__(self, pays_dao: PaysInterface):
        self.pays_dao = pays_dao

    def lister(self) -> list[Pays]:
        """Tous les pays, triés par nom (environ 250 lignes, sans pagination)."""
        return self.pays_dao.find_all()

    def lire(self, code_pays: str) -> Pays:
        """Un pays par son code ISO alpha-2. Lève ValidationError si inconnu."""
        pays = self.pays_dao.find_by_code(code_pays)
        if pays is None:
            raise ValidationError({"pays": [f"Pays inconnu : {code_pays}."]})
        return pays