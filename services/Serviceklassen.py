import datetime
from dateutil.relativedelta import relativedelta

class AktiveModuleService:
    """Service-Klasse: überprüft, ob ein Modul aktiv ist. Für das "Aktive Module" Panel"""
    @staticmethod
    def prüfe_modul(studiengang, modul_kurscode: str) -> None:
        """Überprüft, ob ein Modul gerade aktiv, also angefangen, aber nicht abgeschlossen ist."""
        modul = None
        for m in studiengang.module:
            if m.kurscode == modul_kurscode:
                modul = m
        if modul == None:
            raise KeyError(f"Modul mit Kurscode: \"{modul_kurscode}\" nicht in Studiengang \"{studiengang.name}\" vertreten.")

        return True if modul.angefangen and not modul.abgeschlossen else False

    @staticmethod
    def ermittle_übrige_prüfungsleistungen(studiengang: Studiengang) -> list[Prüfungsleistung]:
        # Es sollen nur die Prüfungsleistungen aus Modulen betrachtet werden, die noch nicht abgeschlossen sind
        prüfungsleistungen_in_übrigen_modulen = [m.prüfungsleistungen for m in studiengang.module if not m.abgeschlossen]
        # Es wird eine Liste aus Listen mit Prüfungsleistung-Objekten erstellt. Diese wird jetzt geflattened
        prüfungsleistungen_in_übrigen_modulen = NotenService._flatten(prüfungsleistungen_in_übrigen_modulen)
        # Eine Prüfungsleistung gilt als "übrig", wenn sie benotet wird und noch keine Note vergeben wurde 
        # (und sie zu einem nicht abgeschlossenen Modul gehört)
        übrige_prüfungsleistungen = [pl for pl in prüfungsleistungen_in_übrigen_modulen if pl.wird_benotet and pl.note is None]
        return übrige_prüfungsleistungen

class NotenService:
    """Service-Klasse: enthält fachliche Logik zur Berechnung von Noten. Für Das "Notendurchschnitt" Panel"""

    #TODO Versionierung von Modulen: überall sicherstellen, dass mit der korrekten Version gearbeitet wird

    @staticmethod
    def berechne_gesamtnote_modul(studiengang: Studiengang, modul_kurscode: str) -> float:
        # Modul ermitteln...
        studiengangmodul = None
        for m in studiengang.module:
            if m.kurscode == modul_kurscode:
                studiengangmodul = m
        if studiengangmodul == None:
            raise KeyError(f"Modul mit Kurscode: \"{modul_kurscode}\" nicht in Studiengang \"{studiengang.name}\" vertreten.")
        
        noten = [n.note * n.gewichtung for n in studiengangmodul.prüfungsleistungen if n.note is not None and n.wird_benotet == True]


        gewichtung_gesamt = [n.gewichtung for n in studiengangmodul.prüfungsleistungen if n.wird_benotet == True]

        if not noten:
            return None
        return round(sum(noten) / sum(gewichtung_gesamt), 2)

    @staticmethod
    def berechne_gesamtnote_studium(studiengang: Studiengang) -> float:
        summe_noten = 0
        anzahl_ects = 0
        if not studiengang.module:
            return None
        for m in studiengang.module:
            if m.abgeschlossen and m.prüfungsleistungen is not None:
                gesamtnote_modul = NotenService.berechne_gesamtnote_modul(studiengang, m.kurscode)
                if gesamtnote_modul is not None: # Wenn das Modul benotete Prüfungsleistungen hat
                    summe_noten += gesamtnote_modul * m.ects
                    anzahl_ects += m.ects
        if anzahl_ects == 0: # Wenn Studiengang (noch) keine benoteten Module besitzt
            return None
        return round(summe_noten / anzahl_ects, 2)
    
    @staticmethod
    def _flatten(liste: list) -> list:
        flattened_list = [item for subliste in liste for item in subliste]
        return flattened_list

    @staticmethod
    def berechne_benötigten_notendurchschnitt(studiengang: Studiengang) -> float:
        gesamtnote_studium = NotenService.berechne_gesamtnote_studium(studiengang) # aktueller Durchschnitt
        if not gesamtnote_studium:
            gesamtnote_studium = 0
        ects_erreicht = EctsService.berechne_ects_erreicht(studiengang) # Gewichtung der bereits benoteten Module
        ects_übrig = studiengang.ects_gesamt - ects_erreicht # Gewichtung der übrigen Module
        if ects_übrig == 0:
            return None

        # benötigter Notendurchschnitt = (gewünschter Durchschnitt * Gesamtgewichtung -...
        #... aktueller Durchschnitt * Gewichtung der bereits benoteten Prüfungsleistungen) /...
        #... Gewichtung der übrigen Prüfungsleistungen

        benötigter_notendurchschnitt = ((
            studiengang.gewünschter_notendurchschnitt * studiengang.ects_gesamt
            - gesamtnote_studium * ects_erreicht)
            / ects_übrig)
        return round(benötigter_notendurchschnitt, 2)

class EctsService:
    """Service-Klasse: enthält fachliche Logik zu Berechnungen mit ECTS. Für das 
    "Abschluss des Studiums in X Jahren" Panel"""
    @staticmethod
    def berechne_ects_erreicht(studiengang: Studiengang) -> int:
        return sum(n.ects for n in studiengang.module if n.abgeschlossen)

    @staticmethod
    def berechne_ects_erreicht_anteil(studiengang: Studiengang) -> float:
        return round(EctsService.berechne_ects_erreicht(studiengang) / studiengang.ects_gesamt * 100, 2)

class ZeitService:
    """Service-Klasse: enthält fachliche Logik zu Berechnungen zur Zeit. Für das 
    "Abschluss des Studiums in X Jahren" Panel"""

    @staticmethod
    def berechne_geplantes_studienende(studiengang: Studiengang) -> datetime.date:
        """Alternative zu explizit gesetztem Studiengang.ende"""
        return studiengang.beginn + relativedelta(months = studiengang.ects_gesamt // 5)
    
    @staticmethod
    def berechne_gesamtlänge_studium_tage(studiengang: Studiengang) -> int:
        if not studiengang.ende:
            return (ZeitService.berechne_geplantes_studienende(studiengang) - studiengang.beginn).days
        else:
            return (studiengang.ende - studiengang.beginn).days
    
    @staticmethod
    def berechne_verstrichene_tage(studiengang: Studiengang) -> int:
        return (datetime.date.today() - studiengang.beginn).days

    @staticmethod
    def berechne_verstrichene_tage_anteil(studiengang: Studiengang) -> float:
        return round(ZeitService.berechne_verstrichene_tage(studiengang) / ZeitService.berechne_gesamtlänge_studium_tage(studiengang) * 100, 2)