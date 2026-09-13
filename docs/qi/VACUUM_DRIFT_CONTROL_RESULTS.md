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
separat. Nächster Schritt: Matrixquadratur, beide Wirkungsableitungen und unabhängige
skalare Gegenrechnung implementieren, kontrollieren und vor Matrixauswertung committen.
