from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path

import json

from domain.Domainklassen import Studiengang, Modul, Wahlpflichtmodul, Pflichtwahlmodul, Prüfungsleistung
from repositories.base.ModulRepository import ModulRepository

class JSONModulRepository(ModulRepository):
    """Konkretes Repository für JSON Dateien."""
    def __init__(self, dateipfad: str):
        self.dateipfad = Path(dateipfad)

    def lade_alle(self) -> list[Modul]:
        """Es wird nur mit der Liste "Module" aus der Datenquelle gearbeitet, die Liste "module" innerhalb
        der Liste "Studiengänge" wird nicht beachtet."""

        #TODO Versionierung von Modulen: sicherstellen, dass die Version existiert und korrekt vergeben ist
        
        if not self.dateipfad.exists():
            return[]

        with self.dateipfad.open("r", encoding="utf-8") as datei:
            daten = json.load(datei)

        module: list[Modul] = []
        if "Module" not in daten:
            raise KeyError(f""" Die Liste "Module" fehlt in {self.dateipfad}.""")
        for modul_daten in daten["Module"]:
            validierte_modul_daten = self._validiere_modul_daten(modul_daten)
            kwargs = dict(
                kurscode = validierte_modul_daten["kurscode"],
                name = validierte_modul_daten["name"],
                ects = validierte_modul_daten["ects"])
            if validierte_modul_daten["typ"] == "modul":
                modulklasse = Modul(**kwargs)
            elif validierte_modul_daten["typ"] == "pflichtwahlmodul":
                modulklasse = Pflichtwahlmodul(**kwargs)
            elif validierte_modul_daten["typ"] == "wahlpflichtmodul":
                modulklasse = Wahlpflichtmodul(**kwargs)
            else:
                raise TypeError(
                    f"""Das Modul {validierte_modul_daten["kurscode"]}: {validierte_modul_daten["name"]} hat einen unzulässigen typ: {validierte_modul_daten["typ"]}"""
                    )
            for prüfungsleistung_daten in modul_daten["prüfungsleistungen"]:
                validierte_prüfungsleistung_daten = self._validiere_prüfungsleistung_daten(prüfungsleistung_daten, validierte_modul_daten)
                prüfungsleistungklasse = Prüfungsleistung(
                    prüfungsform = validierte_prüfungsleistung_daten["prüfungsform"],
                    wird_benotet = validierte_prüfungsleistung_daten["wird_benotet"],
                    gewichtung = validierte_prüfungsleistung_daten["gewichtung"]
                )
                modulklasse.prüfungsleistung_hinzufügen(prüfungsleistungklasse)
            module.append(modulklasse)

        return module
    
    def speichere(self, modul: Modul) -> None:
        """Es wird nur mit der Liste "Module" aus der Datenquelle gearbeitet, die Liste "module" innerhalb
        der Liste "Studiengänge" wird nicht beachtet."""

        #TODO Versionierung von Modulen: sicherstellen, dass die Version noch nicht existiert und korrekt vergeben ist

        module = self.lade_alle()

        for db_modul in module:
            if modul.kurscode == db_modul.kurscode:
                raise ValueError(f"Modul mit Kurscode {modul.kurscode} existiert bereits.")

        modul_daten = [self._modul_als_dict(m) for m in module]
        
        prüfungsleistungen_dict_liste = []
        for pl in modul.prüfungsleistungen:
            prüfungsleistung_dict = {
                "ID": pl.ID,
                "prüfungsform": pl.prüfungsform,
                "wird_benotet": pl.wird_benotet,
                "gewichtung": pl.gewichtung
            }
            prüfungsleistungen_dict_liste.append(prüfungsleistung_dict)

        kwargs = dict(
            kurscode = modul.kurscode,
            name = modul.name,
            ects = modul.ects,
            prüfungsleistungen = prüfungsleistungen_dict_liste
            )

        if isinstance(modul, Wahlpflichtmodul):
            modul_dict = dict(typ = "wahlpflichtmodul", **kwargs)
        elif isinstance(modul, Pflichtwahlmodul):
            modul_dict = dict(typ = "pflichtwahlmodul", **kwargs)
        elif isinstance(modul, Modul):
            modul_dict = dict(typ = "modul", **kwargs)
        else:
            raise TypeError(
                    f"""Das Modul {modul.kurscode}: {modul.name} hat einen unzulässigen typ: {type(modul)}"""
                    )

        modul_daten.append(modul_dict)

        with self.dateipfad.open("r", encoding="utf-8") as datei:
            daten = json.load(datei)

        daten["Module"] = modul_daten
        with self.dateipfad.open("w", encoding="utf-8") as datei:
            json.dump(daten, datei, ensure_ascii=False, indent=4)
    

    def lösche(self, modul_kurscode: str) -> None:
        """Es wird nur mit der Liste "Module" aus der Datenquelle gearbeitet, die Liste "module" innerhalb
        der Liste "Studiengänge" wird nicht beachtet."""

        #TODO Versionierung von Modulen: sicherstellen, dass die richtige Version gelöscht wird

        module = self.lade_alle()

        kurscode_vorhanden = False
        for db_modul in module:
            if modul_kurscode == db_modul.kurscode:
                kurscode_vorhanden = True
                module.remove(db_modul)
        
        if not kurscode_vorhanden:
            raise KeyError(f"Kurscode {modul_kurscode} nicht in db.json vorhanden.")
        
        modul_daten = [self._modul_als_dict(m) for m in module]

        with self.dateipfad.open("r", encoding="utf-8") as datei:
            daten = json.load(datei)

        daten["Module"] = modul_daten
        with self.dateipfad.open("w", encoding="utf-8") as datei:
            json.dump(daten, datei, ensure_ascii=False, indent=4)

    def _modul_als_dict(self, modul: Modul) -> dict:
        if isinstance(modul, Wahlpflichtmodul):
            typ = "wahlpflichtmodul"
        elif isinstance(modul, Pflichtwahlmodul):
            typ = "pflichtwahlmodul"
        elif isinstance(modul, Modul):
            typ = "modul"

        #TODO Versionierung von Modulen: Version mit im dict ausgeben
        
        prüfungsleistungen = []
        for pl in modul.prüfungsleistungen:
            prüfungsleistung = {
                "ID": pl.ID,
                "prüfungsform": pl.prüfungsform,
                "wird_benotet": pl.wird_benotet,
                "gewichtung": pl.gewichtung
            }
            prüfungsleistungen.append(prüfungsleistung)

        
        return {
            "typ": typ,
            "kurscode": modul.kurscode,
            "name": modul.name,
            "ects": modul.ects,
            "prüfungsleistungen": prüfungsleistungen
        }

    def _validiere_modul_daten(self, modul_daten: dict) -> dict:
        """Validiert und formatiert alle Daten eines Moduls in db.json"""

        #TODO Versionierung von Modulen: Version validieren

        # Überprüfung, ob alle Keys für ein Modul in der db.json vorhanden sind
        keys = ["typ", "kurscode", "name", "ects"]
        fehlende_keys = [key for key in keys if key not in modul_daten]
        if fehlende_keys:
            raise KeyError(
                f"In der db.json fehlen einem Modul folgende Keys: {fehlende_keys}. "
                f"Dieses Modul ist betroffen: {modul_daten}" # ggf. sensible Daten?
            )

        # Typ- und Formatprüfungen für die Daten eines Moduls in der db.json"
        if not isinstance(modul_daten["kurscode"], str):
            raise TypeError(
                f"In der db.json ist der Kurscode in einem Modul "
                f"falsch formatiert: {modul_daten["kurscode"]} - es muss ein string sein.")
        modul_kurscode = modul_daten["kurscode"]


        if not isinstance(modul_daten["typ"], str):
            raise TypeError(
                f"In der db.json ist der Key \"typ\" im Modul mit Kurscode {modul_kurscode} "
                f"falsch formatiert - es muss ein string sein.")
        modul_typ = modul_daten["typ"]

        if not isinstance(modul_daten["name"], str):
            raise TypeError(
                f"In der db.json ist der Name im Modul mit Kurscode {modul_kurscode} "
                f"falsch formatiert - es muss ein string sein.")
        modul_name = modul_daten["name"]

        if not isinstance(modul_daten["ects"], int):
            raise TypeError(
                f"In der db.json ist der Key \"ects\" im Modul mit Kurscode {modul_kurscode} "
                f"falsch formatiert - es muss ein int sein.")
        modul_ects = modul_daten["ects"]
    
        return {
            "typ": modul_typ,
            "kurscode": modul_kurscode,
            "name": modul_name,
            "ects": modul_ects
        }

    def _validiere_prüfungsleistung_daten(self, prüfungsleistung_daten: dict, validierte_modul_daten: dict) -> dict:
        """Validiert und formatiert alle Daten einer Prüfungsleistung aus einem BasisModul in db.json"""

        #TODO Versionierung von Modulen: Version in den Errors mit angeben

        # Überprüfung, ob alle Keys für eine Prüfungsleistung eines BasisModuls in der db.json vorhanden sind
        keys = ["ID", "prüfungsform", "wird_benotet", "gewichtung"]
        fehlende_keys = [key for key in keys if key not in prüfungsleistung_daten]
        if fehlende_keys:
            raise KeyError(
                f"In der db.json fehlen einer Prüfungsleistung im Modul mit Kurscode: {validierte_modul_daten["kurscode"]} "
                f"folgende Keys: {fehlende_keys}. "
                f"Diese Prüfungsleistung ist betroffen: {prüfungsleistung}" # ggf. sensible Daten?
            )

        # Typ- und Formatprüfungen für die Daten einer Prüfungsleistung eines BasisModuls im Studiengang in der db.json"
        if not isinstance(prüfungsleistung_daten["ID"], int):
            raise TypeError(
                f"In der db.json ist die ID einer Prüfungsleistung im Modul mit Kurscode {validierte_modul_daten["kurscode"]} "
                f"falsch formatiert - es muss ein int sein.")
        prüfungsleistung_id = prüfungsleistung_daten["ID"]

        if not isinstance(prüfungsleistung_daten["prüfungsform"], str) and prüfungsleistung_daten["prüfungsform"] is not None:
            raise TypeError(
                f"In der db.json ist die Prüfungsform der Prüfungsleistung mit ID {prüfungsleistung_id} im Modul mit Kurscode {validierte_modul_daten["kurscode"]} "
                f"falsch formatiert - es muss ein str, oder null sein.")
        prüfungsleistung_prüfungsform = prüfungsleistung_daten["prüfungsform"]
    
        if not isinstance(prüfungsleistung_daten["wird_benotet"], bool):
            raise TypeError(
                f"In der db.json ist der Key \"wird_benotet\" der Prüfungsleistung mit ID {prüfungsleistung_id} im Modul mit Kurscode {validierte_modul_daten["kurscode"]} "
                f"falsch formatiert - es muss ein bool sein.")
        prüfungsleistung_wird_benotet = prüfungsleistung_daten["wird_benotet"]

        if not isinstance(prüfungsleistung_daten["gewichtung"], float) and not isinstance(prüfungsleistung_daten["gewichtung"], int):
            raise TypeError(
                f"In der db.json ist der Key \"gewichtung\" der Prüfungsleistung mit ID {prüfungsleistung_id} im Modul mit Kurscode {validierte_modul_daten["kurscode"]} "
                f"falsch formatiert - es muss ein float, oder int sein.")
        prüfungsleistung_gewichtung = prüfungsleistung_daten["gewichtung"]

        return{
            "ID": prüfungsleistung_id,
            "prüfungsform": prüfungsleistung_prüfungsform,
            "wird_benotet": prüfungsleistung_wird_benotet,
            "gewichtung": prüfungsleistung_gewichtung
        }