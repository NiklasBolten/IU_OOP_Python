from __future__ import annotations
from repositories.base.ModulRepository import ModulRepository
from repositories.base.StudiengangRepository import StudiengangRepository
from services.Serviceklassen import AktiveModuleService, EctsService, NotenService, ZeitService
from controller.DashboardDTO import DashboardDTO

class DashboardController:
    """Controller: vermittelt zwischen UI (View) und fachlicher Logik/Daten."""
    def __init__(self, modul_repository: ModulRepository, studiengang_repository: StudiengangRepository):
        self.modul_repository = modul_repository
        self.studiengang_repository = studiengang_repository
    
    def lade_dashboard_daten(self) -> DashboardDTO:
        allgemeine_module = self.modul_repository.lade_alle()
        studiengänge = self.studiengang_repository.lade_alle()
        studiengang = studiengänge[0] # TODO refactoring überlegen, wie mehrere Studiengänge effektiv ausgegeben werden können

        aktive_module = [m for m in studiengang.module if AktiveModuleService.prüfe_modul(studiengang, m.kurscode)]
        
        aktive_module_prüfungen = {}

        for modul in aktive_module:
            aktive_module_prüfungen[modul.name] = [
                {
                    "prüfungsform": p.prüfungsform,
                    "prüfungsdatum": p.prüfungsdatum
                }
                for p in modul.prüfungsleistungen
            ]

        aktueller_notendurchschnitt = NotenService.berechne_gesamtnote_studium(studiengang)
        benötigter_notendurchschnitt = NotenService.berechne_benötigten_notendurchschnitt(studiengang)
        anzahl_übrige_prüfungsleistungen = len(AktiveModuleService.ermittle_übrige_prüfungsleistungen(studiengang))
        verstrichene_tage_anteil = ZeitService.berechne_verstrichene_tage_anteil(studiengang)
        ects_erreicht_anteil = EctsService.berechne_ects_erreicht_anteil(studiengang)

        return DashboardDTO(
                studiengang = studiengang.name,
                aktive_module_prüfungen = aktive_module_prüfungen,
                gewünschter_notendurchschnitt = studiengang.gewünschter_notendurchschnitt,
                aktueller_notendurchschnitt = aktueller_notendurchschnitt,
                benötigter_notendurchschnitt = benötigter_notendurchschnitt,
                anzahl_übrige_prüfungsleistungen = anzahl_übrige_prüfungsleistungen,
                studiengang_ende = studiengang.ende,
                verstrichene_tage_anteil = verstrichene_tage_anteil,
                ects_erreicht_anteil = ects_erreicht_anteil
        )