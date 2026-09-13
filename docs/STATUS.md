# Ergebnisstand und wissenschaftliche Bewertung

Stand: 13. September 2026, nach abgeschlossener Strom- und geometrischer
Abstiegsdiagnose. [Projektübersicht](README.md) · [Arbeitsplan](PROJECT_PLAN.md)

## Gesamturteil

**Langfristiger Plan Schritt 1 und 2 sind nicht abgeschlossen.** Unsere Werkzeuge
sind substanziell weiter; der entscheidende Entwurfserfolg fehlt. Keine neue
zulässige Optimierungsbaseline, kein SoTA-/Kraftwerksfortschritt, keine vollständige
SQuID-C-Qualifikation. Ein abgeschlossener negativer Versuch schließt nicht das
zugehörige Forschungspaket. Frühere optimistischere Journaltexte gelten nicht
als aktueller Stand.

## Spulenoptimierung: aktueller Engpass

Die beste fein geprüfte LPQA-Form stammt aus dem wiederholten klassischen
[SLSQP-Lauf mit zusammengesetztem Startgate](optimization/SLSQP_COMPOSITE_RESULTS.md):
beide 2048-Bundle-Suchpfade exakt wiederholt und unabhängig auditiert.
Feiner Roh-Flux 8,191665362116152e-8, erforderlich höchstens 1e-8.
Geometrie und zusätzliche native Prüfungen bestehen. Beide Läufe enden am
Budget; keine nachgewiesene Konvergenz, keine allgemeine Methodenrangfolge.

Die separat [exakt minimierten Ströme](optimization/FIXED_GEOMETRY_CURRENT_RESULTS.md)
senken den feinsten Wert nur auf 8,191664801213237e-8 — weiterhin Faktor8,19 zu hoch.
Bei beiden untersuchten Formen beträgt die feine relative Verbesserung höchstens
0,000016608%. Alle acht Feld-Holdouts sind abgeschlossen und separat nachgerechnet;
Geometrieidentität aller 16 Kopien besteht. Das ist kein relevanter Entwurfsgewinn.

Die anschließende [geometrische Diagnose](optimization/GEOMETRIC_DESCENT_RESULTS.md)
umfasst sechs zertifizierte lineare Modelle,32 komplette native Bundles und 250
unabhängige Checks. Alle sechs Richtungen bestehen die festgelegten
Ableitungsprüfungen, aber jeder endliche Schritt erhöht den Flux und verletzt
die Konstruktions-Auswahlgrenze. Keine feine Abnahme dieser Probes. Das lineare
Modell ist bei diesen Radien unzureichend; weder globales Optimum noch falsche
Ableitungen sind damit belegt. Die nun abgeschlossene
[Krümmungsprüfung](optimization/GEOMETRIC_CURVATURE_RESULTS.md) bestätigt alle
sechs quadratischen Vorzeichen mit mindestens99,60% weniger Vorhersagefehler.
Beide vollständigen Feldmatrizen sind unabhängig qualifiziert. Rang203/207 bei
festem numerischen Cutoff deutet auf schwache/redundante Richtungen; deren Ursache
ist nicht abschließend geklärt. Keine DOFs entfernt, kein neuer Entwurf gewonnen.

Frühere Teilerfolge bleiben gültig, eng begrenzt: Die räumliche Residuen-Darstellung
senkte bei gleichem300-s-Budget den Feldfehler an einem Startpunkt etwa 2,35-fach;
trotzdem waren alle Entwürfe unzulässig. Fünf separat rekonstruierte Archivfelder
lagen mit tatsächlichem Roh-Flux nahe 1e-6 rund 100-mal über der Grenze. Geschwellte
Nullmeldungen sind keine Zulassung. Details und alle erhaltenen Fehlschläge:
[Optimierungsübersicht](optimization/README.md).

## Prüfwerkzeuge: was besteht, was nicht?

