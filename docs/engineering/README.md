# Ingenieurmodelle und unabhängige Plasmareaktion

Zweck: das Ziel über ideale Filamentspulen hinaus um Fertigungsfehler, Volumennetze, mechanische Modelle und freie Plasmagrenzen erweitern.

Aktueller Schluss: Softwarepfade und begrenzte Konvergenzprüfungen laufen. Alle sechs untersuchten Netze bestehen intrinsische Qualitätsprüfungen. Nichtlokale Überlappung, reale Baugruppen und eine physikalisch gültige Mechanik sind unqualifiziert; große Verformungen machen die absoluten linearen Spannungsprognosen ungültig.

[Projektübersicht](../README.md) · [Aktueller Stand](../STATUS.md) · [Arbeitsplan](../PROJECT_PLAN.md)

## Dokumente

- [Tetraeder-Nichtüberlappung: Kontrollkern](TETRA_NONOVERLAP_METHOD.md) — Trennrichtungen, Innenpunkte, vollständige Paarbuchhaltung und unabhängige Partition-/Witness-Audits bestehen34 Tests; reale Spulennetze weiterhin ungeprüft.
- [Nichtlokale Netzüberschneidung: Protokoll](MESH_NONLOCAL_PROTOCOL.md) — Sechs unveränderte Netze, sämtliche nicht benachbarten Tetraederpaare, konservative Trenn-/Innenpunktnachweise und unabhängige vollständige Paarbilanz; noch nicht ausgeführt.
- [Nichtlokale Netzüberschneidung: Ergebnis](MESH_NONLOCAL_RESULTS.md) — Scanner und unabhängiger Streaming-Audit auf kleinen positiven/negativen/abgebrochenen Kontrollfällen geprüft;39 gezielte Tests, keine realen Netzergebnisse.

- [FREE_BOUNDARY_PROTOCOL ](FREE_BOUNDARY_PROTOCOL.md) — Protokoll: Unveränderlicher Vakuum-Holdout der Plasmareaktion; getrennt von Optimierung und ohne Rückschreiben.
- [MESH_INTEGRITY_PROTOCOL ](MESH_INTEGRITY_PROTOCOL.md) — Protokoll: Prüfung aller sechs eingefrorenen Netze auf intrinsische Qualität, Orientierung und Randtopologie.
- [ROBUSTNESS_PROTOCOL ](ROBUSTNESS_PROTOCOL.md) — Protokoll: Festgelegte räumlich korrelierte Fertigungsstörungen für Filamentspulen; kein vollständiges Toleranzmodell.
- [STRUCTURAL_PROTOCOL ](STRUCTURAL_PROTOCOL.md) — Protokoll: Qualifikation des Volumennetz-/Mechanikpfads und Diskretisierungsfolge; keine validierte Reaktorstruktur.

Historische Protokolle wurden bei der Ordnerumstellung nicht fachlich verändert.
Darin genannte bloße Dateinamen lassen sich über diese Übersicht bzw. die
[Migrationsliste](../../manifests/documentation-layout-v1.json) auflösen.
