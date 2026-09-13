# QI-Physik und Teilchenwirkung

Zweck: eine numerisch belastbare QI-relevante Messung aus offenen Goodman-Gleichgewichten aufbauen.

Aktueller Schluss: Bouncewirkung, Teilbereiche der Konturtopologie und radiale Wirkungsableitungen sind unabhängig gegengeprüft. Absolute Einweg-/Driftnormierung besteht nun im analytischen Spiegel mit81 Zellen und separatem Audit, noch nicht an echten QI-Feldern. Der nfp2-Druckfall bleibt im begrenzten Gauge-Test negativ. Bei nfp3 wechseln25 Familien allein durch Neumarkierung das Vorzeichen; die Kettenregel besteht. Invariantenbereich, globale Topologie, physikalischer QI-Driftmaßstab und Gleichgewichtsauflösung bleiben offen.

[Projektübersicht](../README.md) · [Aktueller Stand](../STATUS.md) · [Arbeitsplan](../PROJECT_PLAN.md)

## Dokumente

- [Absolute Drift: analytisches Kontrollprotokoll](ABSOLUTE_DRIFT_CONTROL_PROTOCOL.md) — Definierter stromtragender Spiegel, kartesische Drift gegen Wirkungsableitung, Einweg-/SI-Normierung,81 feste Zellen und separater skalarer Audit; keine QI-Gesamtfreigabe.
- [Absolute Drift: abgeschlossen](ABSOLUTE_DRIFT_CONTROL_RESULTS.md) — Alle81 Zellen/27 Verfeinerungslinien,45 skalare Referenz-/FD-Läufe und absolute SI-Prüfungen bestehen; maximal1,552e-10 relative direkte/skalar-analytische Driftabweichung. Echter QI- und nichtverschwindender radialer Driftfall offen.

- [Gemeinsamer Feldlinienwinkel: Protokoll](QI_PEST_FIDELITY_PROTOCOL.md) — Neue Diagnose eines möglichen Parametrisierungsbeitrags zu den16 frischen/historischen Feldunterschieden; feste Inversion/Kettenregel/Brent-Gegenprüfung, alte Ergebnisse unverändert.
- [Gemeinsamer Feldlinienwinkel: Ergebnis](QI_PEST_FIDELITY_RESULTS.md) — Alle120 Gitter/61.440 unabhängigen Roots bestätigt; Parametrisierung erklärt einen Teil der Abweichung, aber nur4/16 neue Fidelitäts- und5/16 Vergleichsverfeinerungsschirme bestehen. Keine Gesamt-QI-Freigabe.

- [Autoren/Produzenten](QI_PRODUCER_INVENTORY.md) — Vier9.0-Wouts und Eingaben gebunden; strenge Fluss-Bitgleichheit scheitert auf Rundungsniveau. VMEC++-Iterationsoption ist keine historische Produzentenidentität.
- [Frische QI-Auflösung: Protokoll](QI_FRESH_RESOLUTION_PROTOCOL.md) — Vier Fälle mit je2x2 radialer/Winkel-Verfeinerung; feste Solvergrenzen, Quellen-/Feldgegenprüfung und unveränderte alte Ergebnisse.
- [Frische QI-Auflösung: Ergebnis](QI_FRESH_RESOLUTION_RESULTS.md) — Alle16 Kaltstarts und96 Feldgitter unabhängig geprüft; feinere Winkelauflösung besteht die Identitäten, aber nur9/16 Zellen den Auswertungsverfeinerungs- und2/16 den historischen Fidelitätsschirm. Keine Gesamtfreigabe.

- [Clebsch-Spektrum: Protokoll](QI_CLEBSCH_SPECTRAL_PROTOCOL.md) — Unveränderte Halbflächen,64/128-Gitter, exakte gespeicherte Modenmaske, Projektions- und Parseval-Gegenrechnung.
- [Clebsch-Spektrum: Ergebnis](QI_CLEBSCH_SPECTRAL_RESULTS.md) —48 Endpunktgitter unabhängig geprüft; stabile Projektionen, aber alle verfehlen1e-5. Einfache Feldmoden-Trunkierung allein erklärt die Darstellungsabweichung nicht.

- [Clebsch-Interpolation: Protokoll](QI_CLEBSCH_INTERPOLATION_PROTOCOL.md) — Algebraische Trennung aller24 Restfelder in Halbflächen- und Interpolationsbeiträge; unveränderte Grenzwerte.
- [Clebsch-Interpolation: Ergebnis](QI_CLEBSCH_INTERPOLATION_RESULTS.md) — Alle24 Zerlegungen unabhängig bestätigt; zehn von48 Halbflächengittern scheitern bereits ohne Interpolation. Radiale Produktinterpolation allein als Erklärung ausgeschlossen.

