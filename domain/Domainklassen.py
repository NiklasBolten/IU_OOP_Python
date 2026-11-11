from __future__ import annotations
import datetime
from dateutil.relativedelta import relativedelta
from dataclasses import dataclass, field
from services.Serviceklassen import ZeitService

Prüfungsformen = {"Hausarbeit", "Seminararbeit", "Fallstudie", "Projektbericht", "Advanced Workbook", "Fachpräsentation", "Konzeptpräsentation", "Projektpräsentation", "Klausur", "Portfolio", "Bachelorarbeit", "Prüfung mündlich", "Praxisreflexion", "Projektbericht"}
Wahlpflichtmodule = {"DLBIKI01", "DLBINGDABD01", "DLBMIAMVR01", "DLBMIAMVR02", "DLBMIUID01-01", "DLBMIUID02"}
Pflichtwahlmodule = {"DLBMINPMI01", "DLBMINPMI02", "DLBMINPMI03", "LBEWAUP-01", "DLBSEPITI-01_D", "LBKPSGUV"}

@dataclass
class Prüfungsleistung:
    """Domain-Klasse: Prüfungsleistung; Kann sowohl in "Modul", als auch in "StudiengangModul" genutzt werden"""
    ID: int | None = field(default=None, init=False) # ID wird in Modul.prüfungsleistung_hinzufügen automatisch vergeben.
    prüfungsdatum: datetime.date = None
    prüfungsform: Prüfungsformen = None
    wird_benotet: bool = True
    note: float | None = field(default=None, init=False)
    abgeschlossen: bool | False = field(default=False, init=False)
    gewichtung: float = 1

    @classmethod
    def kopie(cls, vorlage: Prüfungsleistung) -> Prüfungsleistung: # Zum Hinzufügen von Prüfungsleistungen aus Modul.prüfungsleistungen in StudiengangModul.prüfungsleistungen
        kopierte_pl = cls(
            prüfungsform=vorlage.prüfungsform,
            wird_benotet=vorlage.wird_benotet,
            gewichtung=vorlage.gewichtung
        )
        kopierte_pl.ID = vorlage.ID
        return kopierte_pl

    def __post_init__(self) -> None:

        if self.prüfungsform != None and self.prüfungsform not in Prüfungsformen:
            raise ValueError("\"Prüfungsform\" muss ein Attribut aus diesem Set sein:" + str(Prüfungsformen))

        if self.note is not None:
            if self.note < 1 or self.note > 6:
                raise ValueError("\"note\" muss im Bereich zwischen 1.0 und 6.0 liegen")
        
        if self.gewichtung <= 0:
            raise ValueError("Gewichtung muss positiv sein.")

@dataclass
class Modul:
    """Domain-Klasse: Stammdaten für StudiengangModul"""

    #TODO Versionierung von Modulen: Attribut "Version" hinzufügen; Logik für Vergabe der Versionsnummer implementieren

    kurscode: str
    name: str
    ects: int = 5
    prüfungsleistungen: list["Prüfungsleistung"] = field(default_factory=list) # Speichert die Stammdaten der Prüfungsleistungen; Note und Prüfungsdatum bleiben hier "None"

    def prüfungsleistung_hinzufügen(self, prüfungsleistung: Prüfungsleistung) -> None:
        if not isinstance(prüfungsleistung, Prüfungsleistung):
            raise TypeError("\"prüfungsleistung\" muss eine Instanz der Klasse \"Prüfungsleistung\" sein.")
        if prüfungsleistung in self.prüfungsleistungen:
            raise ValueError("\"prüfungsleistung\" kann nicht mehrfach der Liste \"prüfungsleistungen\" hinzugefügt werden.")
        if prüfungsleistung.ID is not None:
            raise ValueError("\"prüfungsleistung\" kann nicht zu mehreren Modulen hinzugefügt werden.")
            
        # Vergabe der (lokalen) ID der Prüfungsleistung:
        id = max((p.ID for p in self.prüfungsleistungen), default = 0) + 1
        prüfungsleistung.ID=id

        self.prüfungsleistungen.append(prüfungsleistung)

    def prüfungsleistung_entfernen(self, ID: str) -> None:
        for pl in self.prüfungsleistungen:
            if pl.ID == ID:
                self.prüfungsleistungen.remove(pl)
                return
        # Wenn ID nicht in self.prüfungsleistungen:
        raise KeyError(f"Prüfungsleistung mit ID \"{ID}\" nicht in Modul {self.name} vertreten.")


@dataclass
class Wahlpflichtmodul(Modul):
    """Domain-Klasse: Stammdaten für StudiengangModul"""
    def __post_init__(self) -> None:
        if self.kurscode not in Wahlpflichtmodule:
            raise ValueError("\"kurscode\" muss ein Attribut aus diesem Set sein:" + str(Wahlpflichtmodule))

