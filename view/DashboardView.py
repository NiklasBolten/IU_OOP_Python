from pathlib import Path
from controller.DashboardDTO import DashboardDTO

class DashboardView:
    """View: zuständig für die Darstellung, keine Berechnungslogik."""
    def __init__(self, dateipfad: str):
        self.dateipfad = Path(dateipfad)

    def zeige(self, daten: DashboardDTO) -> None:
        with self.dateipfad.open("r") as template:
            output = template.read()

            output = output.replace("${studiengang}", daten.studiengang)

    #TODO Versionierung von Modulen: Version mit in der Tabelle für aktive_module_prüfungen ausgeben

            rows = []
            for modul_name, prüfungen in daten.aktive_module_prüfungen.items():
                for i, prüfung in enumerate(prüfungen):
                    if i == 0:
                        name_zelle = f'<td rowspan="{len(prüfungen)}">{modul_name}</td>'
                    else:
                        name_zelle = ""  # rowspan übernimmt die Zelle

                    if prüfung["prüfungsform"] is None:
                        prüfungsform = "Nicht angegeben"
                    else:
                        prüfungsform = prüfung["prüfungsform"]
                    
                    if prüfung["prüfungsdatum"] is None:
                        prüfungsdatum = "TBA"
                    else:
                        prüfungsdatum = prüfung["prüfungsdatum"].strftime("%d.%m.%Y")

                    rows.append(
                        f"<tr>{name_zelle}"
                        f"<td>{prüfungsform}</td>"
                        f"<td>{prüfungsdatum}</td></tr>"
                    )

            aktive_module_name_liste = "\n".join(rows)
            output = output.replace("${aktive_module_name}", aktive_module_name_liste)

            output = output.replace("${gewünschter_notendurchschnitt}", str(daten.gewünschter_notendurchschnitt))

            output = output.replace("${aktueller_notendurchschnitt}", str(daten.aktueller_notendurchschnitt))

            if daten.benötigter_notendurchschnitt is None:
                output = output.replace("${benötigter_notendurchschnitt}", "Kein Modul übrig; Alle ECTS vergeben")
            elif daten.benötigter_notendurchschnitt < 1:
                output = output.replace("${benötigter_notendurchschnitt}", "Notendurchschnitt kann nicht mehr erreicht werden")
            elif daten.benötigter_notendurchschnitt > 6:
                output = output.replace("${benötigter_notendurchschnitt}", "Notendurchschnitt wird definitiv erreicht werden")
            else:
                output = output.replace("${benötigter_notendurchschnitt}", str(daten.benötigter_notendurchschnitt))
            
            # Anmerkung: Wenn in einem Studiengang noch nicht alle ECTS vergeben wurden, also Studiengang.ects_gesamt kleiner
            # als die Summe der ECTS der Module in Studiengang.module ist, wird in ${benötigter_notendurchschnitt} ein Wert
            # ausgegeben, obwohl ${anzahl_übrige_prüfungsleistungen} = 0 ist. Da dem Studiengang zu dem Zeitpunkt noch
            # Module hinzugefügt werden können (wodurch ${anzahl_übrige_prüfungsleistungen} ggf. steigen würde), ist das OK.

            output = output.replace("${anzahl_übrige_prüfungsleistungen}", str(daten.anzahl_übrige_prüfungsleistungen))

            output = output.replace("${studiengang_ende}", daten.studiengang_ende.strftime("%d.%m.%Y"))

            if daten.verstrichene_tage_anteil > 100:
                output = output.replace("${verstrichene_tage_anteil}", "100")
            elif daten.verstrichene_tage_anteil < 0:
                output = output.replace("${verstrichene_tage_anteil}", "0")
            else:
                output = output.replace("${verstrichene_tage_anteil}", str(daten.verstrichene_tage_anteil))

            output = output.replace("${ects_erreicht_anteil}", str(daten.ects_erreicht_anteil))

            #aktive_module_prüfungen: dict[str, list[dict[str, str]]] # {"Modul.name": ["prüfungsform": ..., "prüfungsdatum": ...]}
            #gewünschter_notendurchschnitt: float
            #aktueller_notendurchschnitt: float
            #benötigter_notendurchschnitt: float
            #anzahl_übrige_prüfungsleistungen: int
            #studiengang_ende: datetime.date
            #verstrichene_tage_anteil: float
            #ects_erreicht_anteil: float

            with open("output/index.html", "w") as outfile:
                outfile.write(output)

        #TODO: Wenn DashboardController mehrere Studiengänge ausgibt, Home page hinzufügen?