# Nichtachsensymmetrische Vakuumdrift: Grundaufbau

2026-09-13; [Protokoll](VACUUM_DRIFT_CONTROL_PROTOCOL.md) vorab bei4096e70
committet. Vollständige81-Zellen-Matrix und243 skalare Zustände noch nicht ausgeführt.

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

Ruff/Dokumentstruktur/Diff bestehen. Noch keine vollständige registrierte Matrix.
Nächster Schritt: kontrollierten Code committen, dann81 Zellen und243 skalare
Zustände ausführen und unabhängig auswerten. Alte abgeschlossene Rechnungen bleiben unverändert.