@dataclass
class Pflichtwahlmodul(Modul):
    """Domain-Klasse: Stammdaten für StudiengangModul"""
    def __post_init__(self) -> None:
        if self.kurscode not in Pflichtwahlmodule:
            raise ValueError("\"kurscode\" muss ein Attribut aus diesem Set sein:" + str(Pflichtwahlmodule))


@dataclass
class StudiengangModul:
    """Domain-Klasse: Modul innerhalb eines Studiengangs"""

    #TODO Versionierung von Modulen: Attribut "Version" hinzufügen

    kurscode: str
    name: str # "doppelt": Erleichtert Zugriff
    ects: int = 5 # "doppelt": Erleichtert Zugriff bei Berechnung von Noten und ECTS in den Serviceklassen
    semester: int | None = None
    angefangen: bool | False = field(default=False, init=False) # kann über Studiengang.modul_anfangen(modul_kurscode) auf True gesetzt werden
    abgeschlossen: bool | False = field(default=False, init=False) # kann über Studiengang.modul_abschließen(modul_kurscode) auf True gesetzt werden
    prüfungsleistungen: list["Prüfungsleistung"] = field(default_factory=list) #"doppelt": Hier wird auch benotet und ein Prüfungsdatum gesetzt.

    def __post_init__(self) -> None:
        if self.abgeschlossen:
            for pl in self.prüfungsleistungen:
                if pl.abgeschlossen == False:
                    raise ValueError(f"Nicht abgeschlossene Prüfungsleistung übrig: {pl}; Modul kann nicht abgeschlossen sein.")
        if self.semester:
            if self.semester > 12 or self.semester < 1:
                raise ValueError("\"Semester\" kann nur Werte zwischen 1 und 12 annehmen (oder None sein)")

