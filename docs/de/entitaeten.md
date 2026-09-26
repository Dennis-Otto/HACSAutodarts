# Entitäten und Ereignisse

[← Übersicht](README.md) · [English](../entities.md)

Jedes Board ist ein Gerät mit den folgenden Entitäten. Ihre Namen folgen der Sprache von Home Assistant. Die Entitäts-IDs leiten sich vom Board-Namen ab, zum Beispiel `sensor.autodarts_board_training_3_dart_average`.

**Legende:**

| Spalte oder Markierung | Bedeutung |
| --- | --- |
| **BM** | Die Board-Manager-Generation, die die Entität liefert: 1, 2 oder beide |
| *Deaktiviert* | Wird deaktiviert angelegt; bei Bedarf aktivierst du sie in den Entitätseinstellungen |
| *Diagnose*, *Konfiguration* | Die Entitätskategorie; solche Entitäten stehen auf der Geräteseite in eigenen Bereichen |

<img src="../images/de/device.png" alt="Geräteseite eines Autodarts-Boards in Home Assistant" width="760">

## Aktuelle Aufnahme

| Entität | Typ | Beschreibung |
| --- | --- | --- |
| Erkennungsstatus | Sensor (Aufzählung) | `offline`, `starting`, `stopping`, `stopped`, `throw` (bereit), `takeout`, `takeout_in_progress`, `calibrating`, `error`. Unbekannte Zustände künftiger Board-Manager-Versionen erscheinen als *unbekannt*. |
| Letzter Dart | Sensor | Feld des letzten Darts, zum Beispiel `T20`, `D16`, `S5`, `25`, `Bull`. |
| Punkte letzter Dart | Sensor, Punkte | Punkte des letzten Darts. |
| Darts in der Aufnahme | Sensor, Darts | Darts, die gerade im Board erkannt sind (0–3). |
| Erkannte Aufnahmepunkte | Sensor, Punkte | Summe der erkannten Darts. Das Attribut `throws` listet jeden Dart mit `segment`, `number`, `multiplier`, `score`, `bed` und der normierten Position `x`/`y`. Das Attribut `recent_visits` listet die letzten zehn abgeschlossenen Aufnahmen, die neueste zuerst, mit `time`, `score`, `darts` und `segments`. Der Recorder speichert beide Attribute nicht. |
| Letztes Board-Ereignis | Sensor | Der letzte Ereignistext des Board Managers, etwa `Throw detected` oder `Takeout started`. |

Die Aufnahmepunkte sind die reine Summe der Darts, ohne Spielregeln wie Überwerfen.

## Board-Ereignisse

Die Entität **Board-Ereignisse** (`event.*_board_events`) löst native Home-Assistant-Ereignisse aus. Das Attribut `event_type` sagt, was passiert ist; weitere Attribute enthalten die Details. Jedes Ereignis hat zusätzlich `source`: `websocket` für Echtzeit, `poll` beim Abgleich per HTTP und `training` für Session-Ereignisse.

