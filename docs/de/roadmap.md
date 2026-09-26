# Roadmap

[← Übersicht](README.md) · [English](../roadmap.md)

Diese Roadmap zeigt, was jede Version gebracht hat und was als Nächstes kommt. Sie ist eine Richtung, kein Versprechen: Die Prioritäten richten sich nach den Rückmeldungen der Spieler, die Termine nach der verfügbaren Freizeit. Ideen und Stimmen sind als [Funktionswunsch](https://github.com/Dennis-Otto/ha-autodarts/issues/new/choose) willkommen.

## Version 1.0: das lokale Fundament

Enthalten, alles ohne Autodarts-Cloud:

- Lokale Echtzeitverbindung zu Board Manager 1 und 2 mit automatischer Erkennung.
- Steuerung, Board-Einstellungen, Kamerazustand und Board-Manager-Updates.
- Trainingsanalyse mit Treffern pro Feld, Aufnahmeverlauf und dem Ereignis `visit_completed`.
- Drei Dashboard-Karten, ein automatisches Dashboard und sechs Blueprints.
- Dokumentation auf Englisch und Deutsch.

## Version 1.1: Trainingssessions

- Trainingssessions, die mit dem ersten Dart oder bewusst beginnen, nach einer Pause enden und eine Übersicht der letzten 20 Sessions behalten.
- Die Ereignisse `session_started` und `session_ended` und ein siebter Blueprint, der Licht, Erkennung und Kalibrierung an die Session koppelt.
- Die letzten Aufnahmen in der Live-Karte, Sessionstatus und vergangene Sessions in der Trainingskarte.
- Details zum Board-PC aus Board Manager 2: Betriebssystem, Prozessor und Erkennungssoftware.

## Als Nächstes: 1.2

| Thema | Was es bringt |
| --- | --- |
| **Lokale Übungsspiele** | Ein X01-Übungsmodus, der die Restpunkte führt, Überwerfen erkennt und Checkouts vorschlägt, alles vom lokalen Board |
| **Live-Kamerabild** | Livestreams der Board-Kameras statt Standbildern, wo Board Manager 2 sie anbietet |

## Später

| Thema | Voraussetzung |
| --- | --- |
| **Cloud-Spielereignisse:** Leg und Match gewonnen, Überwerfen, Spielerwechsel, Restpunkte | Eine OAuth-Client-ID von Autodarts; sie ist beantragt |
| **HACS-Standardkatalog** | Im September 2026 beantragt ([hacs/default#11306](https://github.com/hacs/default/pull/11306)); die Prüfung bei HACS dauert mehrere Monate |
| **Weitere Sprachen** | Beiträge von Muttersprachlern |
| **Protokoll-Bibliothek auf PyPI** | Eine eigene Bibliothek für das Board-Manager-Protokoll; Voraussetzung für einen möglichen Weg in den Home-Assistant-Kern |

## So werden Prioritäten gesetzt

1. Alles, was bei Nutzern kaputtgeht, auch durch neue Board-Manager-Versionen, kommt zuerst.
2. Lokale Funktionen kommen vor Cloud-Funktionen.
3. Danach Wünsche mit den meisten Reaktionen auf GitHub.