@dataclass
class Studiengang:
    """Domain-Klasse: Gesamter Studiengang"""
    name: str
    beginn: datetime.date
    ende: datetime.date = None
    ects_gesamt: int = 180
    gewünschter_notendurchschnitt: float = 2.0
    module: list["StudiengangModul"] = field(default_factory=list)
    _ects_vergeben = 0

    def modul_hinzufügen(self, modul: Modul, semester=None) -> None:

        #TODO Versionierung von Modulen: Version aus Modul in StudiengangModul übertragen

        if not isinstance(modul, Modul):
            raise TypeError("\"modul\" muss eine Instanz der Klasse \"Modul\" sein.")
        
        studiengangmodul_kurscodes = [m.kurscode for m in self.module]
        if modul.kurscode in studiengangmodul_kurscodes:
            raise ValueError(f"Das Modul \"{modul.kurscode}\" kann nicht mehrfach dem Studiengang \"{self.name}\" hinzugefügt werden.")
        
        if self._ects_vergeben + modul.ects > self.ects_gesamt:
            raise ValueError(f"ECTS-Anzahl des Moduls \"" + modul.name + "\" überschreitet die Anzahl noch verfügbarer ECTS des Studiengangs")
        studiengangmodul = StudiengangModul(
            kurscode = modul.kurscode,
            name = modul.name,
            ects = modul.ects,
            semester = semester,
            prüfungsleistungen=[
                pl.kopie(pl)
                for pl in modul.prüfungsleistungen
            ]
        )
        self._ects_vergeben += modul.ects
        self.module.append(studiengangmodul)

    def modul_anfangen(self, modul_kurscode: str) -> None:
        # Modul ermitteln...
        studiengangmodul = None
        for m in self.module:
            if m.kurscode == modul_kurscode:
                studiengangmodul = m
        if studiengangmodul == None:
            raise KeyError(f"Modul mit Kurscode: \"{modul_kurscode}\" nicht in Studiengang \"{self.name}\" vertreten.")
        
        if studiengangmodul.angefangen == True:
            raise ValueError(f"Modul mit Kurscode: \"{modul_kurscode}\" wurde bereits angefangen")
        else:
            studiengangmodul.angefangen = True
    
    def prüfungsdatum_setzen(self, modul_kurscode: str, prüfungsleistung_id: int, prüfungsdatum: datetime.date) -> None:
        # Modul ermitteln...
        studiengangmodul = None
        for m in self.module:
            if m.kurscode == modul_kurscode:
                studiengangmodul = m
        if studiengangmodul == None:
            raise KeyError(f"Modul mit Kurscode: \"{modul_kurscode}\" nicht in Studiengang \"{self.name}\" vertreten.")

        if studiengangmodul.angefangen == False:
            raise ValueError(f"Modul mit Kurscode: \"{modul_kurscode}\" wurde noch nicht angefangen")
        
        # Prüfungsleistung ermitteln...
        prüfungsleistung = None
        for pl in studiengangmodul.prüfungsleistungen:
            if pl.ID == prüfungsleistung_id:
                prüfungsleistung = pl
        if prüfungsleistung == None:
            raise KeyError(f"Prüfungsleistung mit ID: \"{prüfungsleistung_id}\" nicht in Modul \"{studiengangmodul.kurscode}\" vertreten.")
        
        if not isinstance(prüfungsdatum, datetime.date):
            raise ValueError("Prüfungsdatum muss datetime.date sein.")
        if prüfungsdatum < self.beginn:
            raise ValueError("Prüfungsdatum liegt vor beginn des Studiengangs")
        prüfungsleistung.prüfungsdatum = prüfungsdatum

    def prüfungsleistung_abschließen(self, modul_kurscode: str, prüfungsleistung_id: int, note: float = None) -> None:
        # Modul ermitteln...
        studiengangmodul = None
        for m in self.module:
            if m.kurscode == modul_kurscode:
                studiengangmodul = m
        if studiengangmodul == None:
            raise KeyError(f"Modul mit Kurscode: \"{modul_kurscode}\" nicht in Studiengang \"{self.name}\" vertreten.")

        if studiengangmodul.angefangen == False:
            raise ValueError(f"Modul mit Kurscode: \"{modul_kurscode}\" wurde noch nicht angefangen")
        
        # Prüfungsleistung ermitteln...
        prüfungsleistung = None
        for pl in studiengangmodul.prüfungsleistungen:
            if pl.ID == prüfungsleistung_id:
                prüfungsleistung = pl
        if prüfungsleistung == None:
            raise KeyError(f"Prüfungsleistung mit ID: \"{prüfungsleistung_id}\" nicht in Modul \"{studiengangmodul.kurscode}\" vertreten.")
        
        if isinstance(note, float) or isinstance(note, int):
            note = float(note)
            # Note wurde vergeben, Prüfungsleistung ist benotbar
            if prüfungsleistung.wird_benotet == True:
                prüfungsleistung.note = note
                prüfungsleistung.abgeschlossen = True
            # Note wurde vergeben, Prüfungsleistung ist nicht benotbar
            elif prüfungsleistung.wird_benotet == False:
                raise ValueError(f"Prüfungsleistung mit ID: \"{prüfungsleistung_id}\" ist nicht benotbar.")
        elif note == None:
            # Note wurde nicht vergeben, Prüfungsleistung ist benotbar
            if prüfungsleistung.wird_benotet == True:
                raise ValueError(f"Prüfungsleistung mit ID: \"{prüfungsleistung_id}\" muss benotet werden.")
            # Note wurde nicht vergeben, Prüfungsleistung ist nicht benotbar
            elif prüfungsleistung.wird_benotet == False:
                prüfungsleistung.abgeschlossen = True
        else:
            raise TypeError(f"\"note\" muss vom Typ int, oder float sein, nicht {type(note)}")


    def modul_abschließen(self, modul_kurscode: str) -> None:
        # Modul ermitteln...
        studiengangmodul = None
        for m in self.module:
            if m.kurscode == modul_kurscode:
                studiengangmodul = m
        if studiengangmodul == None:
            raise KeyError(f"Modul mit Kurscode: \"{modul_kurscode}\" nicht in Studiengang \"{self.name}\" vertreten.")
        
        if studiengangmodul.angefangen == False:
            raise ValueError(f"Modul \"{modul_kurscode}\" kann nicht abgeschlossen sein, da es noch nicht angefangen wurde")
            # Überlegung: ein Modul kann nicht abgeschlossen sein, wenn es noch nicht angefangen wurde.
        
        for pl in studiengangmodul.prüfungsleistungen:
            if not pl.abgeschlossen:
                raise ValueError(f"Modul \"{modul_kurscode}\" kann nicht abgeschlossen sein, da Prüfungsleistung mit der ID {pl.ID} nicht abgeschlossen ist")
        
        studiengangmodul.abgeschlossen = True

    def modul_entfernen(self, modul_kurscode: str) -> None:
        for m in self.module:
            if m.kurscode == modul_kurscode:
                self.module.remove(m)
                return
        raise KeyError(f"Modul mit Kurscode: \"{modul_kurscode}\" nicht in Studiengang \"{self.name}\" vertreten.")

    def __post_init__(self) -> None:
        if self.ects_gesamt not in range(0, 360):
            raise ValueError("\"ects_gesamt\" muss zwischen 0 und 360 liegen.")
        if self.ende == None:
            self.ende = ZeitService.berechne_geplantes_studienende(self)