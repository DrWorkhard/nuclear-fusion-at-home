# Geometrischer Abstieg: Kontrollkerne vorbereitet

2026-09-12, [Protokoll](GEOMETRIC_DESCENT_PROTOCOL.md) bei a56c9e1 registriert.
Noch kein LP mit tatsächlichen Spulendaten und keine neue native Formauswertung.

Der Modellbauer erhält alle Ungleichungen und benutzt unverändertb=g/r, ohne
Addition einer Zulässigkeitstoleranz. Ein verschwindender Gradient wird separat
gemeldet. Der HiGHS-Adapter hat ausschließlich die registrierten Optionen und
bewahrt auch erfolglose Solver-Rückgaben ohne erfundenen Lösungspunkt.

Der getrennte Zertifikatsprüfer benutzt skalare Summen, keinen LP-Löser: primale
Zulässigkeit, Marginal-Vorzeichen, Stationarität, Komplementarität und duale
Kostenlücke. Acht analytische/negative Kontrollen bestehen, einschließlich eines
bekannten Optimums mit gleichzeitig aktiver Ungleichung und Boxgrenze, absichtlich
falscher Dualzeichen/Primalpunkte/Zielfunktion/NaNs, Nullgradient und tatsächlich
unlösbarem LP. Ruff und Dokument-/Diffprüfung bestehen. Dies ist eine Prüfung
des linearen Werkzeuges, keine neue physikalische Optimalitätsaussage.

Nächster Schritt: verbindliche Zwei-Quellen-/DOF-Zuordnung, sechs gespeicherte LPs,
native Richtungs-/Schrittproben und deren separater Quellen-/Kettenregel-Audit.
