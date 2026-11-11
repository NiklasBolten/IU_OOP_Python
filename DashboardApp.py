import datetime
import glob

from domain.Domainklassen import Studiengang, Modul, Wahlpflichtmodul, Pflichtwahlmodul, Prüfungsleistung
from controller.DashboardController import DashboardController
from view.DashboardView import DashboardView
from repositories.json.JSONStudiengangRepository import JSONStudiengangRepository
from repositories.json.JSONModulRepository import JSONModulRepository

view_dateipfad = "view/templates/template.html"
datenbanken = glob.glob("daten/*")

def nenne_daten_dateipfad() -> str:
    """Hilfsfunktion zur manuellen Auswahl der Datenbank; Zur leichteren Austestung des Prototypen hinzugefügt."""
    n = 0
    while n not in [m + 1 for m in range(len(datenbanken))]:
        print("Bitte wählen Sie aus, aus welcher Datenbank gelesen werden soll:")
        for m, db_name in enumerate(datenbanken):
            print(f"{m + 1}: {db_name}")
        try:
            n = int(input())
        except ValueError:
            print("Bitte geben Sie eine Zahl ein.")

    daten_dateipfad = datenbanken[int(n)-1]
    print("Der vollständige Dateipfad lautet: " + daten_dateipfad)
    return daten_dateipfad

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
    daten_dateipfad = nenne_daten_dateipfad()
    if daten_dateipfad[-5:] == ".json":
        JSONDashboardApp().start(daten_dateipfad, view_dateipfad)
    else:
        raise NotImplementedError("Bislang können nur JSON-Datenbanken verwendet werden.")