| Bereich | Belegter Teilfortschritt | Offene Grenze |
| --- | --- | --- |
| W7-X / native Reproduktion | Ausgewählte physikalische Regression und frischer lokaler 21-Phasen-Aufbau bestehen; sechs wissenschaftliche Tests ohne Skip | Erweiterter W7-X-Dateivergleich 60/63; gleicher Rechner/erlaubte Caches, keine unabhängige Hardware oder Hosted-CI |
| Feld und Geometrie | Unabhängige Biot-Savart-/Ableitungsprüfungen; kontinuierliche Krümmungs-/Abstandsschranken finden übersehene Gitterverletzungen | Gleitkommapolster statt gerichteter Intervallarithmetik; keine vollständige endliche Baugruppe |
| QI / radiale Wirkung | Unabhängige Traces/Quadratur und überprüfte Gauge-Kettenregel | Bei 25 nfp3-Muldenfamilien ändert reine radiale Feldlinien-Neumarkierung die Vorzeichenklasse; kein global gauge-unabhängiger Maßstab |
| QI / Gleichgewichte | Frische 16-Zellen-Studie vollständig auditiert; doppelte Solver-Winkelauflösung besteht untersuchte Feldidentitäten | Ursprünglich nur 9/16 Auswertungsverfeinerungen und 2/16 historische Feld-Fidelitätspässe; keine Zelle besteht alle ursprünglichen Schirme |
| QI / gemeinsamer Winkel | 120 neue Gitter und 61.440 unabhängige skalare Inversionen bestätigen die Koordinatenrechnung | Nur 4/16 neue Fidelitäts- und 5/16 Vergleichsverfeinerungspässe; Parametrisierung erklärt nicht sämtliche Unterschiede |
| Endliche Spulennetze | Alle sechs Auflösungen bestehen den nicht-gemeinsame-Vertexindizes-Teiltest; feinster Lauf mit 2.222.785 Paarprüfungen und exakt altem 2M-Präfix auditiert | Nachbarpaare, vollständige Baugruppen, reale Wicklungspakete und gültige Mechanik offen; alte große Verformung verletzt lineare Modellannahmen |
| Software | 667 Tests, Ruff und Dokumentstrukturprüfung bestanden | 144 dokumentierte Fixture-Warnungen; separater strenger netCDF4-Importtest scheitert an Größenwarnung. Keine behauptete ABI-/Warnungsfreiheit |

Die beiden QI-Verfeinerungsmaße unterscheiden sich: ursprüngliche
Clebsch-Identitätsverfeinerung und spätere Verfeinerung des historischen
Vergleichsfehlers sind nicht derselbe Test. Autorenreferenzen wurden nicht ersetzt.
Der Netznachweis gilt für die ursprünglichen vier Grundspulen, nicht für eine
vollständige 16-Spulen-Baugruppe oder den neuesten optimierten Entwurf.

Belege: [native Integration](validation/FRESH_NATIVE_INTEGRATION_RESULTS.md),
[QI-Auflösung](qi/QI_FRESH_RESOLUTION_RESULTS.md),
[QI-Koordinatenvergleich](qi/QI_PEST_FIDELITY_RESULTS.md),
[Netzabschluss](engineering/MESH_FINE_COMPLETION_RESULTS.md),
[strenge Importwarnung](validation/NETCDF_IMPORT_WARNING.md).

## Noch zu schließen

1. Eine tatsächlich zulässige klassische Spulenbaseline, danach unabhängige
   Wiederholungen und fairer mehrstartiger Vergleich.
2. Physikalisch qualifizierter QI-/Wirkungs-/Driftmaßstab mit festgelegter
   Domänenabdeckung, Mulden-Identität, Gauge- und Gleichgewichtsauflösung.
3. Gültige endliche Spulengeometrie und Mechanik einschließlich belastbarer
   Material-, Lagerungs- und Modellannahmen.
4. Getrennt: unabhängige Ausführung sowie autoritative SQuID-C-Daten und
   Reproduktion der publizierten Zielgrößen. Fehlende Daten sind nicht das einzige Hindernis.

Die [SQuID-C-Prüfliste](squid_c/SQUID_C_READINESS.md) enthält weitere Einzelgates.
Ein fachlicher Review sollte besonders Entwurfszulässigkeit, QI-Zielgröße und
Gültigkeitsbereich der Ingenieurmodelle hinterfragen.
