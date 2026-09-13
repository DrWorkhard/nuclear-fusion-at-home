# Forschungsprojekt: belastbare Verbesserungen von Stellaratorspulen

Leseeinstieg für die wissenschaftliche Betreuung. Stand: 13. September 2026.
Diese Übersicht, [Ergebnisstand](STATUS.md) und [Arbeitsplan](PROJECT_PLAN.md)
beschreiben Ziel, belegten Fortschritt und nächste Entscheidungen. Vollständige
Messreihen, Fehlschläge und Prüfprotokolle liegen eine Ebene tiefer.

## Forschungsfrage und bisheriger Beitrag

Können wir Stellaratorspulen mit einem besseren Kompromiss aus Magnetfeldqualität,
Baubarkeit und Robustheit konstruieren und den Vorteil unabhängig am Computer
nachweisen? Langfristig wollen wir eigene QI-Plasmakonfigurationen samt passenden
Spulen entwickeln, mit Proxima Fusion und SQuID-C als wissenschaftlicher Orientierung.

Bisher entstanden reproduzierbare Versuchs- und Prüfwerkzeuge sowie methodische
Teilergebnisse. **Noch kein neuer zulässiger Spulenentwurf, kein SoTA-Nachweis und
keine vollständige SQuID-C-Bereitschaft.** Ein niedrigerer Optimierungswert allein
belegt weder bessere Einschlussphysik noch bessere Kraftwerksleistung.

## Langfristiger Plan und aktueller Schwerpunkt

| Schritt | Angestrebtes Ergebnis | Stand |
| --- | --- | --- |
| 1. Rechen- und Prüfwerkzeuge absichern | Gleichgewichte, Magnetfelder, QI-Eigenschaften und Spulengeometrie an bekannten Referenzen unabhängig prüfen | In Arbeit; wichtige Teilprüfungen bestehen, QI-/Ingenieurqualifikation offen |
| 2. Spulen für eine vorgegebene Plasmaoberfläche entwickeln | Zulässige starke klassische Vergleichslösung, anschließend faire Methodenvergleiche | Aktueller Optimierungsschwerpunkt LPQA; noch keine neue zulässige Lösung |
| 3. Eigene QI-Plasmakonfigurationen entwickeln | Plasmaoberfläche variieren und zugehöriges Gleichgewicht auf günstigen Einschluss optimieren | Geplant; derzeit vorhandene Referenzkonfigurationen |
| 4. Plasma und Spulen gemeinsam weiterentwickeln | Einschluss, endlichen Druck, Baubarkeit und Robustheit gemeinsam berücksichtigen | Langfristig geplant |
| 5. Verbesserungen belastbar nachweisen | Unabhängig geprüfter Vorteil gegenüber reproduzierten Referenzen unter gleichen Anforderungen | Offen |

**Wir arbeiten an Schritt 1 und 2.** Die Schritte dürfen sich überlappen.
Spulenoptimierung an einer festen Oberfläche ersetzt keine QI-Plasmaoptimierung.
Umgekehrt beweist eine günstige Plasmaoberfläche noch keine baubaren Spulen.

## Warum drei Referenzfälle?

| Referenz | Zweck | Begrenzung |
| --- | --- | --- |
| W7-X-Modellfall | Gleichgewichtsberechnung gegen etablierte Referenzrechnung prüfen | Kein Vergleich mit dem vollständigen gebauten Gerät oder experimentellen Messungen |
| Landreman-Paul QA / StellCoilBench | Spulen für eine feste magnetische Oberfläche unter festen Geometriegrenzen optimieren | QA-Methodenerfolg ist kein nachgewiesener QI-/SQuID-C-Vorteil |
| Offene Goodman-QI-Fälle | Bouncewirkung und QI-relevante Einschlussdiagnostik an vorhandenen Konfigurationen prüfen | Noch kein global qualifizierter maximum-J-/Driftmaßstab |

Spulenoptimierung und QI-Auswertung können an ihren jeweiligen offenen Daten
entwickelt werden. Für einen späteren QI-Spulenentwurf müssen Feld-, Gleichgewichts-,
QI- und Ingenieurprüfungen zusammenkommen. SQuID-C ist eine spätere Zielbaseline;
dafür ist ein eindeutig zugeordnetes maschinenlesbares Autorenpaket nötig.
Die dokumentierten Verfügbarkeitssuchen vom August sind keine aktuelle oder
universelle Aussage, dass solche Daten nicht existieren.

