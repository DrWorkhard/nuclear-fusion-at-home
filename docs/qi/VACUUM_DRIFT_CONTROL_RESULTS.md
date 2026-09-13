# Nichtachsensymmetrische Vakuumdrift: beide Komponenten analytisch qualifiziert

2026-09-13; [Protokoll](VACUUM_DRIFT_CONTROL_PROTOCOL.md) vorab bei4096e70
committet. Vollständige81-Zellen-Matrix und243 skalare Zustände bei fccd525
ausgeführt, einschließlich separatem unabhängigem Audit.

## Ergebnis und Gültigkeitsgrenze

Alle81 Zellen/27 Verfeinerungslinien und243 unabhängigen skalaren Grund-/FD-
Zustände bestehen. Radiale reduzierte Einwegdrift in sämtlichen Zellen ungleich
null: Betrag0,06559 bis0,79668. Beide Driftkomponenten, alle drei Markierungen,
gleiche physikalische Phase und SI-Umrechnung geprüft. Keine Warnungen/Abbrüche.

| Prüfung | Größter Fehler | Feste Grenze |
| --- | --- | --- |
| Kartesische radiale / Winkel-Drift gegen integrierte Wirkungsableitung | 3,669e-9 /4,677e-9 | 1e-8 |
| Beide Komponenten gegen unabhängigen skalaren Weg | 2,397e-10 /3,109e-10 | 1e-7 |
| Unabhängige Wirkung / Transitlänge | 1,125e-12 /2,426e-10 | 1e-7 |
| FD nach psi,relative Stufen1e-4 /1e-5 | 2,248e-9 /1,446e-9 | jeweils1e-6 |
| FD nach alpha,absolute Stufen1e-4 /1e-5rad | 1,228e-8 /4,112e-10 | jeweils1e-6 |
| Alle64→128→256 Verfeinerungen | 1,763e-10 | 1e-7 |
| Feld-/Vakuumidentitäten | 5,554e-16 | 1e-12 |
| Gleiche Phasenprojektion unter Gauge | 4,022e-16 | 1e-10 |

Fehlernormen wie registriert; bei Driftkomponenten Nenner mindestens1e-12.
Maximale adaptive absolute Fehlerschätzung8,775e-10 ist nicht mit epsabs allein
zu vergleichen: `quad` verwendet auch epsrel mal Integralbetrag. Alle unabhängigen
Vergleichsgrenzen bestehen; Fehlerschätzungen sind keine mathematischen Schranken.

Kartesischer Aufwand12.096 Punkte/162 Roots/2100 Rootfunktionsaufrufe.
Skalar486 Roots/6027 Rootfunktionsaufrufe,972 adaptive Integrale mit
159.516 Integrandaufrufen (40.257 Wirkung,36.855 Transit,41.769 A_psi,40.635 A_alpha).
Je90 Zell-Auditchecks plus Verfeinerungs-/Gesamtprüfungen bestehen; das sind keine
statistisch unabhängigen Experimente. Rohdaten5,7MiB, keine nativen QI-/Spulenaufrufe.

Beispiel psi0,03/Bstar1,6/alpha0,6/N256: reduzierte dpsi0,2820239600 und
dalpha6,6118846924. Für c=-1,0,+1 wird die Winkelkomponente16,01268,
6,61188 beziehungsweise-2,78891. Die festgehaltene Phasenkontraktion bleibt
38,6372514124: **Vorzeichenwechsel der Winkelkomponente sind keine Änderung
derselben physikalischen Phase.** Hier ist das mit direkter Drift kontrolliert,
nicht nur als Kettenregelalgebra vorgegeben.

