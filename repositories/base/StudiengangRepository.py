from __future__ import annotations
from abc import ABC, abstractmethod
from domain.Domainklassen import Studiengang

class StudiengangRepository(ABC):
    """Abstrakte Repository Klasse. Diese Klasse definiert, welche Methoden ein Repository anbieten muss.
    Wie die Daten gespeichert werden, wird hier bewusst nicht festgelegt"""

    @abstractmethod
    def lade_alle(self) -> list[Studiengang]:
        """Lädt alle Studiengänge aus einer Datenquelle."""
        pass

    @abstractmethod
    def speichere(self, studiengang: Studiengang) -> None:
        """Speichert einen Studiengang in einer Datenquelle."""
        pass
    
    @abstractmethod
    def lösche(self, studiengang_name: str) -> None:
        """Löscht einen Studiengang in einer Datenquelle."""
        pass