# Optimierung und Spulendesign

Zweck: reproduzierbare Optimierungsorakel, geprüfte Ableitungen und kontrollierte
Suchversuche auf LPQA sowie gepaarte Spulenrealisierung der eigenen QI-nahen
Plasmaformen.

Die [geschärfte Basis-/Iterationsabnahme](../validation/FOUNDATION_ACCEPTANCE_RESULTS.md)
ist abgeschlossen. Nachfolgende Studien bleiben als Vorarbeit für spätere
Leistungsverbesserung erhalten; eine neue zulässige Form ist kein offenes Gate
der nun abgeschlossenen Schritte1/2.

Aktueller Schluss: Die bisher beste klassische Spulenform besteht die geprüften Geometriebedingungen, verfehlt die Fluxgrenze aber noch um Faktor8,13. Der vollständig geprüfte GN-Folgelauf verbessert den feinen Flux um0,754%; exakte Stromumverteilung half zuvor praktisch nicht. Noch keine zulässige Baseline oder allgemeine Methodenrangfolge.

[Projektübersicht](../README.md) · [Aktueller Stand](../STATUS.md) · [Arbeitsplan](../PROJECT_PLAN.md)

## Dokumente

- [Blockweise native Referenz: Protokoll](BLOCK_NATIVE_REFERENCE_PROTOCOL.md) — Vier neue volle Ressourcenläufe, native Formel in64 Flächenblöcken,336 Vergleiche mit erhaltenen Backends; alte Speicherfehler bleiben negativ.
- [Blockweise native Referenz: Abschluss](BLOCK_NATIVE_REFERENCE_RESULTS.md) — Alle vier realen Vollgrößenfälle und336 unabhängige Gegenvergleiche bestanden, maximal0,427GiB/38,2s; alte drei RAM-Fehler bleiben negativ. Gesamtworkflow der Feldstartprüfung folgt.

- [Angenommene Geometrie → Feldstart: Protokoll](CLEAR_COIL_FIELD_START_PROTOCOL.md) — Frische benannte Seeds, feste Normierung, N/V-Ableitungen und sechs Auflösungszustände je vier physischer Zellen; keine Suche.
- [Angenommene Geometrie → Feldstart: Arbeitsstand](CLEAR_COIL_FIELD_START_RESULTS.md) — 163 neue Bausteinkontrollen; volle native/Sparse-Gegenrechnung besteht, Ressourcen-Gesamtgate an drei dichten Speicherüberschreitungen abgelehnt. Alle vier Sparse-Fälle bestehen; keine Projekt-Feldfreigabe.

- [Schritt4: Optionen und unabhängige Reviews](COUPLED_DESIGN_OPTIONS.md) — Vergleich von Filament-Co-Design, reduzierten Richtungen, REGCOIL und direkten Flächen; drei Agentenreviews, Integrationsfallen und getrennte Teilpakete für Realisierung, gemeinsame Iteration, Druck und Robustheit.
- [Gepaarte reale Spulen: Pilotprotokoll](COUPLED_COIL_PILOT_PROTOCOL.md) — Zwei Plasmaformen, zwei Spulenklassen und Normalfeld-/Innenvektor-Methoden; explizite Flussableitung, feste Budgets und unabhängige feinere Eintrittsschirme.
- [Gepaarte reale Spulen: negativer Abschluss](COUPLED_COIL_PILOT_RESULTS.md) — Acht Startqualifikationen, sechs budgetierte Suchen und alle feinen Abnahmen; keine Zulassung, grobes Raster übersieht sehr kleine Plasmaabstände, typisierte Audit-Ausgabe getrennt geprüft.

- [GN vom aktuellen Stromminimum: Protokoll](CURRENT_START_GN_PROTOCOL.md) — Separater klassischer Lauf vom fixierten besten Zustand,16-Bundle-Startreplay mit nativer Gramprüfung, zweimal2048 Versuche und vollständige unabhängige Abnahmen.
- [GN vom aktuellen Stromminimum: abgeschlossen](CURRENT_START_GN_RESULTS.md) — Zwei2048-Bundle-Pfade exakt wiederholt/auditiert, alle vier Abnahmephasen geschlossen. Feinster Flux8,129882e-8, Gewinn0,754%, weiterhin abgelehnt; Geometrie/nativ bestehen, keine Pareto-Dominanz.

