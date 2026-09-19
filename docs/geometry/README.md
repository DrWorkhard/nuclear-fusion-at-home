# Geometrische Zulässigkeit

Zweck: Krümmung und Abstände unabhängig von den Optimierungsstützstellen beurteilen.

Aktueller Schluss: Grobe Gitter können reale Krümmungsverletzungen übersehen. Positionszeugen und kontinuierliche Fourier-Schranken sind geprüft. Die Schranken verwenden gewöhnliche Gleitkommaarithmetik mit Polster; vollständige Wicklungspaket- und Selbstüberschneidungsprüfungen fehlen.
Die neue außenliegende Startkonstruktion besteht auch real für alle zwölf
Varianten: unabhängige Snapshot-Fehlerübertragung, kontinuierliche Schranken
und alle72 direkten Prüfungen. Nur Filament-Startgeometrie, kein Feldpass.
Der nachfolgende Feldstart ist numerisch qualifiziert, physisch weiterhin
unzulässig. Vor neuen Suchschritten wird eine kumulative Sicherheitsschranke
für veränderte Kurven separat qualifiziert; kein vererbter Seedpass.

[Projektübersicht](../README.md) · [Aktueller Stand](../STATUS.md) · [Arbeitsplan](../PROJECT_PLAN.md)

## Dokumente

- [Spulenänderungen: kumulatives Perturbationsprotokoll](COIL_PERTURBATION_PROTOCOL.md) — Neue D0/D1/D2-Schranken für Abstand/Länge/Krümmung und einfache Projektion gegen unveränderliche Seeds; analytische Kontrollen und feste feldfreie52-Zustandsmatrix vor späterer Suche.
- [Spulenänderungen: Grundbausteine qualifiziert](COIL_PERTURBATION_RESULTS.md) — 200 neue Kontrollen und1840 Gesamttests bestanden; getrennte mathematische Konstruktion/Abnahme, Quellenbinder und zusätzlicher Review. Reale Matrix/Gesamtworkflow noch offen.

- [Außenliegende Startspulen: Protokoll](CLEAR_COIL_INITIALIZATION_PROTOCOL.md) — Gemeinsames3D-Plasmaenvelope, Kreis-/konvexe Fourier-LPs und unveränderte unabhängige Geometriegrenzen vor einem neuen Feldfit.
- [Außenliegende Startspulen: Ergebnisse](CLEAR_COIL_INITIALIZATION_RESULTS.md) — Alle zwölf realen Varianten geometrisch angenommen, beide Formstarts ausgewählt; vollständiger Review-/Prüfverlauf, keine Feld-/Schritt4-Zulassung.

- [CONTINUOUS_COIL_CLEARANCE_CHECK ](CONTINUOUS_COIL_CLEARANCE_CHECK.md) — Dokument: Retrospektive, zwischen allen Stützstellen gültige Abstandsuntergrenze aus Fourier-Ableitungsschranken.
- [CONTINUOUS_CURVATURE_PROTOCOL ](CONTINUOUS_CURVATURE_PROTOCOL.md) — Protokoll: Kontinuierliche Krümmungseinschließung; analytische Kontrollen und Prüfung eingefrorener Felder.
- [CONTINUOUS_CURVATURE_RESULTS ](CONTINUOUS_CURVATURE_RESULTS.md) — Ergebnis: Kontinuierliche Krümmungseinschließung; analytische Kontrollen und Prüfung eingefrorener Felder.
- [CURVATURE_ALIASING_AUDIT ](CURVATURE_ALIASING_AUDIT.md) — Dokument: Unabhängige Positions-/Krümmungszeugen bestätigen von groben Optimierungsgittern übersehene Verletzungen.
- [CURVATURE_ALIASING_RESULTS ](CURVATURE_ALIASING_RESULTS.md) — Ergebnis: Unabhängige Positions-/Krümmungszeugen bestätigen von groben Optimierungsgittern übersehene Verletzungen.

Historische Protokolle wurden bei der Ordnerumstellung nicht fachlich verändert.
Darin genannte bloße Dateinamen lassen sich über diese Übersicht bzw. die
[Migrationsliste](../../manifests/documentation-layout-v1.json) auflösen.
