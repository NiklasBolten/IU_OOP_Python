from __future__ import annotations
from abc import ABC, abstractmethod
from domain.Domainklassen import Modul

class ModulRepository(ABC):
    """Abstrakte Repository Klasse. Diese Klasse definiert, welche Methoden ein Repository anbieten muss.
    Wie die Daten gespeichert werden, wird hier bewusst nicht festgelegt"""

    @abstractmethod
    def lade_alle(self) -> list[Modul]:
        """Lädt alle Module aus einer Datenquelle."""
        pass
    
    @abstractmethod
    def speichere(self, modul: Modul) -> None:
        """Speichert ein Modul in einer Datenquelle."""
        pass

    @abstractmethod
    def lösche(self, modul_kurscode: str) -> None:
        """Löscht ein Modul aus einer Datenquelle."""
        #TODO Versionierung von Modulen: sicherstellen, dass die richtige Version gelöscht wird -> Version als Argument hinzufügen
        pass