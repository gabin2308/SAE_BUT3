# app/models/pays/PaysInterface.py
from abc import ABC, abstractmethod
from typing import Optional

from app.models.pays.Pays import Pays


class PaysInterface(ABC):

    @abstractmethod
    def find_all(self) -> list[Pays]:
        """Tous les pays, triés par nom. Liste courte (environ 250 lignes),
        sans pagination."""

    @abstractmethod
    def find_by_code(self, code_pays: str) -> Optional[Pays]:
        """Un pays par son code ISO alpha-2 (insensible à la casse). None si inconnu."""