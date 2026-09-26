# Sicherheit

[← Übersicht](README.md) · [English](../security.md)

Diese Seite erklärt, wie die Integration deine Daten und dein Board schützt, wem sie vertraut und welche Risiken bleiben. Sicherheitslücken meldest du bitte vertraulich, wie in [SECURITY.md](../../SECURITY.md) beschrieben.

## Was geschützt wird

| Schutzgut | Wo es liegt | Schutz |
| --- | --- | --- |
| API-Schlüssel des Boards, TLS-Schlüssel, Kamerapfade | Konfiguration des Board Managers | Werden direkt beim Lesen verworfen; nie gespeichert, protokolliert, angezeigt oder in Diagnosedaten übernommen |
| Autodarts-OAuth-Token (optionale Cloud-Verknüpfung) | Integrationseintrag in Home Assistant | Nur dort gespeichert, automatisch erneuert, nie protokolliert; das Passwort sieht die Integration nie |
| Board-ID, Board-Adresse, Client-ID | Integrationseintrag in Home Assistant | In Diagnosedaten geschwärzt |
| Trainingssession | `.storage` von Home Assistant | Nur lokal; wird mit der Integration gelöscht |
| Steuerung des Boards | Board-Manager-API | Aktionen nur auf Wunsch eines Nutzers oder einer Automation, genau einmal gesendet |

## Vertrauensgrenzen

```text
 Board-PC                      Home Assistant                    Internet
┌────────────────────┐        ┌──────────────────────────┐       ┌──────────────────────┐
│ Board Manager      │  LAN   │ Autodarts-Integration    │ HTTPS │ Autodarts-Cloud      │
│ Port 3180, ohne    ├───────►│ prüft jede Antwort       ├──────►│ (optional, OAuth)    │
│ Anmeldung          │        │ Dashboard-Karten         │       │ Suchdienst           │
└────────────────────┘        └──────────────────────────┘       │ (nur bei Suche)      │
                                                                 └──────────────────────┘
```

1. **Board Manager → Integration.** Die lokale API hat keine Anmeldung. Die Integration behandelt jede Antwort als nicht vertrauenswürdig: Typen, Wertebereiche und Strukturen werden geprüft, bevor ein Wert eine Entität erreicht. Unerwartete Daten erscheinen als *unbekannt*, statt Fehler auszulösen.
2. **Integration → Dashboard.** Die Karten zeigen Board-Daten im Browser. Jeder Text vom Board oder aus der Entitätsverwaltung wird maskiert, Zahlen werden geprüft, bevor sie zu SVG-Geometrie werden.
3. **Integration → Internet.** Im lokalen Betrieb verlässt nichts das Heimnetz. *Boards im Netzwerk suchen* fragt einmalig und nur auf Wunsch den öffentlichen Suchdienst von Autodarts. Die optionale Cloud-Verknüpfung nutzt die OAuth-Geräteanmeldung über HTTPS mit der gemeinsamen Verbindung von Home Assistant.

## Bedrohungen und Gegenmaßnahmen

| Bedrohung | Gegenmaßnahme | Nachweis |
| --- | --- | --- |
| Geheimnisse des Boards gelangen nach Home Assistant | Die Konfiguration wird direkt nach dem Lesen auf eine Liste erlaubter Felder reduziert; Antworten auf Schreibzugriffe werden verworfen | Tests prüfen, dass der API-Schlüssel nie in Entitäten, Diagnosedaten oder Logs erscheint, auch im Docker-End-to-End-Test |
| Fehlerhafte oder bösartige Board-Daten bringen Integration oder Karten zum Absturz | Prüfung jeder Nachricht; Property-based Tests mit Hypothesis (Trainings-Engine) und fast-check (Karten) mit Tausenden Zufallseingaben | `tests/test_training_properties.py`, `tests/frontend/properties.test.js` |
| Skripteinschleusung über Board- oder Gerätenamen in den Karten | Jeder eingefügte Text wird maskiert; kein `innerHTML` mit unmaskierten Daten | fast-check-Eigenschaft „maskierter Text enthält nie Markup“; DOM-Test, dass ein Spieler namens `<img onerror>` als Text erscheint |
| Ein falsches Board unter der eingerichteten Adresse zeigt oder steuert fremde Daten | Die Board-ID wird bei jedem Lesen geprüft; bei Abweichung sind die Entitäten nicht verfügbar, und ein Reparaturhinweis erscheint | `tests/test_quality.py` |
| Eine Aktion läuft doppelt, etwa Neustart oder Zurücksetzen | Aktionen werden genau einmal gesendet und nie automatisch wiederholt | `tests/test_local_api.py` |
| Eine kompromittierte Abhängigkeit oder ein manipulierter Build | Abhängigkeiten per Hash, gepinnte Actions und Images, Dependabot, Dependency Review, CodeQL, Gitleaks, OpenSSF Scorecard | [Development](../development.md#continuous-integration) |
| Ein manipuliertes Release | Release-Pakete tragen eine mit Sigstore signierte SLSA-Provenance | [Releases](../releases.md#signed-release-packages) |

## Grundsätze

- **Minimale Rechte:** GitHub-Workflows laufen mit Lese-Token, außer ein Job braucht mehr. Die Integration liest den Board Manager und schreibt nur, wenn du oder eine Automation es verlangt.
- **Sicher im Fehlerfall:** Unbekannte Daten werden zu *unbekannt*, ein unerreichbares Board macht Entitäten nicht verfügbar, und ein falsches Board zeigt nie seine Daten.
- **Lokal zuerst:** Die Cloud ist optional; die lokale Steuerung hängt nie von ihr ab.
- **Kleine Angriffsfläche:** Keine Python-Abhängigkeiten zur Laufzeit, keine offenen Ports, keine Dienste außer den Entitäten.

## Verbleibende Risiken

- Die lokale API des Board Managers hat keine Anmeldung. Jeder, der Port 3180 in deinem Netzwerk erreicht, kann das Board steuern, mit oder ohne diese Integration. Betreibe den Board-PC in einem vertrauenswürdigen Netzwerk.
- Autodarts unterstützt die lokale API ab Board Manager 2 offiziell nicht mehr. Eine künftige Version kann sie ändern; die Integration erkennt die Generation und wird gegen beide getestet.