## Aktuell entscheidende Befunde

- Die beste fein geprüfte LPQA-Form erreicht etwa **8,13e-8 statt geforderter
  höchstens 1e-8**. Geprüfte Geometrie-/native Bedingungen bestehen; die
  Magnetfeldgrenze nicht. Wiederholte Suchläufe endeten am Budget, nicht bewiesen konvergiert.
- [Exakte Stromoptimierung](optimization/FIXED_GEOMETRY_CURRENT_RESULTS.md)
  bringt bei den zwei festgehaltenen Formen praktisch nichts. Alle acht
  Feld-Holdouts und unabhängigen Gegenprüfungen sind abgeschlossen.
- [Sechs geometrische Kontrollschritte](optimization/GEOMETRIC_DESCENT_RESULTS.md)
  verschlechtern sämtlich den Flux und verletzen Konstruktionsbedingungen,
  obwohl lineare Modelle Abstieg vorhersagen und Ableitungen bestehen.
  Das separat [geprüfte quadratische Modell](optimization/GEOMETRIC_CURVATURE_RESULTS.md)
  erklärt alle sechs Verschlechterungen mit mindestens99,60% kleinerem
  Vorhersagefehler. Der folgende [GN-Suchlauf](optimization/CURRENT_START_GN_RESULTS.md)
  ist nun vollständig wiederholt, auditiert und fein geprüft:0,754% Fluxgewinn,
  weiterhin unzulässig und nicht nachgewiesen konvergiert.
- Der [frische lokale native Aufbau](validation/FRESH_NATIVE_INTEGRATION_RESULTS.md)
  besteht alle 21 Phasen und sechs wissenschaftlichen Tests ohne Skip.
  Der erweiterte W7-X-Dateivergleich bleibt ausdrücklich 60/63.
- [QI-Koordinaten- und Auflösungsprüfungen](qi/README.md) erklären einen Teil
  historischer Unterschiede, nicht alle. Absolute physikalische Drift und
  verlässliche umfassendere QI-Bewertung sind weiterhin offen.
- [Alle sechs Spulennetze](engineering/MESH_FINE_COMPLETION_RESULTS.md)
  bestehen einen unabhängig geprüften, eingeschränkten Nichtüberlappungstest.
  Nachbarpaare, vollständige Baugruppen und gültige Mechanik bleiben offen.

Zahlen, Prüfgrenzen und wissenschaftliche Einordnung: [Ergebnisstand](STATUS.md).
Die vollständige Chronologie bleibt im [Forschungsjournal](logbook/README.md).

## Wie Erfolg beurteilt wird

Klassische Optimierung, globale Suche, robuste Verfahren und lernende Modelle
müssen denselben unabhängigen Bewertungsweg bestehen. AI ist weder Zielgröße noch
Qualitätsnachweis. Neue Versuche, Budgets und Grenzwerte werden vorab festgelegt;
negative Resultate bleiben erhalten. Eine zulässige klassische Baseline geht dem
fairen mehrstartigen Vergleich und einer behaupteten robusten Paretoverbesserung voraus.

## Detailbereiche

- [Optimierung](optimization/README.md): Orakel, Ableitungen, Suchversuche und Diagnosen.
- [Geometrie](geometry/README.md): Diskretisierung, Krümmung und kontinuierliche Abstandsgrenzen.
- [QI-Physik](qi/README.md): Daten, Bouncewirkung, Feldlinien, Druck und Koordinaten.
- [Ingenieurmodelle](engineering/README.md): Fertigungsfehler, Netze, Mechanik und freie Plasmagrenze.
- [Validierung](validation/README.md): Evidenz, Umgebung, W7-X und übergreifende Audits.
- [SQuID-C](squid_c/README.md): Datenanforderung, Aufnahme und Bereitschaftsprüfungen.
- [Forschungsjournal](logbook/README.md): Befunde, Entscheidungen und chronologische Prüfprotokolle.

Verbindliche Arbeitsregeln: [AGENTS.md](../AGENTS.md). Nach jedem abgeschlossenen
Arbeitsschritt Detailbericht und Prüfvermerk ergänzen, beide READMEs/Stand/Plan
prüfen, relevante Tests ausführen und lokal committen. Die Dokumenthierarchie
bleibt flach: drei Übersichtsseiten und sieben zweckgebundene Detailordner.
