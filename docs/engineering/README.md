# Ingenieurmodelle und unabhängige Plasmareaktion

Zweck: das Ziel über ideale Filamentspulen hinaus um Fertigungsfehler, Volumennetze, mechanische Modelle und freie Plasmagrenzen erweitern.

Aktueller Schluss: Softwarepfade und begrenzte Konvergenzprüfungen laufen. Alle sechs untersuchten Netze bestehen intrinsische Qualitätsprüfungen. Nichtlokale Überlappung, reale Baugruppen und eine physikalisch gültige Mechanik sind unqualifiziert; große Verformungen machen die absoluten linearen Spannungsprognosen ungültig.

[Projektübersicht](../README.md) · [Aktueller Stand](../STATUS.md) · [Arbeitsplan](../PROJECT_PLAN.md)

## Dokumente

- [Tetraeder-Nichtüberlappung: Kontrollkern](TETRA_NONOVERLAP_METHOD.md) — Trennrichtungen und unabhängig bestätigte gemeinsame Innenpunkte bestehen zehn Tests; reale Spulennetze/räumliche Vorauswahl noch ungeprüft.

- [FREE_BOUNDARY_PROTOCOL ](FREE_BOUNDARY_PROTOCOL.md) — Protokoll: Unveränderlicher Vakuum-Holdout der Plasmareaktion; getrennt von Optimierung und ohne Rückschreiben.
- [MESH_INTEGRITY_PROTOCOL ](MESH_INTEGRITY_PROTOCOL.md) — Protokoll: Prüfung aller sechs eingefrorenen Netze auf intrinsische Qualität, Orientierung und Randtopologie.
- [ROBUSTNESS_PROTOCOL ](ROBUSTNESS_PROTOCOL.md) — Protokoll: Festgelegte räumlich korrelierte Fertigungsstörungen für Filamentspulen; kein vollständiges Toleranzmodell.
- [STRUCTURAL_PROTOCOL ](STRUCTURAL_PROTOCOL.md) — Protokoll: Qualifikation des Volumennetz-/Mechanikpfads und Diskretisierungsfolge; keine validierte Reaktorstruktur.

Historische Protokolle wurden bei der Ordnerumstellung nicht fachlich verändert.
Darin genannte bloße Dateinamen lassen sich über diese Übersicht bzw. die
[Migrationsliste](../../manifests/documentation-layout-v1.json) auflösen.