- [Krümmung der geometrischen Probes: Protokoll](GEOMETRIC_CURVATURE_PROTOCOL.md) — Dieselben zwei Quellen/32 Feldpunkte, vollständige gebündelte/native Matrizen, sechs quadratische Vorhersagen und lokale Spektral-/Stromraumdiagnose.
- [Krümmung der geometrischen Probes: abgeschlossen](GEOMETRIC_CURVATURE_RESULTS.md) — Alle32 Felder/beide Matrizen unabhängig qualifiziert, alle sechs quadratischen Vorzeichen korrekt und mindestens99,60% weniger Vorhersagefehler; lokale Spektren/Stromkopplung geprüft, kein neuer Entwurf.

- [Geometrischer Abstieg: Protokoll](GEOMETRIC_DESCENT_PROTOCOL.md) — Zwei unveränderte Stromminimierer, sechs feste Radius-LPs mit unabhängigem Primal-Dual-Zertifikat, geprüfte Richtungen und maximal32 native Kontrollbundles.
- [Geometrischer Abstieg: abgeschlossen](GEOMETRIC_DESCENT_RESULTS.md) — Sechs LPs sowie32 native Bundles und250 unabhängige Checks abgeschlossen; Ableitungen bestehen, alle sechs echten Schritte erhöhen den Flux und verletzen Konstruktionsbedingungen. Keine Zulassung.

- [Feste Geometrie, optimale Ströme: Protokoll](FIXED_GEOMETRY_CURRENT_PROTOCOL.md) — Zwei unveränderte AL-/SLSQP-Spulenformen, exaktes dreidimensionales Strom-LS-Teilproblem, unabhängiges QR/Provenienz-/Feld-Holdout; klassische Diagnose ohne Neuheitsbehauptung.
- [Feste Geometrie, optimale Ströme: abgeschlossen](FIXED_GEOMETRY_CURRENT_RESULTS.md) — Beide exakten Stromminima,114 unabhängige Checks und alle acht Feld-Holdouts mit separatem Audit abgeschlossen; feinster Gewinn höchstens0,000016608%, beide Formen bleiben unzulässig.

- [SLSQP mit zusammengesetztem Startgate: Protokoll](SLSQP_COMPOSITE_PROTOCOL.md) — Identischer AL-Start und Physik; neuer vollständiger Start-Jacobian-/alter9-Bundle-Replay, unabhängige Paarqualifikation plus unveränderte Nicht-Paar-FD-Grenze, zwei2048-Bundle-Suchen.
- [SLSQP mit zusammengesetztem Startgate: Ergebnis](SLSQP_COMPOSITE_RESULTS.md) — Beide2048-Bundle-Arme exakt wiederholt/auditiert, alle feinen Abnahmen geschlossen; Geometrie/nativ bestehen, Flux8,191665e-8 bleibt unzulässig. Keine Pareto-Dominanz.

- [Nachoptimierungsstart: Ableitungsprotokoll](POLISH_START_DERIVATIVE_PROTOCOL.md) — Fester gescheiterter Startup-Zustand, zwei Quellbasis-Richtungen, drei komplexe Schrittweiten und unabhängige reelle Kettenregel; keine neue Suche.
- [Nachoptimierungsstart: Ableitungsergebnis](POLISH_START_DERIVATIVE_RESULTS.md) — Beide Richtungen/alle120 Paarzeilen qualifiziert, reeller35-Prüfungen-Audit bestätigt; Abweichungen<=4,063e-11 stützen Rundungserklärung. Alter FD-Test bleibt negativ, neue Suche noch offen.

- [SLSQP-Nachoptimierung: Protokoll](SLSQP_POLISH_PROTOCOL.md) — Separater hybrider Versuch vom durch das AL-Ledger festgelegten Kandidaten; zwei2048-Bundle-Arme, gesamte Vorarbeit bilanziert, unveränderte Abnahme.
- [SLSQP-Nachoptimierung: Ergebnis](SLSQP_POLISH_RESULTS.md) — Nach neun Startup-Bundles vor Solverstart an vier Abstand-Ableitungen gestoppt; separater Postmortem bestätigt Daten/negative Klassifikation, Ursachenprüfung folgt.

- [Alternativer Start: Protokoll](UPSTREAM_START_PROTOCOL.md) — Erster vorab ausgewählter Archiveintrag, explizite feste Stromsumme, neue Qualifikation vor unverändertem klassischen Pilot.
- [Alternativer Start: Ergebnis](UPSTREAM_START_RESULTS.md) — Startqualifikation, beide Suchpfade und alle feinen Abnahmen abgeschlossen; Geometrie/nativ bestehen, Flux8,955e-8 bleibt unzulässig. Keine Pareto-/SoTA-Behauptung.

