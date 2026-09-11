# Forschungsprojekt: belastbare Verbesserungen von Stellaratorspulen

Leseeinstieg für die wissenschaftliche Betreuung. Stand: 11. September 2026.
In etwa zehn Minuten: diese Seite, [Ergebnisstand](STATUS.md), dann
[Arbeitsplan](PROJECT_PLAN.md). Messreihen und Protokolle liegen eine Ebene tiefer.

## Forschungsfrage und Beitrag

Können wir Stellaratorspulen mit einem besseren Kompromiss aus Magnetfeldqualität,
Baubarkeit und Robustheit konstruieren, und diesen Vorteil unabhängig am Computer
nachweisen? Langfristig interessieren uns QI-Konfigurationen in Richtung Proxima
Fusion und SQuID-C. Ein besserer Optimierungswert allein beantwortet die Frage
nicht: Ein Entwurf muss zuerst alle festgelegten physikalischen und geometrischen
Anforderungen erfüllen.

Der bisherige Beitrag ist eine geprüfte Versuchs- und Validierungsinfrastruktur
mit einigen methodischen Teilergebnissen. Es gibt **noch keinen nachgewiesenen
SoTA-Entwurf, keine zulässige neue Optimierungsbaseline und keine vollständige
SQuID-C-Bereitschaft**. Auch ein qualifizierter Magnetfeldentwurf wäre noch kein
Nachweis besserer Kraftwerksleistung oder wirtschaftlicher Energiegewinnung.

## Drei Referenzfälle mit unterschiedlichen Aufgaben

Die drei Referenzfälle prüfen unterschiedliche Teile der Forschung. Sie sind
teilweise unabhängig bearbeitbar; eine feste Reihenfolge „erst W7-X, dann
Landreman-Paul, dann Goodman“ ist nicht erforderlich. Der derzeitige Startpunkt
der eigentlichen Spulenoptimierung ist der Landreman-Paul-QA-Fall.

| Referenzfall | Wissenschaftlicher Zweck | Was er nicht ersetzt |
| --- | --- | --- |
| W7-X | Prüfen, ob unsere Gleichgewichtsberechnung für einen festgelegten W7-X-Modellfall die Ergebnisse einer etablierten Referenzrechnung reproduziert | Validierung des vollständigen gebauten Geräts |
| Landreman-Paul QA / StellCoilBench | Verfahren vergleichen, die für eine vorgegebene magnetische Plasmaoberfläche passende Spulen unter festen Geometriegrenzen konstruieren | Nachweis der Übertragbarkeit auf QI-Entwürfe oder SQuID-C |
| Offene Goodman-QI-Fälle | An vorhandenen Magnetfeldkonfigurationen prüfen, ob wir Bouncewirkung und weitere QI-relevante Eigenschaften zuverlässig berechnen | Globale QI-/maximum-J-Zertifizierung |

**Parallel bearbeitbar:** Die Spulenoptimierung und die QI-Auswertung lassen sich
an ihren jeweiligen offenen Daten entwickeln. Für die Goodman-Auswertung sind
noch keine selbst optimierten Spulen nötig. Der W7-X-Vergleich prüft die
Gleichgewichtsberechnung, qualifiziert aber nicht automatisch die übrigen
Werkzeuge. Er vergleicht numerische Rechnungen, keine experimentellen Messdaten.

**Beim späteren QI-Spulenentwurf müssen die Ergebnisse zusammenkommen:** Die
Optimierung erzeugt einen Kandidaten; Feld- und Gleichgewichtsberechnungen
bestimmen seine magnetischen Eigenschaften; die QI-Auswertung untersucht die
relevante Einschlussphysik. Zusammen mit unabhängigen Geometrie- und
Ingenieurprüfungen entscheidet dies über seine Eignung und kann weitere
Optimierungsschritte anleiten. Belastbare Erfolgsaussagen setzen geprüfte
Werkzeuge und einen unabhängig geprüften Entwurf voraus. Ein methodischer Erfolg
am QA-Fall allein belegt noch keinen Vorteil für QI-Entwürfe.