- [Clebsch-Normierung: Protokoll](QI_CLEBSCH_PROTOCOL.md) — Vier feste Wout-Fälle, signierter Fluss samt2pi-Faktor, unabhängige Fourierdarstellungen und Negativkontrollen; keine absolute Driftfreigabe.
- [Clebsch-Normierung: Ergebnis](QI_CLEBSCH_RESULTS.md) — Alle24 Feld-/Fehlerrechnungen unabhängig bestätigt;19 Gitter bestehen, fünf poloidale Identitäten verfehlen die feste Grenze. Keine absolute Driftfreigabe.

- [Drift und Koordinaten](QI_DRIFT_COORDINATES.md) — Primärquellen-/Kettenregeleinordnung: beide Driftkomponenten und dieselbe physikalische Phase transformieren; reine algebraische Kontrolle, noch keine absolute Frequenzvalidierung.

- [Radiale Gauge: Ergebnis](QI_RADIAL_GAUGE_RESULTS.md) — Alle84 alten Traces exakt wiederholt; 25 nfp3-Familien wechseln unter Neumarkierung das Vorzeichen, unabhängige Zuordnungs-/Kettenregelprüfung besteht.

- [Radiale Gauge: Protokoll](QI_RADIAL_GAUGE_PROTOCOL.md) — Vorab festgelegte Kettenregel-/Vorzeichendiagnose unter radialer Feldlinien-Neumarkierung; unveränderte Fälle, Pitchwerte und Pflicht zum exakten Standard-Replay.

- [QI_COVERAGE_TOPOLOGY_PROTOCOL ](QI_COVERAGE_TOPOLOGY_PROTOCOL.md) — Protokoll: Erweiterung auf fünf Radien/neun Pitch-Werte und Konturwindung; eine unzugängliche nfp1-Zelle bleibt fehlgeschlagen.
- [QI_COVERAGE_TOPOLOGY_RESULTS ](QI_COVERAGE_TOPOLOGY_RESULTS.md) — Ergebnis: Erweiterung auf fünf Radien/neun Pitch-Werte und Konturwindung; eine unzugängliche nfp1-Zelle bleibt fehlgeschlagen.
- [QI_FINITE_BETA_INVENTORY ](QI_FINITE_BETA_INVENTORY.md) — Dokument: Hash-Inventar von 31 Goodman-Druckgleichgewichten plus Eingaben; Grundlage für Arbeit ohne SQuID-C.
- [QI_MEASUREMENT_PROTOCOL ](QI_MEASUREMENT_PROTOCOL.md) — Protokoll: Definition und erste Qualifikation der Bouncewirkung an drei Vakuumfällen, mit unabhängiger Quadratur.
- [QI_MEASUREMENT_RESULTS_V1 ](QI_MEASUREMENT_RESULTS_V1.md) — Ergebnis: Definition und erste Qualifikation der Bouncewirkung an drei Vakuumfällen, mit unabhängiger Quadratur.
- [QI_PRESSURE_TRACE_PROTOCOL ](QI_PRESSURE_TRACE_PROTOCOL.md) — Protokoll: Zweiter Feldlinien-/Längenrechner für den Druck-Pilot; 84 Trace- und 320 Familienvergleiche.
- [QI_PRESSURE_TRACE_RESULTS ](QI_PRESSURE_TRACE_RESULTS.md) — Ergebnis: Zweiter Feldlinien-/Längenrechner für den Druck-Pilot; 84 Trace- und 320 Familienvergleiche.
- [QI_RADIAL_ACTION_PROTOCOL ](QI_RADIAL_ACTION_PROTOCOL.md) — Protokoll: Vier eingefrorene Vakuum-/Druckfälle, feste Invarianten und 320 Muldenfamilien; keine globale maximum-J-Aussage.
- [QI_RADIAL_ACTION_RESULTS ](QI_RADIAL_ACTION_RESULTS.md) — Ergebnis: Vier eingefrorene Vakuum-/Druckfälle, feste Invarianten und 320 Muldenfamilien; keine globale maximum-J-Aussage.
- [QI_TRACE_CROSSCHECK_PROTOCOL ](QI_TRACE_CROSSCHECK_PROTOCOL.md) — Protokoll: Unabhängige VMEC-Fourierrekonstruktion, Feldlinieninversion und Gegenprüfung des ersten Vakuum-Piloten.
- [QI_TRACE_CROSSCHECK_RESULTS ](QI_TRACE_CROSSCHECK_RESULTS.md) — Ergebnis: Unabhängige VMEC-Fourierrekonstruktion, Feldlinieninversion und Gegenprüfung des ersten Vakuum-Piloten.

Historische Protokolle wurden bei der Ordnerumstellung nicht fachlich verändert.
Darin genannte bloße Dateinamen lassen sich über diese Übersicht bzw. die
[Migrationsliste](../../manifests/documentation-layout-v1.json) auflösen.
