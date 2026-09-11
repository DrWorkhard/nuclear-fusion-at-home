# Optimierung und Spulendesign

Zweck: reproduzierbare Optimierungsorakel, geprüfte Ableitungen und kontrollierte Suchversuche auf dem offenen LPQA-Fall.

Aktueller Schluss: Die räumliche Residuen-Darstellung senkt bei gleichem Zeitbudget den Magnetfeldfehler an einem Startpunkt um etwa Faktor 2,35. Kein Kandidat erfüllt alle Zulässigkeitsgrenzen. Direkte Ungleichungen sind nun an zwei eingefrorenen Feldern qualifiziert, aber noch kein Suchergebnis.

[Projektübersicht](../README.md) · [Aktueller Stand](../STATUS.md) · [Arbeitsplan](../PROJECT_PLAN.md)

## Dokumente

- [Direkter SLSQP-Pilot: Protokoll](DIRECT_SLSQP_PILOT_PROTOCOL.md) — Neue beschränkte Konstruktion mit zwei festen 256-Bundle-Budgets und unabhängiger Prüfung beider Kandidaten; keine Umdeutung zum früheren Methodenvergleich.
- [Direkte Ungleichungen: Qualifikation](DIRECT_INEQUALITY_QUALIFICATION_RESULTS.md) — Alle 138 Zeilen bestehen die feste Ableitungsprüfung; unabhängige/native Metriken stimmen überein. Noch keine neue Konstruktion.
- [AFFINE_FEASIBILITY_PROTOCOL ](AFFINE_FEASIBILITY_PROTOCOL.md) — Protokoll: Feste Koordinatenskalierung ermöglicht gleiche verbrauchte Budgets; beide Methoden bleiben im Holdout unzulässig.
- [AFFINE_FEASIBILITY_RESULTS ](AFFINE_FEASIBILITY_RESULTS.md) — Ergebnis: Feste Koordinatenskalierung ermöglicht gleiche verbrauchte Budgets; beide Methoden bleiben im Holdout unzulässig.
- [BATCHED_QUALIFICATION_FAILURE ](BATCHED_QUALIFICATION_FAILURE.md) — Dokument: Erhaltener JSON-Serialisierungsfehler beim ersten Ableitungsversuch; exakte Abgrenzung zum erfolgreichen Retry.
- [BATCHED_SPATIAL_JACOBIAN_PROTOCOL ](BATCHED_SPATIAL_JACOBIAN_PROTOCOL.md) — Protokoll: Analytische Ableitung in 16 Spulenkontraktionen; Kontrollformeln, Matrixvergleich und wiederholte Zeitmessungen.
- [BATCHED_SPATIAL_JACOBIAN_RESULTS ](BATCHED_SPATIAL_JACOBIAN_RESULTS.md) — Ergebnis: Analytische Ableitung in 16 Spulenkontraktionen; Kontrollformeln, Matrixvergleich und wiederholte Zeitmessungen.
- [DIRECT_INEQUALITY_QUALIFICATION_PROTOCOL ](DIRECT_INEQUALITY_QUALIFICATION_PROTOCOL.md) — Protokoll: Vorgesehene Qualifikation konservativer glatter Geometrie-Ungleichungen; noch kein beschränkter Optimierungslauf.
- [GUARDED_FEASIBILITY_PROTOCOL ](GUARDED_FEASIBILITY_PROTOCOL.md) — Protokoll: Suchkonstruktion mit Geometriereserven und feinerer Krümmung; wiederholbar, Magnetfeldfehler bleibt zu groß.
- [GUARDED_FEASIBILITY_RESULTS ](GUARDED_FEASIBILITY_RESULTS.md) — Ergebnis: Suchkonstruktion mit Geometriereserven und feinerer Krümmung; wiederholbar, Magnetfeldfehler bleibt zu groß.
- [GUARDED_REPLAY_PROTOCOL ](GUARDED_REPLAY_PROTOCOL.md) — Protokoll: Vorab festgelegte unabhängige Rekonstruktion und Konditionierungsdiagnostik eines gespeicherten Kandidaten.
- [NORMALIZED_FEASIBILITY_PROTOCOL ](NORMALIZED_FEASIBILITY_PROTOCOL.md) — Protokoll: Neuskalierter gemeinsamer Orakelvergleich und unveränderte unabhängige Flux-/Geometrie-Akzeptanz.
- [NORMALIZED_FEASIBILITY_RESULTS ](NORMALIZED_FEASIBILITY_RESULTS.md) — Ergebnis: Neuskalierter gemeinsamer Orakelvergleich und unveränderte unabhängige Flux-/Geometrie-Akzeptanz.
- [OPTIMIZATION_ORACLE_PROTOCOL ](OPTIMIZATION_ORACLE_PROTOCOL.md) — Protokoll: Gemeinsamer benannter Parameterraum, Vektor/Jacobimatrix, Budgets, Wiederholung und erhaltener Aufbaufehler.
- [OPTIMIZATION_ORACLE_RESULTS ](OPTIMIZATION_ORACLE_RESULTS.md) — Ergebnis: Gemeinsamer benannter Parameterraum, Vektor/Jacobimatrix, Budgets, Wiederholung und erhaltener Aufbaufehler.
- [REPLAY_MAPPING_REMEDIATION ](REPLAY_MAPPING_REMEDIATION.md) — Dokument: Ursache der falschen Array-Wiedergabe: Laufzeitnamen ändern die Parameterreihenfolge; benannte physikalische Zuordnung behebt sie.
- [SPATIAL_FLUX_FACTORIZATION_PROTOCOL ](SPATIAL_FLUX_FACTORIZATION_PROTOCOL.md) — Protokoll: Algebraische, zielfunktionserhaltende räumliche Fluxdarstellung; zwei physikalische Zustände und Ableitungskontrollen.
- [SPATIAL_FLUX_FACTORIZATION_RESULTS ](SPATIAL_FLUX_FACTORIZATION_RESULTS.md) — Ergebnis: Algebraische, zielfunktionserhaltende räumliche Fluxdarstellung; zwei physikalische Zustände und Ableitungskontrollen.
- [SPATIAL_FLUX_LOCAL_VJP_PROTOCOL ](SPATIAL_FLUX_LOCAL_VJP_PROTOCOL.md) — Protokoll: Qualifikation derselben Jacobimatrix mittels einzelpunktlokaler adjungierter Ableitungen.
- [SPATIAL_GRAM_CHECK ](SPATIAL_GRAM_CHECK.md) — Dokument: Unabhängige Matrixidentität für den zusätzlich positiven semidefiniten Gauss-Newton-Anteil, ohne Konvergenzbehauptung.
- [SPATIAL_TRF_PILOT_PROTOCOL ](SPATIAL_TRF_PILOT_PROTOCOL.md) — Protokoll: Kontrollierter 128-Vorschläge-Pilot; bessere räumliche Fluxwerte pro Vorschlag, erheblicher Zeitmehraufwand, beide unzulässig.
- [SPATIAL_TRF_PILOT_RESULTS ](SPATIAL_TRF_PILOT_RESULTS.md) — Ergebnis: Kontrollierter 128-Vorschläge-Pilot; bessere räumliche Fluxwerte pro Vorschlag, erheblicher Zeitmehraufwand, beide unzulässig.
- [TIMED_SPATIAL_PILOT_PROTOCOL ](TIMED_SPATIAL_PILOT_PROTOCOL.md) — Protokoll: Zwei 300-Sekunden-Läufe je Darstellung; komplette Abrechnung und unabhängige Ablehnung aller vier Kandidaten.
- [TIMED_SPATIAL_PILOT_RESULTS ](TIMED_SPATIAL_PILOT_RESULTS.md) — Ergebnis: Zwei 300-Sekunden-Läufe je Darstellung; komplette Abrechnung und unabhängige Ablehnung aller vier Kandidaten.

Historische Protokolle wurden bei der Ordnerumstellung nicht fachlich verändert.
Darin genannte bloße Dateinamen lassen sich über diese Übersicht bzw. die
[Migrationsliste](../../manifests/documentation-layout-v1.json) auflösen.
