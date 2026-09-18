# Lokale Board-Steuerung

Ab Version 0.3.0 lässt sich HACSAutodarts direkt mit dem lokalen Board Manager verbinden. Eine Client-ID oder Cloud-Anmeldung in Home Assistant ist dafür nicht erforderlich. Voraussetzungen und Status der optionalen Cloud-Anbindung stehen in der [Einrichtungsanleitung](SETUP-DE.md).

Version **0.4.0** ergänzt Echtzeit-Ereignisse, weitere Zustände, Kalibrierung je Kamera, Kamerastörungen und eine gespeicherte lokale Trainingsstatistik. Für ein Update genügt die Aktualisierung der Integration mit anschließendem Home-Assistant-Neustart. Bestehende Einträge bleiben erhalten; die neuen Entitäten werden ergänzt.

## Einrichten

1. Den Fork über HACS aktualisieren bzw. `custom_components/autodarts` ersetzen und Home Assistant neu starten.
2. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Autodarts** öffnen.
3. **Lokales Board** wählen.
4. IP-Adresse oder Hostnamen eingeben, beispielsweise `192.168.1.50`, ohne `http://` und ohne Port. Port separat angeben, normalerweise **3180**.
5. Das Board wird anhand seiner bereits im Board Manager hinterlegten Board-ID zugeordnet.

Home Assistant muss diese Adresse erreichen können. Eine Verbindung vom Handy allein genügt nicht. Der Board Manager muss bereits eingerichtet sein. Seine eigene Registrierung bei Autodarts und seine Cloud-Verbindung sind von der Anmeldung dieser HA-Integration unabhängig.

Ist das Board schon in Home Assistant angelegt, den Eintrag behalten und **Neu konfigurieren → Lokales Board** verwenden. Eine andere Board-ID an der neuen Adresse wird abgewiesen. Die IDs bisheriger Sensoren bleiben erhalten.

Mit einer gültigen Client-ID für diese Integration lässt sich am selben Eintrag über **Neu konfigurieren → Cloud-Konto verknüpfen** die Cloud-Anbindung ergänzen. Ein zweiter Integrationseintrag ist nicht erforderlich.

## Buttons

| Button | Aktion | Standardmäßig aktiv |
|---|---|---|
| Erkennung starten | Startet die lokale Darterkennung | Ja |
| Erkennung stoppen | Stoppt die lokale Darterkennung | Ja |
| Erkennung zurücksetzen | Setzt die aktuelle Erkennung zurück | Ja |
| Board Manager neu starten | Sendet den Neustartbefehl des Board Managers | Ja |
| Automatische Kalibrierung starten | Startet die automatische Board-Kalibrierung | Ja |
| Kamera 1/2/3 … kalibrieren | Kalibriert gezielt die jeweilige Kamera einschließlich Verzerrungskorrektur | Ja |
| Trainingsstatistik zurücksetzen | Beginnt eine neue lokale Zählsitzung in Home Assistant | Ja |
| Mit Autodarts-Cloud verbinden | Verbindet den Board Manager mit seinem Upstream | Nein |
| Von Autodarts-Cloud trennen | Trennt die Upstream-Verbindung des Board Managers | Nein |
| Kamera-Streams starten | Aktiviert die vom Board Manager bereitgestellten Streams | Nein |
| Kamera-Streams stoppen | Stoppt diese Streams | Nein |

Die Board-Befehle wirken direkt auf das Board und können ein laufendes Spiel unterbrechen. Für die Kalibrierung das Board freimachen. „Erkennung starten“ startet die Erkennung; die Auswahl und Erstellung eines Spiels erfolgt weiterhin in Autodarts. Der Neustartbutton ist kein Neustartbefehl für den gesamten Rechner. Das Zurücksetzen der Trainingsstatistik verändert ausschließlich die HA-Zähler und ist auch bei ausgeschaltetem Board verfügbar.

Zusatzbuttons lassen sich auf der Geräteseite unter den deaktivierten Entitäten einzeln aktivieren. Jeder Button kann mit der HA-Aktion `button.press` in Automationen und Dashboards verwendet werden.

## Schalter und Einstellungen

| Entität | Bedeutung |
|---|---|
| Erkennung | Ein/aus, mit dem tatsächlich vom Board gemeldeten Zustand |
| Autodarts-Cloud-Verbindung | Upstream-Verbindung des Boards; unabhängig vom HA-Cloud-Login |
| Beim Start kalibrieren | Automatische Kalibrierung beim Start |
| Automatische Nachkalibrierung | Board-Manager-Option `auto_calibrate` |
| Automatische Verzerrungskorrektur | Board-Manager-Option `auto_distortion` |
| Kamera-Standby (Minuten) | 5, 10, 15, 30 oder 60 Minuten |

Einstellungen werden als einzelne Änderungen übertragen. Kameraauswahl, manuelle Kalibrierungsdaten und Zugangsdaten werden dabei nicht überschrieben. Schalter zeigen den vom Board zurückgemeldeten Zustand; ein angenommener HTTP-Befehl wird nicht automatisch als erfolgreich umgeschalteter Zustand dargestellt.

