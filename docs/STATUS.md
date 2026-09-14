# Ergebnisstand und wissenschaftliche Bewertung

Stand: 14. September 2026, nach unabhängiger Ablehnung des ersten Plasmaentwurfs.
[Projektübersicht](README.md) · [Arbeitsplan](PROJECT_PLAN.md)

## Gesamturteil

**Jetzt aktiv: Schritt3 nach neuem ausdrücklichem Nutzerauftrag.** Die
[registrierte Plasmaoptimierung](qi/PLASMA_OPTIMIZATION_RESULTS.md) hat eine um
0,4mm in zbs(1,1) veränderte nfp2-Vakuumform ausgewählt:14,35% kleinerer
Trainings-S-Wert nach16 neuen Suchgleichgewichten. Alle19 Kaltstarts und die
feinere unabhängige Abnahme sind jetzt abgeschlossen:15,53% schlechterer
erweiterter S-Wert und20 lokale Wirkungsverletzungen. Quellen, Wiederholung,
Felder, Konturen, Tracer und alle Verfeinerungen bestehen. Der Entwurf wird
abgelehnt; Schritt3 bleibt offen. Schritt1/2 bleiben abgeschlossen.

**Schritt1 und2 sind als begrenzte Basis- und Iterationsfähigkeit abgeschlossen.**
Die [konsolidierte Abnahme](validation/FOUNDATION_ACCEPTANCE_RESULTS.md) besteht:
720 Tests mit144 bekannten Warnungen, sechs strikte W7-X-/Goodman-Datenregressionen
ohne Skip, zwei exakt wiederholte24-Bundle-Solverpfade, separate Audits und alle
vier unabhängigen Kandidatenabnahmen. Alle acht Schritt1- und drei Schritt2-Gates
stehen auf Pass. Ein korrekt abgelehnter Entwurf verhindert diesen Basisabschluss nicht.

Unverändert: keine neue zulässige Optimierungsbaseline, kein SoTA-/Kraftwerksvorteil,
keine vollständige SQuID-C-Qualifikation. Globale QI-/Orbit-/Mechanikarbeit bleibt
erhalten und offen, ist aber nicht Teil der jetzigen LPQA-Filamentabnahme.
Historische umfassendere Abschlussformulierungen sind durch die ausdrückliche
Planänderung ersetzt; ihre numerischen Befunde werden nicht umetikettiert.

## Erhaltene Spulenforschung: spätere Leistungsbaseline

Die beste fein geprüfte LPQA-Form stammt aus dem klassischen
[GN-Folgelauf vom fixierten Stromminimum](optimization/CURRENT_START_GN_RESULTS.md).
Beide2048-Bundle-Pfade exakt wiederholt und unabhängig auditiert; alle vier
Abnahmephasen abgeschlossen. Feiner Roh-Flux8,129882387125932e-8, erforderlich
höchstens1e-8: weiterhin Faktor8,13 zu hoch. Gegenüber dem Stromminimum sinkt der
Flux um0,754%. Geometrie und zusätzliche native Prüfungen bestehen, aber keine
vollständige Pareto-Dominanz. Beide Läufe enden am Budget; keine nachgewiesene
Konvergenz oder allgemeine Methodenrangfolge. Vorherige exakte Stromminimierung
half bei festgehaltener Geometrie praktisch nicht.

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
ist nicht abschließend geklärt. Keine DOFs entfernt; die Diagnose selbst ist kein
Entwurfsgewinn. Der spätere GN-Folgelauf ist oben separat bewertet.

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
| Absolute Drift / analytische Kontrolle | Zwei81-Zellen-Kontrollen samt45/243 unabhängigen skalaren Zuständen bestehen; nichtverschwindende radiale Drift und gleiche Phase geprüft | Erste Ordnung auf eingefrorener Feldlinie; bis74% relativer Flusslabelhub bei10keV, keine validierte endliche Bahn oder echte QI-Gesamtqualifikation |
| QI / Gleichgewichte | Frische 16-Zellen-Studie vollständig auditiert; doppelte Solver-Winkelauflösung besteht untersuchte Feldidentitäten | Ursprünglich nur 9/16 Auswertungsverfeinerungen und 2/16 historische Feld-Fidelitätspässe; keine Zelle besteht alle ursprünglichen Schirme |
| QI / gemeinsamer Winkel | 120 neue Gitter und 61.440 unabhängige skalare Inversionen bestätigen die Koordinatenrechnung | Nur 4/16 neue Fidelitäts- und 5/16 Vergleichsverfeinerungspässe; Parametrisierung erklärt nicht sämtliche Unterschiede |
| Endliche Spulennetze | Alle sechs Auflösungen bestehen den nicht-gemeinsame-Vertexindizes-Teiltest; feinster Lauf mit 2.222.785 Paarprüfungen und exakt altem 2M-Präfix auditiert | Nachbarpaare, vollständige Baugruppen, reale Wicklungspakete und gültige Mechanik offen; alte große Verformung verletzt lineare Modellannahmen |
| Software | 766 Tests, Ruff und Dokumentstrukturprüfung bestanden | 144 dokumentierte Fixture-Warnungen; separater strenger netCDF4-Importtest scheitert an Größenwarnung. Keine behauptete ABI-/Warnungsfreiheit |

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

## Abschluss und Übergabe

`foundation-acceptance-v2` ist vollständig bestanden; der erste Lauf bleibt samt
fehlerhaftem Metadatenvergleich und negativem Gesamtaudit erhalten. Die Korrektur
änderte keine numerischen Kriterien. Beide Demonstrationskandidaten bleiben mit
8,191664e-8 gegenüber1e-8 unzulässig; der kurze Zyklus ist kein Leistungsexperiment.
Der frühere bessere Forschungsentwurf wird dadurch nicht ersetzt.

Altbestand bei5971fee lokal getaggt; keine alten numerischen Kerne/Evidenz verändert,
externe Quellen einschließlich bestehender STELLOPT-Anpassungen unverändert.
Bedienung und Grenzen stehen im [Abschlussbericht](validation/FOUNDATION_ACCEPTANCE_RESULTS.md).
Damit endete die Basisarbeit. Die danach ausdrücklich beauftragte Schritt3-Arbeit
ist getrennt registriert; keine automatische Ausweitung auf Schritte4/5.

## Später zu qualifizieren — keine Voraussetzungen für Schritt1/2

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