| `event_type` | Wann | Attribute |
| --- | --- | --- |
| `dart_detected` | Ein neuer Dart landet | `dart_index` (1–3), `segment`, `score` |
| `dart_corrected` | Das Board korrigiert einen erkannten Dart | `dart_index`, `segment`, `score` |
| `takeout_started` | Du beginnst, die Darts zu ziehen | keine |
| `takeout_finished` | Das Board ist wieder frei | keine |
| `visit_completed` | Eine Aufnahme endet: bei der Entnahme, wenn nach einer verpassten Entnahme neue Darts folgen, oder wenn die Erkennung stoppt | `score`, `darts`, `segments` (etwa `["T20", "T20", "S20"]`) |
| `status_changed` | Der Erkennungsstatus ändert sich | `status` |
| `session_started` | Eine Trainingssession beginnt: mit dem Schalter *Trainingssession*, der Taste *Neue Trainingssession* oder mit dem ersten Dart, wenn *Sessions automatisch starten* an ist | `started` und `reason` (`manual`, `new_session` oder `first_dart`) |
| `session_ended` | Eine Trainingssession endet: mit dem Schalter, der Taste oder nach der Pause aus *Session beenden nach einer Pause von* | `reason` (`manual`, `new_session` oder `idle`), `started`, `ended`, `duration_minutes`, `darts`, `points`, `average`, `visits`, `highest_visit` und die übrigen Trainingssummen |
| `bust` | Ein Dart im [Übungsspiel](#übungsspiel) geht unter null, lässt mit Double-Out 1 übrig oder erreicht 0 ohne Double | `game`, `player`, `name`, `remaining` (der Rest zu Beginn der Aufnahme, der bleibt) |
| `leg_won` | Ein Dart beendet das Übungsleg | `game`, `player`, `name`, `darts` und `average` des Legs, `checkout` (der ausgecheckte Rest), `legs` und `sets` des Gewinners danach |
| `match_won` | Ein Dart entscheidet ein Übungsmatch mehrerer Spieler | `game`, `player`, `name`, `sets`, `average` des Matches |
| `turn_changed` | Im Übungsmatch wurden die Darts gezogen und der nächste Spieler ist dran | `game`, `player`, `name`, `remaining` |

Nach einem Neustart oder Verbindungsabbruch werden Ereignisse nie wiederholt. Beispiele stehen unter [Automationen](automationen.md).

## Trainingssession

Die Integration zählt deine Darts in Trainingssessions, in Home Assistant und unabhängig von Autodarts-Spielen. Sessions überstehen Neustarts.

- **Starten und beenden:** Der Schalter *Trainingssession* startet eine Session bei null und beendet sie. *Neue Trainingssession* beendet die laufende Session und startet die nächste.
- **Automatisch:** Ist *Sessions automatisch starten* an, startet der erste Dart eine Session, wenn keine läuft. *Session beenden nach einer Pause von* beendet eine Session so viele Minuten nach ihrem letzten Dart; `0` lässt sie weiterlaufen.
- **Ohne Session** werden Darts und Aufnahmen weiter als [Board-Ereignisse](#board-ereignisse) gemeldet, etwa für eine 180-Feier im Online-Spiel, aber nicht gezählt.
- **Historie:** Eine beendete Session behält ihre Summen, bis die nächste beginnt. *Schnitt der letzten Session* hält den 3-Dart-Average jeder beendeten Session mit Darts fest; sein Verlauf zeigt deine Entwicklung.

Mit den Standardwerten, automatischer Start an und keine Pausengrenze, zählt jeder Dart wie in Version 1.0.

| Entität | Typ | Beschreibung |
| --- | --- | --- |
| Training: Darts | Sensor, Summe | Darts der Session. Das Attribut `hits` zählt die Treffer pro Feld, etwa `{"T20": 12, "S20": 30, "BULL": 2, "MISS": 3}`; das Trefferbild nutzt es. Der Recorder speichert `hits` nicht. |
| Training: Punkte | Sensor, Summe | Summe aller Punkte. |
| Training: 3-Dart-Average | Sensor | Punkte pro drei Darts, der übliche Darts-Schnitt. Vor dem ersten Dart *unbekannt*. |
| Training: Aufnahmen | Sensor, Summe | Aufnahmen mit mindestens einem gezählten Dart. |
| Training: Höchste Aufnahme | Sensor | Höchste Aufnahme der Session. |
| Training: 100+ Aufnahmen | Sensor, Summe | Aufnahmen mit 100–139 Punkten. |
| Training: 140+ Aufnahmen | Sensor, Summe | Aufnahmen mit 140–179 Punkten. |
| Training: 180er | Sensor, Summe | Aufnahmen mit drei Triple 20. |
| Training: Triple | Sensor, Summe | Darts in einem Triple-Feld. |
| Training: Doubles | Sensor, Summe | Darts in einem Double-Feld (ohne Bull). |
| Training: Bull-Treffer | Sensor, Summe | Darts im Bull oder Single Bull. |
| Training: Fehlwürfe | Sensor, Summe | Darts außerhalb der Wertungsfelder. |
| Trainingsbeginn | Sensor, Zeitstempel | Wann die Session begonnen hat. |
| Trainingssession | Schalter | An, solange eine Session läuft. Einschalten startet eine Session bei null, Ausschalten beendet sie. |
| Neue Trainingssession | Taste | Beendet die laufende Session und startet die nächste; das Board selbst bleibt unberührt. |
| Sessions automatisch starten | Schalter, *Konfiguration* | Der erste Dart startet eine Session, wenn keine läuft. Standardmäßig an. |
| Session beenden nach einer Pause von | Zahl, *Konfiguration* | Minuten ohne Darts, 0–240, nach denen eine Session von selbst endet. `0`, der Standard, lässt sie weiterlaufen. |
| Schnitt der letzten Session | Sensor, Punkte | 3-Dart-Average der letzten beendeten Session. Attribute: `started`, `ended`, `duration_minutes`, die Summen und `sessions` mit den letzten 20 Sessions, die der Recorder nicht speichert. |

Die Summen nutzen die Zustandsklasse *total increasing*. Statistiken und Verlaufsdiagramme von Home Assistant behandeln einen Neustart der Session daher korrekt. [So wird gezählt](funktionsweise.md#trainingssession).

## Übungsspiel

Spiele X01 am lokalen Board ohne Autodarts-Spiel. Home Assistant zählt herunter, erkennt Überwerfen und zeigt den Checkout-Weg. Das Spiel braucht keine Cloud und übersteht Neustarts.

- **Starten:** Wähle 301, 501 oder 701 in *Übungsspiel*. Darts, die schon im Board stecken, zählen nicht. *Neues Übungsleg* beginnt das Leg wieder beim vollen Rest.
- **Aufnahmen:** Eine Aufnahme endet, wenn du die Darts ziehst. Nach dem Überwerfen bleibt der Rest vom Beginn der Aufnahme. Darts nach dem Überwerfen oder nach dem Checkout zählen nicht.
- **Checkout:** der Weg für die restlichen Darts der Aufnahme, etwa `T20 T20 BULL` für 170. [So wird der Weg gewählt](funktionsweise.md#übungsspiel).
- **Matches:** Stelle *Übungsspiel Spieler* auf 2, 3 oder 4. Nach einer Aufnahme wirft der nächste Spieler; auch beim Überwerfen ist der Nächste dran. Wer zuerst *Übungsspiel Legs pro Satz* Legs gewinnt, holt den Satz, und wer zuerst *Übungsspiel Sätze zum Sieg* Sätze holt, gewinnt das Match. Das Ergebnis bleibt in der Karte stehen, bis der nächste Dart ein neues Match beginnt. Mit einem Spieler werden Legs und Sätze nicht gezählt.
- **Sessions:** Übungsspiel und [Trainingssessions](#trainingssession) sind unabhängig. Ein Dart zählt in beiden.

| Entität | Typ | Beschreibung |
| --- | --- | --- |
| Übungsspiel | Auswahl | `off` (*Aus*), `301`, `501` oder `701`. Die Wahl eines Spiels startet ein neues Match. |
| Übungsspiel Restpunkte | Sensor | Restpunkte des Spielers am Board; ohne Spiel *unbekannt*. Attribute: `game`, `double_out`, `player` und `name` des Spielers am Board, `checkout`, `bust`, `won`, `visit` (die Felder der aktuellen Aufnahme), `darts` und `average` des Legs, `players`, `legs_to_win`, `sets_to_win`, `winner` (der Matchgewinner bis zum nächsten Dart), `scores` mit `player`, `name`, `remaining`, `legs`, `sets` und dem Match-`average` jedes Spielers sowie `legs` mit den letzten 10 Legs (`game`, `player`, `name`, `darts`, `average`, `checkout`, `ended`). Der Recorder speichert weder `visit`, `scores` noch `legs`. |
| Übungsspiel Checkout-Weg | Sensor | Der Checkout-Weg, etwa `T20 25 D18`; *unbekannt*, wenn es keinen gibt. |
| Neues Übungsleg | Taste | Beginnt das Leg wieder beim vollen Rest; Legs und Sätze bleiben. |
| Neues Übungsmatch | Taste | Beginnt das Match wieder bei null Legs und Sätzen. |
| Übungsspiel Spieler | Zahl | 1–4 Spieler. Eine Änderung startet ein neues Match. |
| Übungsspiel Legs pro Satz | Zahl | 1–11 Legs gewinnen einen Satz. Eine Änderung startet ein neues Match. |
| Übungsspiel Sätze zum Sieg | Zahl | 1–7 Sätze gewinnen das Match. Eine Änderung startet ein neues Match. |
| Übungsspiel Spieler *N* | Text, *Konfiguration* | Name von Spieler 1–4, höchstens 20 Zeichen, für Anzeigetafel und Ereignisse. Ohne Namen zeigt die Karte *Spieler N*. |
| Übungsspiel Double-Out | Schalter, *Konfiguration* | Checkout auf einem Double oder dem Bullseye. Standardmäßig an. |

## Steuerung

| Entität | Typ | Beschreibung |
| --- | --- | --- |
| Erkennung | Schalter | Startet oder stoppt die Dart-Erkennung. |
| Erkennung starten, Erkennung stoppen | Tasten | Dieselben Aktionen als Tasten, für Skripte und Dashboards. |
| Erkennung zurücksetzen | Taste | Verwirft die im Board erkannten Darts. |
| Automatische Kalibrierung starten | Taste, *Konfiguration* | Kalibriert alle Kameras. |
| Kamera *N* kalibrieren | Taste, *Konfiguration* | Kalibriert eine Kamera. |
| Board Manager neu starten | Taste, *Konfiguration* | Startet den Board-Manager-Dienst neu. |
| Kamerastreams starten, Kamerastreams stoppen | Tasten, *Konfiguration*, *Deaktiviert* | Steuert die Kamerastreams des Board Managers. |
| Board-Cloud-Verbindung | Schalter, **BM 1** | Stellt die eigene Verbindung des Boards zu Autodarts her oder trennt sie. |
| Board-Cloud-Verbindung herstellen, Board-Cloud-Verbindung trennen | Tasten, **BM 1**, *Deaktiviert* | Dasselbe als Tasten. |

Jede Aktion wird **genau einmal** gesendet. Lehnt das Board sie ab oder antwortet es nicht, meldet Home Assistant einen Fehler, statt es erneut zu versuchen. So wird keine Aktion doppelt ausgeführt.

## Board-Einstellungen

| Entität | Typ | Beschreibung |
| --- | --- | --- |
| Beim Start kalibrieren | Schalter, *Konfiguration* | Kalibriert beim Start der Erkennung. |
| Automatisch nachkalibrieren | Schalter, *Konfiguration* | Der Board Manager kalibriert bei Bedarf selbst nach. |
| Automatische Verzerrungskorrektur | Schalter, *Konfiguration* | Korrigiert die Linsenverzerrung bei der Kalibrierung. |
| Kamera-Standby (Minuten) | Auswahl, *Konfiguration* | Versetzt die Kameras nach 5, 10, 15, 30 oder 60 Minuten ohne Nutzung in den Standby. |

Änderungen werden in die Board-Manager-Konfiguration geschrieben; gesendet wird nur die geänderte Einstellung.

## Zustand und Verbindungen

| Entität | Typ | Beschreibung |
| --- | --- | --- |
| Board-Manager-Verbindung | Binärsensor, *Diagnose* | Home Assistant erreicht den Board Manager. |
| Echtzeitverbindung | Binärsensor, *Diagnose* | Echtzeitereignisse kommen an. Ohne sie liest die Integration alle 2 Sekunden. |
| Autodarts-Cloud-Verbindung | Binärsensor, **BM 2**, *Diagnose* | Die Verbindung des Boards zu Autodarts. |
| Kameras aktiv | Binärsensor | Die Kameras laufen. |
| Kalibrierung läuft | Binärsensor | Eine Kalibrierung läuft. |
| Kamerastörung | Binärsensor, *Diagnose* | An, wenn eine Kamera bei laufender Erkennung 15 Sekunden lang keine Bilder liefert. Normales Stoppen, Kalibrieren und Standby zählen nicht. |
| Störung Kamera *N* | Binärsensor, *Diagnose* | Dasselbe für eine einzelne Kamera. |
| Erkennungsbildrate | Sensor, fps, *Diagnose*, *Deaktiviert* | Bilder pro Sekunde der Erkennung. |
| Bildrate Kamera *N* | Sensor, fps, *Diagnose*, *Deaktiviert* | Bilder pro Sekunde einer Kamera. |
| CPU-Auslastung | Sensor, %, **BM 2**, *Diagnose* | CPU-Last des Board-PCs. |
| Speichernutzung | Sensor, **BM 2**, *Diagnose*, *Deaktiviert* | Speichernutzung laut Board Manager 2. |
| Betriebssystem des Board-PCs | Sensor, **BM 2**, *Diagnose* | Distribution und Version des Board-PCs, etwa *Debian 13*. Attribute: `kernel`, `architecture`. |
| Prozessor des Board-PCs | Sensor, **BM 2**, *Diagnose* | Prozessormodell des Board-PCs. Attribut: `cores`. |
| Version der Erkennungssoftware | Sensor, **BM 2**, *Diagnose* | Version der Autodarts-Erkennungssoftware. Attribut: `opencv_version`. |
| Board-Software | Update, **BM 2** | Installierte und neueste Board-Manager-Version. Updates installierst du auf dem Board-PC. |

Die Entitäten einer einzelnen Kamera tragen das Attribut `camera` mit der Kameranummer. Die [Board-Status-Karte](karten.md#board-status) nutzt es.

## Bewegung

| Entität | Typ | Beschreibung |
| --- | --- | --- |
| Hand erkannt | Binärsensor | Eine Hand ist vor dem Board. |
| Bild stabil | Binärsensor | Das Kamerabild ist ruhig. |
| Darts teilweise entfernt | Binärsensor | Einige Darts sind entfernt. |
| Darts vollständig entfernt | Binärsensor | Alle Darts sind entfernt. |

Während die Erkennung gestoppt ist, startet, stoppt oder kalibriert, sind diese Sensoren *aus*.

## Kameras

| Entität | Typ | Beschreibung |
| --- | --- | --- |
| Kamera *N* | Kamera, *Deaktiviert* | Eine Board-Kamera, etwa für eine Bildkarte oder den Kameradialog. Mit **BM 2** leitet die Liveansicht den Kamerastream des Boards über Home Assistant weiter; läuft der Stream nicht, und mit BM 1, zeigt sie Standbilder. Um eine Kamera zu zeigen, startet oder stoppt die Integration weder die Erkennung noch die Streams. |

## Cloud-Spieldaten (optional)

Diese Entitäten gibt es nur mit [verknüpftem Autodarts-Konto](installation.md#autodarts-cloud-verknüpfen-optional). Sie werden während eines Matches alle 5 Sekunden gelesen, sonst einmal pro Minute.

| Entität | Typ | Beschreibung |
| --- | --- | --- |
| Board-Status | Sensor (Aufzählung), *Diagnose* | `connected` oder `disconnected` in der Autodarts-Cloud. |
| Spielmodus | Sensor | Variante des laufenden Spiels, etwa `X01` oder `Cricket`. |
| Spielstatus | Sensor (Aufzählung) | `no_match`, `active` oder `finished`. |
| Runde | Sensor | Aktuelle Runde. |
| Punkte der Aufnahme | Sensor, Punkte | Punkte der aktuellen Aufnahme im Spiel. |
| Geworfene Darts | Sensor, Darts | Im Spiel geworfene Darts. |

Ohne lokales Board kommen auch *Letztes Board-Ereignis*, *Letzter Dart* und *Darts in der Aufnahme* aus der Cloud.

## Verfügbarkeit

- Lokale Entitäten werden *nicht verfügbar*, wenn der Board Manager nicht antwortet, und erholen sich selbst.
- Trainingsentitäten bleiben verfügbar, weil die Session in Home Assistant gespeichert ist.
- Antwortet unter der eingerichteten Adresse ein **anderes Board**, bleiben die Entitäten nicht verfügbar, und Home Assistant zeigt einen Reparaturhinweis.
- Beim Umstieg von Board Manager 1 auf 2 lädt sich die Integration selbst neu und ergänzt oder entfernt die generationsspezifischen Entitäten.