- [Vorhandene LPQA-Felder: Rekonstruktionsergebnis](UPSTREAM_LPQA_RECONSTRUCTION_RESULTS.md) — Alle fünf Quellen-/Feldgegenprüfungen bestanden; tatsächlicher Roh-Flux nahe1e-6 statt gemeldeter Null, alle fünf an1e-8 abgelehnt. Geometrische Gitterschirme bestanden.

- [Vorhandene LPQA-Felder: Rekonstruktionsprotokoll](UPSTREAM_LPQA_RECONSTRUCTION_PROTOCOL.md) — Fünf fest ausgewählte Archivfelder, Symmetrie-/Stromidentität, direkte Biot-Savart-Gegenrechnung und unveränderte feine Gitterabnahme; noch keine vollständige Baselinefreigabe.

- [Vorhandene LPQA-Referenzen: Inventarergebnis](UPSTREAM_LPQA_INVENTORY_RESULTS.md) — 5301 quellgeprüfte Berichte, 27 gemeldet passende Datensätze und fünf unqualifizierte Rekonstruktionskandidaten; 2954 geschwellte Nullmeldungen sind keine Roh-Fluxfreigabe.

- [Vorhandene LPQA-Referenzen: Inventarprotokoll](UPSTREAM_LPQA_INVENTORY_PROTOCOL.md) — Vollständige lokale Metadatenbestandsaufnahme und explizit unqualifizierte Rekonstruktions-Warteliste; keine Gleichsetzung geschwellter Nullwerte mit verschwindendem Feldfehler.

- [Unveränderte AL-Recovery: Ergebnisse](NATURAL_AUGLAG_RECOVERY_RESULTS.md) — Zwei exakt wiederholte Suchläufe und historische Präfixe unabhängig bestätigt; alle feinen Abnahmen abgeschlossen, Geometrie/nativ bestanden, Flux Faktor26,99 über Grenze.

- [Jacobiskalierte AL: Ergebnisse](NATURAL_AUGLAG_JAC_RESULTS.md) — Vollständig wiederholt/auditiert/fein geprüft; Flux rund11,4% kleiner als unskaliert, aber höhere Krümmung und weiter Faktor23,91 über Grenze. Keine Pareto-Dominanz.

- [Jacobiskalierte AL: Protokoll](NATURAL_AUGLAG_JAC_PROTOCOL.md) — Getrennt festgelegter klassischer Ein-Options-Versuch mit `x_scale=jac`; identische Physik/Budgets, erst nach abgeschlossener unveränderter Recovery und Abnahme.

- [Feldstärkenaudit](FIELD_STRENGTH_AUDIT.md) — Prüft an vorhandenen Holdouts, ob bloß geringere Feldstärke die kleineren rohen Fluxwerte erklärt; feste Basisstromsumme und globale Skalenkontrolle, keine neue Abnahmegrenze.

- [Natürliche AL: Wiederherstellungsprotokoll](NATURAL_AUGLAG_RECOVERY_PROTOCOL.md) — Expliziter Einzelarm-/Präfix-Postmortem und neuer unveränderter Zwei-Arm-Lauf; unterbrochene Originalstudie bleibt unqualifiziert.

- [Natürliche Flux-AL: unterbrochener Pilot](NATURAL_AUGLAG_RESULTS.md) — Erster 1033-Bundle-Arm und gespeichertes 700-Bundle-Präfix unabhängig bestätigt; Studie bleibt unvollständig, Wiederholung und Abnahme offen.

- [Natürliche Flux-AL: Protokoll](NATURAL_AUGLAG_PROTOCOL.md) — Klassische Least-Squares-AL mit rohem Flux, analytisch geprüftem Residuum und festem achtstufigem Budget; keine Gleichsetzung mit früherer quartischer Flux-Strafe.

- [SLSQP-1024: geprüftes Ergebnis](DIRECT_SLSQP_1024_RESULTS.md) — Neue Wiederholungen exakt, historischer Präfix/Audit fehlgeschlagen; unabhängige Geometrie/nativ bestehen, Flux Faktor 12,7 über Grenze abgelehnt.

