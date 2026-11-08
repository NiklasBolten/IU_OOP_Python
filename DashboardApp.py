import datetime

from domain.Domainklassen import Studiengang, Modul, Wahlpflichtmodul, Pflichtwahlmodul, Prüfungsleistung
from controller.DashboardController import DashboardController
from view.DashboardView import DashboardView
from repositories.json.JSONStudiengangRepository import JSONStudiengangRepository
from repositories.json.JSONModulRepository import JSONModulRepository

daten_dateipfad = "daten/db.json"
view_dateipfad = "view/template.html"

class JSONDashboardApp:
    """Application Klasse mit JSON Repository."""

    def start(self, daten_dateipfad: str, view_dateipfad: str) -> None:
        modul_repo = JSONModulRepository(daten_dateipfad)
        repo = JSONStudiengangRepository(daten_dateipfad, modul_repo)
        view = DashboardView(view_dateipfad)
        controller = DashboardController(modul_repo, repo)

        daten = controller.lade_dashboard_daten()
        view.zeige(daten)

if __name__ == "__main__":
    JSONDashboardApp().start(daten_dateipfad, view_dateipfad)