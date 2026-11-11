import datetime

from domain.Domainklassen import Studiengang, Modul, Wahlpflichtmodul, Pflichtwahlmodul, Prüfungsleistung
from services.Serviceklassen import AktiveModuleService, EctsService, NotenService, ZeitService
from repositories.json.JSONStudiengangRepository import JSONStudiengangRepository
from repositories.json.JSONModulRepository import JSONModulRepository

# Reines Test-Programm. Hier können fachliche Logik und die technische Implementierung der Datenhaltung ausgetestet werden.

daten_dateipfad = "daten/testdb.json" # Kann auch zu anderer db.json verlinkt werden;
# Muss nur dem Schema von "leer.json" entsprechen.

modul_repo = JSONModulRepository(daten_dateipfad)
repo = JSONStudiengangRepository(daten_dateipfad, modul_repo)

def erstelle_und_speichere_studiengang() -> None:
    """Stellt nur ein Beispiel dar, wie ein Studiengang aufgebaut werden kann.
    Zum Testen kann der Code gerne bearbeitet werden"""

    # Prüfungsleistung erstellen:
    pl1 = Prüfungsleistung(prüfungsform = "Fallstudie", gewichtung = 1)
    pl2 = Prüfungsleistung(gewichtung = 2)
    pl3 = Prüfungsleistung()

    # Modul erstellen:
    m1 = Modul(name="testmodul 1", kurscode="testmodul_kurscode 1", ects = 5)
    m2 = Modul(name="testmodul 2", kurscode="testmodul_kurscode 2", ects = 10)

    # Wahlpflichtmodul / Pflichtwahlmodul erstellen funktionieren genau so:
    # wp1 = Wahlpflichtmodul(name="testwpmodul", kurscode="testwpmodul_kurscode", ects = 5)
    # pw1 = Pflichtwahlmodul(name="testpwmodul", kurscode="testpwmodul_kurscode", ects = 5)

    # Prüfungsleistung zu dem Modul hinzufügen:
    m1.prüfungsleistung_hinzufügen(pl1)
    m1.prüfungsleistung_hinzufügen(pl2)

    m2.prüfungsleistung_hinzufügen(pl3)

    # Studiengang erstellen:
    s1 = Studiengang(name = "Teststudiengang", beginn = datetime.date(2026,4,1))

    # erstes Modul hinzufügen und abschließen:

    s1.modul_hinzufügen(m1, semester = 12)
    s1.modul_anfangen("testmodul_kurscode 1")
    
    s1.prüfungsdatum_setzen("testmodul_kurscode 1", 1, datetime.date(2026, 5, 1))
    s1.prüfungsleistung_abschließen("testmodul_kurscode 1", 1, 2.0)
    
    s1.prüfungsdatum_setzen("testmodul_kurscode 1", 2, datetime.date(2026, 6, 1))
    s1.prüfungsleistung_abschließen("testmodul_kurscode 1", 2, 1.0)
    
    s1.modul_abschließen("testmodul_kurscode 1")

    # zweites Modul hinzufügen und abschließen:

    s1.modul_hinzufügen(m2, semester=1)
    s1.modul_anfangen("testmodul_kurscode 2")
    
    s1.prüfungsdatum_setzen("testmodul_kurscode 2", 1, datetime.date(2026, 5, 1))
    s1.prüfungsleistung_abschließen("testmodul_kurscode 2", 1, 2.0)

    s1.modul_abschließen("testmodul_kurscode 2")

    # Module in db.json speichern:
    modul_repo.speichere(m1)
    modul_repo.speichere(m2)

    # Studiengang in db.json speichern:
    repo.speichere(s1)

def lade_modul(modul_kurscode: str) -> Modul:
    for modul in modul_repo.lade_alle():
        if modul.kurscode == modul_kurscode:
            return(modul)

def lade_studiengang(studiengang_name: str) -> Studiengang:
    for studiengang in repo.lade_alle():
        if studiengang.name == studiengang_name:
            return(studiengang)

def bearbeite_studiengang(studiengang_name: str) -> None:
    """Stellt nur ein Beispiel dar, wie ein Studiengang aus der db bearbeitet werden kann.
    Zum Testen kann der Code gerne bearbeitet werden."""
    s1 = lade_studiengang(studiengang_name)
    
    for modul in s1.module:
        if not modul.angefangen: 
            s1.modul_anfangen(modul.kurscode)

        s1.prüfungsdatum_setzen(modul.kurscode, 1, datetime.date(2027, 10, 2))

        if len(modul.prüfungsleistungen) == 1 and modul.prüfungsleistungen[0].wird_benotet:
            s1.prüfungsleistung_abschließen(modul.kurscode, 1, 2.2)
            s1.modul_abschließen(modul.kurscode)


    repo.lösche(studiengang_name)
    repo.speichere(s1)

def lösche_studiengang(studiengang_name: str) -> None:
    repo.lösche(studiengang_name)

def lösche_modul(modul_kurscode: str) -> None:
    modul_repo.lösche(modul_kurscode)



erstelle_und_speichere_studiengang()
# print(lade_modul("BBAK02"))
# print(lade_studiengang("Medizinische Informatik"))
# bearbeite_studiengang("Medizinische Informatik")