Wichtige zusätzliche Einordnung, keine nachträgliche Änderung eines Gates:
Die gewählten10keV-Teilchen sind SI-Testparameter für die **erste Driftordnung
entlang der eingefrorenen Feldlinie**. Bei den feinsten27 Fällen erreicht
abs(Delta_psi)/psi bis0,7361; maximaler Winkelhub0,2508rad. Das sind diagnostisch
berechnete Werte aus gespeicherten Daten, keine vorab registrierte Bahnabnahme.
Eine kleine Abweichung von der Ausgangsfeldlinie ist damit nicht gesichert.
Trotz bestandener algebraisch-numerischer Normierung werden die absoluten Zahlen
**nicht als validierte endliche10keV-Teilchenbahnen** freigegeben. Dazu fehlt
eine unabhängige Bahn-/Kleinparameter-Konvergenzprüfung; keine günstiger gewählte
Energie ersetzt rückwirkend diesen Test.

Schluss: Nichtverschwindende radiale Drift, Winkel-Drift, Vakuumlimit, Einweg-SI-
Normierung und gleiche Phase sind in der festgelegten ersten Ordnung qualifiziert.
Endliche Bahnen, echte QI-Gleichgewichte, Mulden-/Invariantendomäne und Auflösung
bleiben offen. Kein Schritt1-Abschluss oder Stellarator-/maximum-J-Zertifikat.

Evidenz: `evidence/vacuum-drift-control-v1.json`, separater `*-audit.json`,
beide `*-driver/`,81 Arrays unter `artifacts/vacuum-drift-control-v1/`.
Abschließende gesamte Regression700 bestanden/144 bekannte Fixture-Warnungen;
Ruff/Dokumentstruktur/Diff bestanden. Strenge netCDF-Importwarnung unverändert offen.

## Aufbewahrter Grundaufbau vor Ausführung

Neun reine Kontrollen bestehen: exaktes Clebsch-/Vakuumfeld und Feldlinientangente,
alle kartesischen Feld-/Koordinaten-/Feldstärke-/Krümmungsableitungen bei beiden
festen FD-Schritten, beide unsymmetrischen Umkehrpunkte, allgemeine gegen
Vakuumdrift, nichtverschwindende lokale radiale Projektion, alle drei Gauge-
Projektionen derselben physikalischen Phase, radiale SI-Skalierungen und
ungültige Domänen/Rootbrackets samt tatsächlichen Aufrufzählern.

Der kleine Testfall psi0,02/Bstar1,4/alpha0,4 ist kein nachträglich ausgewählter
Matrixfall. Keine Aussage über integrierte radiale Drift oder echte QI-Felder
aus lokalen Projektionen. Keine neue native Gleichgewichts-/Spulenrechnung.

Ruff/Dokumentstruktur/Diff bestehen. Beide READMEs/Stand/Plan geprüft, Gesamturteil
unverändert; volle Regression weiterhin zuletzt687 Tests, neun neue Kontrollen
separat.

## Quadratur-/Auditvorbereitung

Vier weitere Workflowkontrollen bestehen, zusammen13 mit den Grundtests.
Die integrierte radiale und Winkelverschiebung des gesonderten Testfalls stimmen
mit eigener skalarer Geometrie, adaptiver Quadratur und beiden FD-Stufen in
beiden Koordinaten überein. Nichtverschwindende integrierte radiale Testdrift
belegt; keine echte QI-Anwendung daraus abgeleitet.

Der kleine Gesamtworkflow bewahrt alle64/128/256 Stufen und neun skalaren Grund-/
FD-Zustände. Mutationen von radialem Vorzeichen, Faktor zwei, Phase/Gauge,
SI-Einheiten, fehlender FD-Stufe, Jacobian und nichtendlichen Arrays werden
abgelehnt. Mittelzellenfehler unterdrückt spätere Auflösungen nicht; ein
abgebrochenes skalares Integral behält beide Roots und seinen tatsächlichen Aufruf.
Quell-/Protokoll-/Arrayhashes, Versionen, Arbeit, Warnungen, getrennte Driftanteile
und sämtliche Phasenprojektionen werden gespeichert; unabhängiger Auditor
importiert keinen kartesischen Produzenten.

Ruff/Dokumentstruktur/Diff bestanden vor der Auswertung. Der damalige nächste
Schritt ist oben geschlossen. Nun die endliche-Bahn-/Asymptotikgrenze separat
prüfen; alte abgeschlossene Rechnungen und sämtliche Testparameter bleiben erhalten.