## Sensoren und Kameras

- **Board-Manager-Verbindung:** lokale Erreichbarkeit. Bleibt als „getrennt“ sichtbar, wenn die übrigen lokalen Entitäten nicht verfügbar sind.
- **Lokaler Erkennungsstatus** und **Board-Ereignis:** vom Board gemeldeter Status bzw. letztes Ereignis.
- **Letzter Wurf**, **Würfe in der Aufnahme**, **Punkte letzter Wurf**, **Erkannte Aufnahmepunkte:** lokal erkannte Darts. Die Punktesumme berücksichtigt keine Spielregeln wie Überwerfen und ersetzt keinen Cloud-Matchscore.
- **Erkennungsbildrate** und **Kamera-Bildraten:** optionale Diagnosewerte, standardmäßig deaktiviert. Bei gestoppter Erkennung sind 0 FPS normal.
- **Kamera 1, 2, …:** optionale Schnappschüsse, standardmäßig deaktiviert. Das Anzeigen startet weder Erkennung noch Kamera-Streams. Sind die Kameras nicht aktiv, kann kein Bild verfügbar sein.

Status und Bildraten werden alle zwei Sekunden abgefragt, Einstellungen und Firmwareversion alle 30 Sekunden. Zusätzlich aktualisiert der lokale WebSocket-Kanal Status und Erkennungszustände unmittelbar. Die Abfragen bleiben zur Wiederherstellung und als Rückfall bei fehlender WebSocket-Unterstützung aktiv. Nach einer Aktion wird eine Aktualisierung angefordert. Kamerabilder werden nur auf Anfrage geladen. Später erkannte Kameras werden automatisch ergänzt.

Lokale und Cloud-Daten werden getrennt aktualisiert. Abgelaufene Cloud-Anmeldedaten oder ein Cloud-Ausfall blockieren die lokalen Bedienelemente nicht. Fällt das lokale Netzwerk aus, stehen lokale Steuerbefehle erst nach Wiederherstellung wieder zur Verfügung.

## Echtzeit-Ereignisse und Zustände

Die zusätzliche **Event-Entität „Board-Ereignisse“** liefert Zeitstempel und Ereignistyp. Der bisherige Sensor „Board-Ereignis“ bleibt erhalten.

| Ereignistyp | Bedeutung | Zusätzliche Attribute |
|---|---|---|
| `dart_detected` | Neuer lokal erkannter Dart | `dart_index` (ab 1), `segment`, `score` |
| `dart_corrected` | Segment eines vorhandenen Darts geändert | `dart_index`, `segment`, `score` |
| `takeout_started` | Herausnehmen begonnen | — |
| `takeout_finished` | Beobachtetes Herausnehmen abgeschlossen | — |
| `status_changed` | Board-Status geändert | `status` |

Das Attribut `source` nennt `websocket` oder `poll`. Die Ereignisse lassen sich mit den normalen HA-Ereignisauslösern verwenden. Identische Nachrichten lösen denselben Wurf nicht erneut aus. Die WebSocket-Verbindung wird bei Abbruch mit wachsendem Abstand erneut aufgebaut. Der Diagnose-Sensor **Echtzeit-Verbindung** zeigt ihren Zustand an.

Weitere Binärsensoren: **Hand erkannt**, **Bild stabil**, **Darts teilweise entfernt**, **Darts vollständig entfernt**, **Kameras aktiv** und **Kalibrierung läuft**. Die ersten vier geben die Erkennungsmeldungen wieder. Bei gestoppter Erkennung oder während der Kalibrierung werden keine alten Bewegungszustände als aktiv angezeigt. „Darts vollständig entfernt“ ist eine Detektionsmeldung, keine unabhängige dauerhafte Belegungsmessung des Boards.

Es handelt sich nicht um ein lückenloses Spielprotokoll: Bei Netzwerkunterbrechungen können Ereignisse fehlen. Im reinen Abfragemodus können außerdem sehr kurze Zustandswechsel zwischen zwei Abfragen liegen. Der beim Start oder nach einer Unterbrechung vorgefundene Zustand wird nicht als neue Wurfserie wiederholt.

## Kamera-Fehlererkennung

**Kamerastörung** und **Kamera 1/2/3 … Störung** melden einen anhaltenden Bildausfall: Eine Kamera liefert mindestens **15 Sekunden lang 0 FPS**, obwohl sowohl Erkennung als auch Kameras als aktiv gemeldet werden. Ein positiver FPS-Wert hebt den Fehler wieder auf.

Start, Kalibrierung, Stopp und Kamera-Standby lösen diesen Alarm nicht aus. Fehlende Messwerte gelten als unbekannt, nicht als 0 FPS. Die Integration startet bei einer Störung keine automatische Reparatur und führt keine Board-Befehle aus.

## Lokale Trainingsstatistik

