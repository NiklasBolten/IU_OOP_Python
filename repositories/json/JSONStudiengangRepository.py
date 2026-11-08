from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path

import json
import datetime

from domain.Domainklassen import Studiengang, Modul, Wahlpflichtmodul, Pflichtwahlmodul, Prüfungsleistung
from repositories.base.StudiengangRepository import StudiengangRepository
from repositories.base.ModulRepository import ModulRepository

class JSONStudiengangRepository(StudiengangRepository):
    """Konkretes Repository für JSON Dateien."""
    def __init__(self, dateipfad: str, modul_repo: ModulRepository): #Dependency Injection
        self.dateipfad = Path(dateipfad)
        self.modul_repo = modul_repo

    def lade_alle(self) -> list[Studiengang]:
        #TODO Versionierung von Modulen: sicherstellen, dass überall die Version aus den Stammdaten mit der Version aus den Instanzdaten übereinstimmt
        if not self.dateipfad.exists():
            return[]

        with self.dateipfad.open("r", encoding="utf-8") as datei:
            daten = json.load(datei)

        modul_stammdaten = self.modul_repo.lade_alle()
        studiengänge: list[Studiengang] = []
        if "Studiengänge" not in daten:
            raise KeyError(f""" Die Liste "Studiengänge" fehlt in {self.dateipfad}.""")
        for studiengang_daten in daten["Studiengänge"]:
            validierte_studiengang_daten = self._validiere_studiengang_daten(studiengang_daten) # validiert eine Studiengang-Instanz
            studiengang = Studiengang(
                name = validierte_studiengang_daten["name"],
                beginn = validierte_studiengang_daten["beginn"],
                ende =  validierte_studiengang_daten["ende"],
                ects_gesamt = validierte_studiengang_daten["ects_gesamt"],
                gewünschter_notendurchschnitt = validierte_studiengang_daten["gewünschter_notendurchschnitt"]
        )

            for modul_daten in studiengang_daten["module"]:
                validierte_modul_daten = self._validiere_modul_daten(modul_daten, validierte_studiengang_daten)
                studiengang_modul = None
                for modul in modul_stammdaten: # Module aus den Stammdaten der Module nach Kurscode durchsuchen
                # (hier wird auf die validierten Modul-Objekte aus self.modul_repo.lade_alle() zugegriffen)
                    if modul.kurscode == validierte_modul_daten["kurscode"]: # Bei passendem Kurscode Modul aus Stammdaten aufbauen
                        kwargs = dict(
                            name = modul.name,
                            ects = modul.ects,
                            kurscode = modul.kurscode,
                        )

                        if isinstance(modul, Wahlpflichtmodul):
                            studiengang_modul = Wahlpflichtmodul(**kwargs)
                        elif isinstance(modul, Pflichtwahlmodul):
                            studiengang_modul = Pflichtwahlmodul(**kwargs)
                        elif isinstance(modul, Modul):
                            studiengang_modul = Modul(**kwargs)
                        # Prüfungsleistungen aus Stammdaten aufbauen
                        for prüfungsleistung in modul.prüfungsleistungen:
                            modul_prüfungsleistung = Prüfungsleistung(
                                prüfungsform = prüfungsleistung.prüfungsform,
                                wird_benotet = prüfungsleistung.wird_benotet,
                                gewichtung = prüfungsleistung.gewichtung
                            )
                            studiengang_modul.prüfungsleistung_hinzufügen(modul_prüfungsleistung)
                if studiengang_modul is None:
                    raise ValueError(
                        f"In der db.json, im Studiengang {studiengang.name}, Modul Kurscode: {validierte_modul_daten["kurscode"]} "
                        f"nicht in der Modulliste gefunden."
                    )
                studiengang.modul_hinzufügen(studiengang_modul, validierte_modul_daten["semester"])

                # Module und Prüfungsleistungen innerhalb der Studiengang-Klasse über dessen Methoden einfügen

                # Wenn ein Modul in der db.json nicht angefangen und nicht abgeschlossen ist, aber bereits
                # "prüfungsdatum", "note", oder "abgeschlossen" in den Prüfungsleistungen eingetragen sind, werden diese
                # überschrieben. Ist das überhaupt ein Problem? Die betroffenen Attribute können in dem Kontext 
                # eh nur durch manuelles schreiben in die db.json verändert werden.

                if validierte_modul_daten["angefangen"] == True:
                    studiengang.modul_anfangen(validierte_modul_daten["kurscode"])
                    for prüfungsleistung_daten in modul_daten["prüfungsleistungen"]:
                        validierte_prüfungsleistung_daten = self._validiere_prüfungsleistung_daten(prüfungsleistung_daten,
                         validierte_modul_daten, validierte_studiengang_daten, modul_stammdaten)

                        if validierte_prüfungsleistung_daten["prüfungsdatum"]:
                                studiengang.prüfungsdatum_setzen(
                                    validierte_modul_daten["kurscode"],
                                    validierte_prüfungsleistung_daten["ID"],
                                    validierte_prüfungsleistung_daten["prüfungsdatum"]
                                )
                        if validierte_prüfungsleistung_daten["abgeschlossen"] == True:
                            studiengang.prüfungsleistung_abschließen(
                                validierte_modul_daten["kurscode"],
                                validierte_prüfungsleistung_daten["ID"],
                                validierte_prüfungsleistung_daten["note"]
                                )
                if validierte_modul_daten["abgeschlossen"] == True:
                    studiengang.modul_abschließen(validierte_modul_daten["kurscode"])
                    
            studiengänge.append(studiengang)
        return studiengänge

    def speichere(self, studiengang: Studiengang) -> None:
        
        if not isinstance(studiengang, Studiengang):
            raise TypeError(f"Die Funktion kann nur Studiengänge hinzufügen, nicht {type(studiengang)}")

        modul_stammdaten = self.modul_repo.lade_alle()
        studiengänge = self.lade_alle()

        for db_studiengang in studiengänge:
            if studiengang.name == db_studiengang.name:
                raise ValueError(f"Studiengang mit Name {studiengang.name} existiert bereits.")
        
        studiengänge.append(studiengang)
        
        studiengang_daten = [self._studiengang_als_dict(s) for s in studiengänge]

        #TODO Versionierung von Modulen: sicherstellen, dass die Version aus den Stammdaten mit der Version aus den Instanzdaten übereinstimmt

        for modul in studiengang.module:
            studiengang_modul = None
            for db_modul in modul_stammdaten:
                if db_modul.kurscode == modul.kurscode:
                    studiengang_modul = modul
            if studiengang_modul is None:
                raise ValueError(
                    f"Kurscode '{modul.kurscode}' in Studiengang '{studiengang.name}' "
                    f"nicht in der Modulliste gefunden."
                )

        with self.dateipfad.open("r", encoding="utf-8") as datei:
            daten = json.load(datei)

        daten["Studiengänge"] = studiengang_daten

        with self.dateipfad.open("w", encoding="utf-8") as datei:
            json.dump(daten, datei, ensure_ascii=False, indent=4)

    
    def lösche(self, studiengang_name: str) -> None:    
        studiengänge = self.lade_alle()

        name_vorhanden = False
        for studiengang in studiengänge[:]: #arbeitet mit Kopie der Liste, um doppelte Einträge korrekt zu behandeln 
            if studiengang_name == studiengang.name and not name_vorhanden:
                name_vorhanden = True
                studiengänge.remove(studiengang)
            elif studiengang_name == studiengang.name and name_vorhanden == True:
                # kann nur passieren, wenn db manuell bearbeitet wurde;
                # einfaches break nach entfernen des studiengangs wäre schneller, aber würde diesen Fehler ignorieren.
                raise ValueError(f"Studiengang mit Name {studiengang.name} doppelt in db.json vergeben.")

        
        if not name_vorhanden:
            raise KeyError(f"Studiengang \"{studiengang_name}\" nicht in db.json vorhanden.")
        
        studiengang_daten = [self._studiengang_als_dict(s) for s in studiengänge]

        with self.dateipfad.open("r", encoding="utf-8") as datei:
            daten = json.load(datei)

        daten["Studiengänge"] = studiengang_daten
        with self.dateipfad.open("w", encoding="utf-8") as datei:
            json.dump(daten, datei, ensure_ascii=False, indent=4)

    def _studiengang_als_dict(self, studiengang: Studiengang) -> dict: 

        #TODO Versionierung von Modulen: Version mit im dict ausgeben

        if isinstance(studiengang.ende, datetime.date):
            studiengang_ende = studiengang.ende.strftime("%Y-%m-%d")
        elif studiengang.ende is None:
            studiengang_ende = None
        else:
            raise TypeError(f"Studiengang.ende muss datetime.date-Objekt, oder None sein, nicht {type(studiengang.ende)}")

        prüfungsdatum_dict = {}
        for modul in studiengang.module:
            for pl in modul.prüfungsleistungen:
                if isinstance(pl.prüfungsdatum, datetime.date):
                     pl_prüfungsdatum = pl.prüfungsdatum.strftime("%Y-%m-%d")
                     prüfungsdatum_dict[pl.ID] = pl_prüfungsdatum
                elif pl.prüfungsdatum is None:
                    pl_prüfungsdatum = None
                    prüfungsdatum_dict[pl.ID] = pl_prüfungsdatum
                else:
                    raise TypeError(f"Prüfungsleistung.prüfungsdatum muss datetime.date-Objekt, oder None sein, nicht {type(pl.prüfungsdatum)}")
        
        return {
            "name": studiengang.name,
            "beginn": studiengang.beginn.strftime("%Y-%m-%d"),
            "ende": studiengang_ende,
            "ects_gesamt": studiengang.ects_gesamt,
            "gewünschter_notendurchschnitt": studiengang.gewünschter_notendurchschnitt,
            "module": [
                {
                    "kurscode": modul.kurscode,
                    "semester": modul.semester,
                    "angefangen": modul.angefangen,
                    "abgeschlossen": modul.abgeschlossen,
                    "prüfungsleistungen": [
                        {
                            "ID": prüfungsleistung.ID,
                            "prüfungsform": prüfungsleistung.prüfungsform,
                            "prüfungsdatum": prüfungsdatum_dict[prüfungsleistung.ID],
                            "wird_benotet": prüfungsleistung.wird_benotet,
                            "note": prüfungsleistung.note,
                            "abgeschlossen": prüfungsleistung.abgeschlossen,
                            "gewichtung": prüfungsleistung.gewichtung
                        }
                        for prüfungsleistung in modul.prüfungsleistungen
                    ]
                } for modul in studiengang.module
            ]
        }

    def _validiere_studiengang_daten(self, studiengang_daten: dict) -> dict:
        """Validiert und formatiert alle Daten aus einer Instanz der Liste "Studiengänge" in db.json, bis auf module"""
        # Überprüfung, ob alle Keys für einen Studiengang in der db.json vorhanden sind
        keys = ["name", "beginn", "ende", "ects_gesamt", "gewünschter_notendurchschnitt", "module"]
        fehlende_keys = [key for key in keys if key not in studiengang_daten]
        if fehlende_keys:
            raise KeyError(
                f"In der db.json fehlen einem Studiengang folgende Keys: {fehlende_keys}. "
                f"Dieser Studiengang ist betroffen: {studiengang_daten}" # ggf. sensible Daten?
            )
        
        # Typ- und Formatprüfungen für die Daten eines Studiengangs in der db.json, ohne "module[]"
        if not isinstance(studiengang_daten["name"], str):
            raise TypeError(
                f"In der db.json ist der name eines Studiengangs falsch formatiert: {studiengang_daten["name"]} "
                f"- es muss ein String sein.")
        studiengang_name = studiengang_daten["name"]

        if not isinstance(studiengang_daten["beginn"], str):
            raise TypeError(
                f"In der db.json, im Studiengang {studiengang_daten["name"]} ist \"beginn\" falsch formatiert "
                f"- Es ist kein String. Richtiges Format: \"YYYY-MM-DD\""
                )
        try:
            studiengang_beginn = datetime.date.fromisoformat(studiengang_daten["beginn"])
        except ValueError as e:
            raise ValueError(
                f"In der db.json, im Studiengang {studiengang_daten["name"]} ist \"beginn\" falsch formatiert "
                f"- Es ist ein String, aber im im falschen Format für ein Datum. Richtiges Format: \"YYYY-MM-DD\""
                ) from e
            
        if studiengang_daten["ende"] == None:
            studiengang_ende = None
        else:
            try:
                studiengang_ende = datetime.date.fromisoformat(studiengang_daten["ende"])
            except ValueError as e:
                raise ValueError(
                    f"In der db.json, im Studiengang {studiengang_daten["name"]} ist \"ende\" falsch formatiert "
                    f"- Es ist ein String, aber im im falschen Format für ein Datum. Richtiges Format: \"YYYY-MM-DD\", oder null"
                    ) from e
            except TypeError as e:
                raise TypeError(
                    f"In der db.json, im Studiengang {studiengang_daten["name"]} ist \"ende\" falsch formatiert "
                    f"- Es ist weder ein String, noch null. Richtiges Format: \"YYYY-MM-DD\", oder null"
                    ) from e
            
        if not isinstance(studiengang_daten["ects_gesamt"], int):
            raise TypeError(
                f"In der db.json, im Studiengang {studiengang_daten["name"]} ist \"ects_gesamt\" falsch formatiert "
                f"- es muss ein int sein.")
        studiengang_ects_gesamt = studiengang_daten["ects_gesamt"]

        if not isinstance(studiengang_daten["gewünschter_notendurchschnitt"], float):
            raise TypeError(
                f"In der db.json, im Studiengang {studiengang_daten["name"]} ist \"gewünschter_notendurchschnitt\" falsch formatiert "
                f"- es muss ein float sein.")
        studiengang_gewünschter_notendurchschnitt = studiengang_daten["gewünschter_notendurchschnitt"]
        return {
            "name": studiengang_name,
            "beginn": studiengang_beginn,
            "ende": studiengang_ende,
            "ects_gesamt": studiengang_ects_gesamt,
            "gewünschter_notendurchschnitt": studiengang_gewünschter_notendurchschnitt
        }

    def _validiere_modul_daten(self, modul_daten: dict, validierte_studiengang_daten: dict) -> dict:
        """Validiert und formatiert alle Daten aus einer Instanz der Liste "module" aus einem Studiengang in db.json"""

        #TODO Versionierung von Modulen: sicherstellen, dass die Version aus den Stammdaten mit der Version aus den Instanzdaten 
        # bei der Validierung übereinstimmt

        # Überprüfung, ob alle Keys für ein Modul im Studiengang in der db.json vorhanden sind
        keys = ["kurscode", "semester", "angefangen", "abgeschlossen", "prüfungsleistungen"]
        fehlende_keys = [key for key in keys if key not in modul_daten]
        if fehlende_keys:
            raise KeyError(
                f"In der db.json fehlen einem Modul im Studiengang {validierte_studiengang_daten["name"]} folgende Keys: {fehlende_keys}. "
                f"Dieses Modul ist betroffen: {modul_daten}" # ggf. sensible Daten?
            )
        # Typ- und Formatprüfungen für die Daten eines Moduls im Studiengang in der db.json, ohne "prüfungsleistungen[]"
        if not isinstance(modul_daten["kurscode"], str):
            raise TypeError(
                f"In der db.json ist der Kurscode eines Moduls im Studiengang {validierte_studiengang_daten["name"]} falsch formatiert"
                f"- es muss ein string sein.")
        modul_kurscode = modul_daten["kurscode"]

        if not isinstance(modul_daten["semester"], int) and modul_daten["semester"] is not None:
            raise TypeError(
                f"In der db.json ist das Semester des Moduls mit Kurscode {modul_kurscode} im Studiengang {validierte_studiengang_daten["name"]} falsch formatiert"
                f"- es muss ein int, oder null sein.")
        modul_semester = modul_daten["semester"]

        if not isinstance(modul_daten["angefangen"], bool):
            raise TypeError(
                f"In der db.json ist der Key \"angefangen\" des Moduls mit Kurscode {modul_kurscode} im Studiengang {validierte_studiengang_daten["name"]} falsch formatiert"
                f"- es muss ein bool sein.")
        modul_angefangen = modul_daten["angefangen"]

        if not isinstance(modul_daten["abgeschlossen"], bool):
            raise TypeError(
                f"In der db.json ist der Key \"abgeschlossen\" des Moduls mit Kurscode {modul_kurscode} im Studiengang {validierte_studiengang_daten["name"]} falsch formatiert"
                f"- es muss ein bool sein.")
        modul_abgeschlossen = modul_daten["abgeschlossen"]

        return{
            "kurscode": modul_kurscode,
            "semester": modul_semester,
            "angefangen": modul_angefangen,
            "abgeschlossen": modul_abgeschlossen
        }
    
    def _validiere_prüfungsleistung_daten(self, prüfungsleistung_daten: dict, validierte_modul_daten: dict, validierte_studiengang_daten: dict
    , modul_stammdaten: list[Modul]) -> dict:
        """Validiert und formatiert alle Daten einer Prüfungsleistung aus einer Instanz der Liste "module" aus einem Studiengang in db.json"""
        # Überprüfung, ob alle Keys für eine Prüfungsleistung eines Moduls im Studiengang in der db.json vorhanden sind
        keys = ["ID", "prüfungsform", "prüfungsdatum", "wird_benotet", "note", "abgeschlossen", "gewichtung"]
        fehlende_keys = [key for key in keys if key not in prüfungsleistung_daten]
        if fehlende_keys:
            raise KeyError(
                f"In der db.json fehlen einer Prüfungsleistung im Modul mit Kurscode: {validierte_modul_daten["kurscode"]} "
                f"im Studiengang {validierte_studiengang_daten["name"]} folgende Keys: {fehlende_keys}. "
                f"Diese Prüfungsleistung ist betroffen: {prüfungsleistung_daten}" # ggf. sensible Daten?
            )

        # Typ- und Formatprüfungen für die Daten einer Prüfungsleistung eines Moduls im Studiengang in der db.json"
        if not isinstance(prüfungsleistung_daten["ID"], int):
            raise TypeError(
                f"In der db.json ist die ID einer Prüfungsleistung im Modul mit Kurscode {validierte_modul_daten["kurscode"]} "
                f"im Studiengang {validierte_studiengang_daten["name"]} falsch formatiert - es muss ein int sein.")
        prüfungsleistung_id = prüfungsleistung_daten["ID"]

        if not isinstance(prüfungsleistung_daten["prüfungsform"], str) and prüfungsleistung_daten["prüfungsform"] is not None:
            raise TypeError(
                f"In der db.json ist die Prüfungsform der Prüfungsleistung mit ID {prüfungsleistung_id} im Modul mit Kurscode {validierte_modul_daten["kurscode"]} "
                f"im Studiengang {validierte_studiengang_daten["name"]} falsch formatiert - es muss ein str, oder null sein.")
        prüfungsleistung_prüfungsform = prüfungsleistung_daten["prüfungsform"]
        
        if prüfungsleistung_daten["prüfungsdatum"] is None:
            prüfungsleistung_prüfungsdatum = None
        else:
            try:    
                prüfungsleistung_prüfungsdatum = datetime.date.fromisoformat(prüfungsleistung_daten["prüfungsdatum"])
            except ValueError:
                raise ValueError(
                    f"In der db.json, im Studiengang {validierte_studiengang_daten["name"]}, im Modul Kurscode: {validierte_modul_daten["kurscode"]}, "
                    f"in der Prüfungsleistung ID: {prüfungsleistung_id} ist das Prüfungsdatum falsch formatiert "
                    f"- Es ist ein String, aber im im falschen Format für ein Datum. Richtiges Format: \"YYYY-MM-DD\", oder null"
                    )
            except TypeError:
                raise TypeError(
                    f"In der db.json, im Studiengang {validierte_studiengang_daten["name"]}, im Modul Kurscode: {validierte_modul_daten["kurscode"]}, "
                    f"in der Prüfungsleistung ID: {prüfungsleistung_id} ist das Prüfungsdatum falsch formatiert "
                    f"- Es ist kein String. Richtiges Format: \"YYYY-MM-DD\", oder null"
                    )
    
        if not isinstance(prüfungsleistung_daten["wird_benotet"], bool):
            raise TypeError(
                f"In der db.json ist der Key \"wird_benotet\" der Prüfungsleistung mit ID {prüfungsleistung_id} im Modul mit Kurscode {validierte_modul_daten["kurscode"]} "
                f"im Studiengang {validierte_studiengang_daten["name"]} falsch formatiert - es muss ein bool sein.")
        prüfungsleistung_wird_benotet = prüfungsleistung_daten["wird_benotet"]

        if not isinstance(prüfungsleistung_daten["note"], float) and prüfungsleistung_daten["note"] is not None:
            raise TypeError(
                f"In der db.json ist der Key \"note\" der Prüfungsleistung mit ID {prüfungsleistung_id} im Modul mit Kurscode {validierte_modul_daten["kurscode"]} "
                f"im Studiengang {validierte_studiengang_daten["name"]} falsch formatiert - es muss ein float, oder null sein.")
        prüfungsleistung_note = prüfungsleistung_daten["note"]

        if not isinstance(prüfungsleistung_daten["abgeschlossen"], bool):
            raise TypeError(
                f"In der db.json ist der Key \"abgeschlossen\" der Prüfungsleistung mit ID {prüfungsleistung_id} im Modul mit Kurscode {validierte_modul_daten["kurscode"]} "
                f"im Studiengang {validierte_studiengang_daten["name"]} falsch formatiert - es muss ein bool sein.")
        prüfungsleistung_abgeschlossen = prüfungsleistung_daten["abgeschlossen"]

        if not isinstance(prüfungsleistung_daten["gewichtung"], float) and not isinstance(prüfungsleistung_daten["gewichtung"], int):
            raise TypeError(
                f"In der db.json ist der Key \"gewichtung\" der Prüfungsleistung mit ID {prüfungsleistung_id} im Modul mit Kurscode {validierte_modul_daten["kurscode"]} "
                f"im Studiengang {validierte_studiengang_daten["name"]} falsch formatiert - es muss ein float, oder int sein.")
        prüfungsleistung_gewichtung = prüfungsleistung_daten["gewichtung"]

        # Vergleich der Stammdaten einer Prüfungsleistung aus den Modul-Stammdaten mit den Daten einer Prüfungsleistung aus dem Studiengang

        for modul in modul_stammdaten:
            for pl_stammdaten in modul.prüfungsleistungen:
                if modul.kurscode == validierte_modul_daten["kurscode"] and prüfungsleistung_id == pl_stammdaten.ID:
                    if prüfungsleistung_prüfungsform != pl_stammdaten.prüfungsform:
                        raise ValueError(
                            f"In der db.json weicht die Prüfungsform der Prüfungsleistung mit ID {prüfungsleistung_id} im Modul mit Kurscode "
                            f"{validierte_modul_daten["kurscode"]} im Studiengang {validierte_studiengang_daten["name"]} von den Stammdaten "
                            f"ab: Im Studiengang: {prüfungsleistung_prüfungsform}; in den Stammdaten: {pl_stammdaten.prüfungsform:}")

                    if prüfungsleistung_wird_benotet != pl_stammdaten.wird_benotet:
                        raise ValueError(
                            f"In der db.json weicht das Attribut \"wird_benotet\" der Prüfungsleistung mit ID {prüfungsleistung_id} im Modul mit Kurscode "
                            f"{validierte_modul_daten["kurscode"]} im Studiengang {validierte_studiengang_daten["name"]} von den Stammdaten "
                            f"ab: Im Studiengang: {prüfungsleistung_wird_benotet}; in den Stammdaten: {pl_stammdaten.wird_benotet}")

                    if prüfungsleistung_gewichtung != pl_stammdaten.gewichtung:
                        raise ValueError(
                            f"In der db.json weicht die Gewichtung der Prüfungsleistung mit ID {prüfungsleistung_id} im Modul mit Kurscode "
                            f"{validierte_modul_daten["kurscode"]} im Studiengang {validierte_studiengang_daten["name"]} von den Stammdaten "
                            f"ab: Im Studiengang: {prüfungsleistung_gewichtung}; in den Stammdaten: {pl_stammdaten.gewichtung}")



        return{
            "ID": prüfungsleistung_id,
            "prüfungsform": prüfungsleistung_prüfungsform,
            "prüfungsdatum": prüfungsleistung_prüfungsdatum,
            "wird_benotet": prüfungsleistung_wird_benotet,
            "note": prüfungsleistung_note,
            "abgeschlossen": prüfungsleistung_abgeschlossen,
            "gewichtung": prüfungsleistung_gewichtung
        }