SQuID-C ist eine spätere Zielbaseline. Wir benötigen dafür ein eindeutig
zugeordnetes, maschinenlesbares Autorenpaket und eine qualifizierte Reproduktion.
Die letzten dokumentierten Verfügbarkeitssuchen sind vom August; sie sind kein
aktueller oder universeller Beweis, dass keine Daten existieren.

## Was inzwischen belastbar ist

- **Landreman-Paul QA / StellCoilBench:** Eine analytisch geprüfte räumliche
  Darstellung des Magnetfeldfehlers erhält Zielfunktion und Gradienten.
  Ihre beschleunigte Ableitung ermöglicht einen
  wiederholten Vergleich bei gleichem Zeitbudget. An einem festen Startpunkt ist
  der Magnetfeldfehler rund 2,35-fach kleiner; trotzdem sind alle Entwürfe unzulässig.
- **Landreman-Paul QA / StellCoilBench:** Unabhängige Geometrieprüfungen finden
  Krümmungsverletzungen zwischen den Optimierungsstützstellen.
  Kontinuierliche Schranken verhindern hier falsche
  Freigaben, unter ausdrücklich dokumentierten Gleitkomma-Annahmen.
- **Offene Goodman-QI-Fälle:** QI-Teilmessungen sind gegen unabhängige Integration
  und Feldlinienrekonstruktion geprüft. Endlicher Plasmadruck verändert die
  gemessenen Vorzeichen radialer Bouncewirkungsableitungen. Der untersuchte
  Bereich ist begrenzt.
- **W7-X:** Der ausgewählte Gleichgewichtsvergleich besteht. Im erweiterten
  Dateivergleich bleiben drei von 63 Größen abweichend.
- **Landreman-Paul QA / StellCoilBench:** Ein anschließender Pilot mit direkten
  Randbedingungen besteht Geometrie- und zusätzliche native Prüfungen. Sein
  Magnetfeldfehler bleibt jedoch Faktor 23,3 über der festen Grenze;
  eine zulässige Baseline ist weiterhin offen.

Die Zahlen, Gegenprüfungen und Grenzen stehen im [Ergebnisstand](STATUS.md).

## Wie Erfolg beurteilt wird

Methoden sind gleichberechtigt: klassische Optimierung, automatische Ableitungen,
globale Suche, robuste Verfahren und lernende Modelle müssen denselben unabhängigen
Bewertungsweg bestehen. AI ist weder Zielgröße noch Qualitätsnachweis.
Protokolle, Eingaben, Rechenbudgets und Grenzwerte werden vor neuen Versuchen
festgehalten. Fehlschläge bleiben erhalten. Erst nach einer zulässigen klassischen
Baseline sind mehrstartige Methodenvergleiche und robuste Paretoverbesserungen
sinnvoll. Grenzen von Filament-, Gleichgewichts- und Mechanikmodellen bleiben
Teil jeder Aussage.

## Detailbereiche

- [Optimierung](optimization/README.md): Orakel, Ableitungen, Vergleichsversuche und zurückgewiesene Kandidaten.
- [Geometrie](geometry/README.md): Gitterfehler, Krümmung und kontinuierliche Abstandsgrenzen.
- [QI-Physik](qi/README.md): Daten, Bouncewirkung, Feldlinien und endlicher Druck.
- [Ingenieurmodelle](engineering/README.md): Fertigungsfehler, Netze, Mechanik und freie Plasmagrenze.
- [Validierung](validation/README.md): Evidenzregeln, Umgebung, W7-X und übergreifende Audits.
- [SQuID-C](squid_c/README.md): Aufnahmekriterien, offene Bereitschaftsprüfungen und Datenanforderung.
- [Forschungsjournal](logbook/README.md): chronologische Befunde, Entscheidungen und Prüfprotokoll.

Dokumentationsregel: In `docs/` stehen nur diese Übersicht, Ergebnisstand und
Arbeitsplan. Jeder Detailordner hat einen eigenen Zweck und eine gepflegte
`README.md`; weitere Verschachtelung ist ausgeschlossen. Verbindliche Regeln für
künftige Sitzungen stehen in [AGENTS.md](../AGENTS.md).