Die Sitzung zählt lokal beobachtete **Würfe**, **Triple**, **Bull-Treffer**, **180er** und **Punkte**. Ein weiterer Sensor zeigt den Sitzungsbeginn. Bull-Treffer umfassen Single Bull (25) und Double Bull (50). Eine 180 erfordert drei innerhalb derselben Aufnahme beobachtete T20.

- Die Werte werden in Home Assistant gespeichert und bleiben nach regulärem Neustart oder Neuladen der Integration erhalten. Beim Löschen des Integrationseintrags werden sie entfernt.
- **Trainingsstatistik zurücksetzen** setzt die Zähler auf 0 und den Sitzungsbeginn neu. Bereits steckende Darts werden danach nicht erneut gezählt.
- Segmentkorrekturen der aktuellen Aufnahme ändern Punkte, Triple, Bull und gegebenenfalls die 180er-Zahl, ohne einen zusätzlichen Wurf zu zählen. Zähler können durch solche Korrekturen sinken.
- Beim Herausnehmen werden bereits beobachtete Würfe beibehalten. Die Erkennung setzt für die nächste Aufnahme wieder an.
- Bei Neustart oder Verbindungsunterbrechung bleiben bisherige Summen erhalten. Vorhandene Darts werden als Ausgangszustand übernommen; nicht beobachtete Würfe werden nicht nachträglich rekonstruiert. Dadurch können insbesondere teilweise beobachtete 180er fehlen.

Die Sitzung umfasst alle während der Erkennung beobachteten Würfe, unabhängig von Cloud-Spielmodus oder Spieler. Sie berücksichtigt weder Überwerfen noch Checkouts und ist keine spielerbezogene Autodarts-Statistik.

## Dashboard-Beispiel

Die tatsächlichen Entitäts-IDs aus deiner Geräteseite einsetzen. Namen können je nach Sprache oder früheren Installationen abweichen.

```yaml
type: entities
title: Autodarts
entities:
  - entity: switch.autodarts_board_detection
  - entity: button.autodarts_board_start_automatic_calibration
  - entity: button.autodarts_board_reset_detection
  - entity: sensor.autodarts_board_last_throw
  - entity: sensor.autodarts_board_detected_visit_score
```

## Protokoll und Prüfstand

Die Integration verwendet die lokalen Endpunkte des **Board Managers 1.0.7**:

| Funktion | Methode und Pfad |
|---|---|
| Status | `GET /api/state` |
| Unterstützte Einstellungen und Board-ID | `GET /api/config` |
| Firmwareversion (Klartext) | `GET /api/version` |
| Bildraten | `GET /api/state/stats`, `GET /api/cams/stats` |
| Erkennungszustände | `GET /api/state/motion` |
| Kamerazustand | `GET /api/cams/state` |
| Push-Ereignisse | WebSocket `/api/events` |
| Erkennung starten/stoppen | `PUT /api/start`, `PUT /api/stop` |
| Erkennung zurücksetzen | `POST /api/reset` |
| Board Manager neu starten | `POST /api/restart` |
| Automatisch kalibrieren | `POST /api/config/calibration/auto` |
| Einzelne Kamera kalibrieren | `POST /api/config/calibration/auto/{index}?distortion=true` |
| Upstream verbinden/trennen | `PUT /api/upstream/connect`, `PUT /api/upstream/disconnect` |
| Kamera-Streams starten/stoppen | `PUT /api/streams/start`, `PUT /api/streams/stop` |
| Einzelne Einstellung ändern | `PATCH /api/config` |
| Kamera-Schnappschuss | `GET /api/img/cams/{index}` (Index beginnt bei 0) |

Für ältere Versionen wird bei Start/Stopp nur nach HTTP 404/405 einmal auf `/api/detection/start` bzw. `/api/detection/stop` ausgewichen. Nach Zeitüberschreitungen oder anderen Fehlern wird ein Steuerbefehl nicht automatisch wiederholt, da er bereits ausgeführt worden sein könnte. Andere Firmwareversionen sind nicht live geprüft.

**Mit Board Manager 1.0.7 geprüft:** Status, Version, gefilterte Einstellungen, Bildraten, Bewegungs-/Kamerazustände sowie WebSocket-Verbindungsaufbau und -abbau. **Automatisiert mit simulierten Antworten geprüft:** HA-Einrichtung, Buttons einschließlich Einzelkalibrierung, Schalter, Einstellungsänderungen, Kamerazugriff, Echtzeit-Ereignisse, Trainingskorrekturen/-speicherung, Kameraausfälle, Wiederverbindung und Weiterbetrieb bei Cloud-Ausfällen. Die Hardwarevalidierung von Wurfserien und Steueraktionen sowie die Live-Validierung der Cloud-Anmeldung stehen noch aus.

Die Konfigurationsantwort enthält einen Board-API-Schlüssel. Der Client behält daraus nur Board-ID, Kameraanzahl und die oben aufgeführten Einstellungen. API-Schlüssel und Kamera-Gerätepfade werden weder als Attribute veröffentlicht noch in den Diagnosedownload übernommen. Cloud-Tokens sind ebenfalls nicht im Diagnosedownload enthalten.
