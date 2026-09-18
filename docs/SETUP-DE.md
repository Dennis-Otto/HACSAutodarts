# Autodarts mit Home Assistant verknüpfen

**Für lokale Steuerung brauchst du keine Client-ID.** Wähle beim Hinzufügen der Integration **Lokales Board** und trage IP/Hostname sowie Port ein. Kalibrierung, Erkennung, Reset und weitere lokale Funktionen sind in der [Anleitung zur lokalen Steuerung](LOCAL-CONTROL.md) beschrieben.

Die folgenden Schritte betreffen die zusätzliche Cloud-Anmeldung für Spiel- und Matchdaten.

## Voraussetzungen für die Cloud-Anbindung

Die Cloud-Anbindung benötigt ein Autodarts-Konto mit Zugriff auf das Board und eine für diese Integration freigeschaltete **OAuth-Client-ID mit Geräteanmeldung**. Die Client-ID bezeichnet die Anwendung; sie ist keine E-Mail-Adresse, Board-ID oder ein Passwort. Die Anmeldung am eigenen Konto erfolgt anschließend über den angezeigten Code.

**Aktueller Stand:** Es ist noch keine freigeschaltete Projekt-Client-ID enthalten. Ohne eine gültige ID kann die Cloud-Anmeldung nicht abgeschlossen werden. Die lokale Board-Steuerung ist unabhängig davon nutzbar. Der bisherige Client `autodarts-play` unterstützt das neue Anmeldeverfahren nicht.

## Installation über HACS

1. In HACS die **benutzerdefinierten Repositories** öffnen.
2. `https://github.com/Dennis-Otto/HACSAutodarts` als Typ **Integration** hinzufügen.
3. Autodarts installieren und Home Assistant neu starten.
4. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **Autodarts** suchen.
5. **Cloud-Konto verknüpfen** wählen und die freigeschaltete Client-ID eintragen. Die lokale Board-IP ist optional. Ohne Client-ID stattdessen **Lokales Board** wählen.
6. Den angezeigten Link öffnen und die Verbindung bestätigen. Alternativ `https://auth.autodarts.io/link` aufrufen und den angezeigten achtstelligen Code eingeben; er kann mit Bindestrich als `ABCD-EFGH` dargestellt werden.
7. Home Assistant fährt nach der Freigabe automatisch fort. Falls nötig, das gewünschte Board auswählen.

## Bestehende Installation aktualisieren

Original und Fork verwenden beide den Integrationsnamen `autodarts` und können nicht parallel installiert werden. Stelle in HACS das liefernde Repository auf den Fork um bzw. ersetze manuell den Ordner `config/custom_components/autodarts`. Starte danach Home Assistant neu.

**Den bestehenden Eintrag unter Geräte & Dienste behalten.** Über **Neu konfigurieren → Lokales Board** kannst du die lokale Adresse hinterlegen oder ändern. Mit erreichbarem lokalem Board bleiben dessen Bedienelemente auch während einer ausstehenden Cloud-Anmeldung nutzbar. Ein Eintrag der bisherigen Version 2 fordert eine erneute Anmeldung an. Nach Eingabe der Client-ID und Freigabe bleiben Eintrags-ID, Board-Zuordnung, Sensor-IDs sowie lokale IP und Port erhalten. Verwende dasselbe Autodarts-Konto bzw. ein Konto mit Zugriff auf das bisherige Board.

## Häufige Meldungen

- **Client-ID abgelehnt:** Die ID ist ungültig oder nicht für die Geräteanmeldung freigeschaltet. Prüfe die eingegebene Client-ID für diese Integration. Ohne gültige ID ist die Einrichtung über **Lokales Board** möglich.
- **Code abgelaufen / Verknüpfung abgelehnt:** Den Anmeldevorgang neu starten und den neuen Code bestätigen.
- **Keine Boards:** Das angemeldete Konto hat keine Boards in der Board-Liste.
- **Falsches Konto bei erneuter Anmeldung:** Das bisherige Board ist in diesem Konto nicht vorhanden.
- **Autodarts nicht erreichbar:** Netzwerkverbindung prüfen und erneut versuchen. Temporäre Ausfälle beim Warten auf Freigabe werden bis zum Ablauf des Codes mit zunehmendem Abstand erneut geprüft.

## Prüfstand

Die automatischen Tests laufen mit Home Assistant 2026.9.2 und Python 3.14 mit simulierten Autodarts-Antworten. Lokale Lesezugriffe und der WebSocket-Verbindungsaufbau wurden mit Board Manager 1.0.7 geprüft. Die Hardwarevalidierung von Steueraktionen und Wurfereignissen sowie die Live-Validierung der Cloud-Anmeldung und Matchdaten stehen noch aus.
