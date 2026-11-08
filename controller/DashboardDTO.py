from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DashboardDTO:
    """DTO für die Übergabe vorbereiteter Dashboard-Daten."""

    #TODO Versionierung von Modulen: Annotation von aktive_module_prüfungen anpassen, sodass auch die Version ausgegeben wird

    studiengang: str
    aktive_module_prüfungen: dict[str, list[dict[str, str]]] # {"Modul.name": ["prüfungsform": ..., "prüfungsdatum": ...]}
    gewünschter_notendurchschnitt: float
    aktueller_notendurchschnitt: float
    benötigter_notendurchschnitt: float
    anzahl_übrige_prüfungsleistungen: int
    studiengang_ende: datetime.date
    verstrichene_tage_anteil: float
    ects_erreicht_anteil: float