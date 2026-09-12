# Forschungsprojekt: belastbare Verbesserungen von Stellaratorspulen

Leseeinstieg für die wissenschaftliche Betreuung. Stand: 12. September 2026.
In etwa zehn Minuten: diese Seite, [Ergebnisstand](STATUS.md), dann
[Arbeitsplan](PROJECT_PLAN.md). Messreihen und Protokolle liegen eine Ebene tiefer.

## Forschungsfrage und Beitrag

Können wir Stellaratorspulen mit einem besseren Kompromiss aus Magnetfeldqualität,
Baubarkeit und Robustheit konstruieren, und diesen Vorteil unabhängig am Computer
nachweisen? Langfristig wollen wir eigene magnetische Plasmaoberflächen und
QI-Plasmakonfigurationen samt passenden Spulen entwickeln, mit Proxima Fusion
und SQuID-C als wissenschaftlicher Orientierung. Ein besserer Optimierungswert
allein beantwortet die Frage nicht: Ein Entwurf muss zuerst alle festgelegten
physikalischen und geometrischen Anforderungen erfüllen.

Der bisherige Beitrag ist eine geprüfte Versuchs- und Validierungsinfrastruktur
mit einigen methodischen Teilergebnissen. Es gibt **noch keinen nachgewiesenen
SoTA-Entwurf, keine zulässige neue Optimierungsbaseline und keine vollständige
SQuID-C-Bereitschaft**. Auch ein qualifizierter Magnetfeldentwurf wäre noch kein
Nachweis besserer Kraftwerksleistung oder wirtschaftlicher Energiegewinnung.

## Langfristiger Plan und aktueller Schwerpunkt

| Schritt | Angestrebtes Ergebnis | Stand |
| --- | --- | --- |
| 1. Rechen- und Prüfwerkzeuge absichern | Gleichgewichte, Magnetfelder, QI-Eigenschaften und Spulengeometrie an bekannten Referenzfällen zuverlässig berechnen und unabhängig prüfen | **In Arbeit:** Teilprüfungen bestehen, weitere physikalische und technische Prüfungen sind offen |
| 2. Spulen für eine vorgegebene Plasmaoberfläche entwickeln | Eine zulässige klassische Spulenlösung als Vergleichsbasis; darauf aufbauend faire Vergleiche von Optimierungsverfahren | **Aktueller Optimierungsschwerpunkt:** Landreman-Paul QA; noch keine neue zulässige Lösung |
| 3. Eigene QI-Plasmakonfigurationen entwickeln | Die magnetische Plasmaoberfläche selbst variieren und das zugehörige Gleichgewicht auf günstige Einschlussbedingungen optimieren | Geplant; derzeit verwenden wir vorhandene Referenzkonfigurationen |
| 4. Plasma und Spulen gemeinsam weiterentwickeln | Plasmakonfiguration und Spulen aufeinander abstimmen, einschließlich endlichem Plasmadruck, Fertigungsabweichungen und technischen Anforderungen | Langfristig geplant; erste Prüfwerkzeuge dafür entstehen bereits |
| 5. Verbesserungen belastbar nachweisen | Eigene Entwürfe unabhängig prüfen und ihren Vorteil gegenüber reproduzierten Referenzentwürfen unter gleichen Anforderungen belegen | Offen; eine bessere Optimierungszahl allein genügt nicht |

**Wir arbeiten derzeit an Schritt 1 und 2.** Die vorgegebene Plasmaoberfläche ist
eine kontrollierte Entwicklungsaufgabe für unsere Methoden. In Schritt 3 wird
ihre Form selbst zum Entwurfsparameter; gute Einschlussphysik muss am zugehörigen
Gleichgewicht geprüft werden und folgt nicht allein aus der Oberflächenform.

Die Schritte geben die Entwicklungsrichtung an und können sich überlappen.
Insbesondere sollen Erkenntnisse über baubare Spulen auf die Entwicklung der
Plasmakonfiguration zurückwirken. Unabhängige Prüfung begleitet alle Schritte.
Der [Arbeitsplan](PROJECT_PLAN.md) konkretisiert die nächsten Aufgaben und
Erfolgskriterien.

## Aktuelle Arbeit an den drei Referenzfällen

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

Die [neueste lokale Diagnose](optimization/DIRECT_DESCENT_COMPOSITE_RESULTS.md)
zeigt an vier festgelegten Testschritten: Größere Schritte verschlechtern den
Magnetfeldfehler stark, obwohl das lineare Modell eine Verbesserung vorhersagt.
Nur der kleinste Schritt am ausgewählten Kandidaten verbessert ihn leicht.
Die [unabhängige Abstand-Ableitungsprüfung](optimization/COMPLEX_CLEARANCE_RESULTS.md)
stützt die verwendeten Ableitungen an den untersuchten Zuständen; der ursprüngliche
fehlgeschlagene Differenzentest bleibt unverändert dokumentiert. Diese Diagnose
ist kein neuer zulässiger Entwurf.

Der anschließende [quadratische Modelltest](optimization/QUADRATIC_FIELD_MODEL_RESULTS.md)
sagt an allen vier Testschritten das richtige Änderungs-Vorzeichen voraus und
verringert den Vorhersagefehler gegenüber dem linearen Modell um mindestens
99,907%. Vollständige native Ableitungsmatrizen und ein separater Kern-Audit
bestätigen die Rechnung. Als Nächstes folgt ein getrennt vorab festgelegter
Optimierungsversuch mit dieser Krümmungsinformation und unabhängiger Abnahme.

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
Nach jedem abgeschlossenen Arbeitsschritt werden die betroffene Dokumentation
und der Prüfvermerk ergänzt; beide READMEs, Ergebnisstand, Arbeitsplan und
Bereichsübersicht werden auf nötige Aktualisierungen geprüft. Das gilt auch für
negative Ergebnisse und Blocker, nicht erst am Sitzungsende.
