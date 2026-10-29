# app/models/aeroport/AeroportInterface.py
from abc import ABC, abstractmethod
from typing import Optional

from app.models.aeroport.Aeroport import Aeroport


class AeroportInterface(ABC):

    @abstractmethod
    def rechercher(self, q: str, limite: int = 10) -> list[Aeroport]:
        """Autocomplétion (US9). Cherche dans code_iata, nom, ville et nom du pays
        (LEFT JOIN pays, alias SQL `nom_pays`), sans tenir compte de la casse
        (et des accents si l'extension unaccent est active).
        Tri : code IATA exact, puis ville commençant par q, puis le reste.
        `q` est toujours passé en paramètre (%s), avec % et _ échappés :
        jamais concaténé dans le SQL. Renvoie [] si rien ne correspond."""

    @abstractmethod
    def find_by_code(self, code_iata: str) -> Optional[Aeroport]:
        """Un aéroport par son code IATA (insensible à la casse), avec nom_pays.
        Sert à valider origine/destination d'une recherche (US9) et à
        afficher la fiche d'un vol (US20). None si le code est inconnu."""

    @abstractmethod
    def find_plus_proche(self, latitude: float, longitude: float) -> Optional[Aeroport]:
        """Aéroport le plus proche d'une position (US10), calculé sur
        latitude/longitude. Ignore les aéroports sans coordonnées. None si aucun."""