- [Neuer SLSQP-1024-Lauf: Protokoll](DIRECT_SLSQP_1024_PROTOCOL.md) — Klassische Vergleichskonstruktion mit gleichem maximalem Bundlebudget wie GN, unverändertem Originalstart und Pflicht zur Reproduktion des alten 256-Vorschläge-Präfixes.
- [Native Feldprojektion: geprüftes Ergebnis](GN_NATIVE_COVECTOR_RESULTS.md) — Beide 1024-Bundle-Suchen exakt wiederholt und auditiert; feine Geometrie-/native Abnahme besteht, Flux Faktor 24,7 über Grenze abgelehnt.
- [Native Feldprojektion: korrigierter Pilot](GN_NATIVE_COVECTOR_PROTOCOL.md) — Konsistente Identitätsprüfung bei unveränderten Werten/Gradienten/H_GN; drei feste Zustandsprüfungen und Pflicht zur exakten Wiederholung des alten Suchpräfixes.
- [Gespeicherter GN-Fehlerpunkt: Ergebnis](GN_FAILED_POINT_RESULTS.md) — Native Zustandsstabilität und unabhängige Ableitungen bestehen; die separat gerundete Feldprojektion verursacht die Identitätsabweichung im Suchadapter.
- [Gespeicherter GN-Fehlerpunkt: Protokoll](GN_FAILED_POINT_PROTOCOL.md) — Frische native Auswertung, getrennte Feldkovektoren/Matrizen und unabhängige affine Stromprüfung zur Ursachenunterscheidung.
- [GN-Fehlerreplay: Protokoll](GN_FAILURE_REPLAY_PROTOCOL.md) — Höchstens 29 Bundles, exakte Wiederholung des gescheiterten Präfixes und vollständige Erfassung des Fehlerpunkts, ohne Grenzwertänderung.
- [GN-Trust-Pilot: gestoppt](GN_TRUST_PILOT_RESULTS.md) — Nach 28 vollständigen Bundles scheitert die Feld-/Gradientidentität; zweiter Arm nicht gestartet, Fehlerpfad muss den problematischen Punkt vollständig erfassen.
- [GN-Trust-Pilot: Protokoll](GN_TRUST_PILOT_PROTOCOL.md) — Klassischer Solver mit expliziter Fluxkrümmung, festen 1024-Bundle-Grenzen und zwei Wiederholungen; unveränderte unabhängige Abnahme.
- [Quadratisches Feldmodell: Ergebnis](QUADRATIC_FIELD_MODEL_RESULTS.md) — Alle vier Vorzeichen stimmen, mindestens 99,907% geringerer Vorhersagefehler als linear; vollständiger nativer Matrixvergleich und unabhängiger Kern-Audit bestehen.
- [Quadratisches Feldmodell: Protokoll](QUADRATIC_FIELD_MODEL_PROTOCOL.md) — Vorab festgelegte Qualifikation und Vorhersageprüfung an allen vier gespeicherten Testschritten; keine neue Optimierung.
- [Lokale Proben mit unabhängiger Ableitungsprüfung](DIRECT_DESCENT_COMPOSITE_RESULTS.md) — Vier echte Wertprobes: der kleinste Schritt verbessert leicht, größere lineare Abstiege verschlechtern den Flux stark; motiviert quadratisches Feldmodell.
- [Komplexe-Schritt-Abstandsprüfung: Ergebnis](COMPLEX_CLEARANCE_RESULTS.md) — Alle 120 Paar-Richtungsableitungen stimmen an beiden festen Zuständen bis rund 2,4e-12; der alte Differenzentest bleibt als Fehlschlag erhalten.
- [Komplexe-Schritt-Abstandsprüfung: Protokoll](COMPLEX_CLEARANCE_PROTOCOL.md) — Unabhängige Fourier-/Wertberechnung prüft alle 120 Abstandsbeschränkungen; soll Rundungsauslöschung von einem Ableitungsfehler unterscheiden.
- [Lokale Diagnostik: gestoppt](DIRECT_DESCENT_DIAGNOSTIC_RESULTS.md) — Neue Richtungsprüfung verfehlt den festen Grenzwert; keine Abstiegsprobes. Rundungsauslöschung ist eine zu prüfende Vermutung.
- [Lokale Abstiegsdiagnostik: Protokoll](DIRECT_DESCENT_DIAGNOSTIC_PROTOCOL.md) — Prüft das lokale Modell und echte nichtlineare Änderungen mit drei kleinen, begrenzten Schritten; keine Verlängerung des abgeschlossenen Piloten.
- [Direkter SLSQP-Pilot: Ergebnis](DIRECT_SLSQP_PILOT_RESULTS.md) — Exakt wiederholter 256-Bundle-Lauf, unabhängige Auswahlprüfung, Geometrie/nativ bestanden, Flux abgelehnt; Konvergenz offen.
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
