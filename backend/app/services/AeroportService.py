# app/services/AeroportService.py
from app.models.aeroport.Aeroport import Aeroport
from app.models.aeroport.AeroportInterface import AeroportInterface
from app.utils.exceptions import ValidationError

LIMITE_MAX = 20
LONGUEUR_MIN_RECHERCHE = 2


class AeroportService:

    def __init__(self, aeroport_dao: AeroportInterface):
        self.aeroport_dao = aeroport_dao

    def rechercher(self, q: str, limite: int = 10) -> list[Aeroport]:
        """Autocomplétion (US9). Renvoie [] si q a moins de 2 caractères
        (le schéma renvoie déjà un 422 en amont ; ce garde-fou protège les
        appels internes). La limite est bornée entre 1 et 20."""
        q = " ".join((q or "").split())
        if len(q) < LONGUEUR_MIN_RECHERCHE:
            return []
        return self.aeroport_dao.rechercher(q, min(max(limite, 1), LIMITE_MAX))

    def lire(self, code_iata: str) -> Aeroport:
        """Un aéroport par son code IATA. Lève ValidationError si inconnu
        (HTTP 400 comme les autres erreurs métier, avec le champ en cause)."""
        aeroport = self.aeroport_dao.find_by_code(code_iata)
        if aeroport is None:
            raise ValidationError({"aeroport": [f"Aéroport inconnu : {code_iata}."]})
        return aeroport

    def verifier_codes(self, **codes: str | None) -> None:
        """Vérifie plusieurs codes IATA d'un coup, pour valider une recherche
        (US9) avant d'écrire dans `recherches` : sans cela, la clé étrangère
        lèverait une erreur SQL 500 au lieu d'un message lisible.
        Usage : service.verifier_codes(origine="CDG", destination="JFK").
        Les valeurs None sont ignorées. Lève ValidationError avec une erreur
        par champ invalide."""
        erreurs: dict[str, list[str]] = {}
        for champ, code in codes.items():
            if code is None:
                continue
            if self.aeroport_dao.find_by_code(code) is None:
                erreurs[champ] = [f"Aéroport inconnu : {code}."]
        if erreurs:
            raise ValidationError(erreurs)

    def plus_proche(self, latitude: float, longitude: float) -> Aeroport | None:
        """Aéroport le plus proche d'une position (US10, lot 2).
        Vérifie seulement que les coordonnées sont plausibles."""
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValidationError({"position": ["Coordonnées invalides."]})
        return self.aeroport_dao.find_plus_proche(latitude, longitude)