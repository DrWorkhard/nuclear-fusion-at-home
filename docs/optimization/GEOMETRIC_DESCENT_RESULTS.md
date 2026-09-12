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

## Quellgebundener Modelllauf vorbereitet

Der additive Treiber bindet genau die beiden abgeschlossenen Stromminimierer
und sämtliche zugehörigen Qualifikations-/Holdoutaudits. Aus dem vollständigen
serialisierten Stromgraphen werden drei Stromspalten identifiziert, alle204
anderen Spalten bilden den unveränderten geometrischen Suchraum. Benannte
Quellvektoren und exakt stromunabhängige137 Geometriezeilen werden geprüft.

Sechs feste LPs speichern vollständige Eingaben, Solverausgaben/Marginalwerte,
geometrische Schritte und lineare Vorhersagen. Separater Dateiaudit rekonstruiert
die Matrix und prüft alle Primal-Dual-Nachweise ohne weitere LP-Lösung. Drei
synthetische Ablaufkontrollen bestehen: kompletter Sechserlauf/Audit, manipulierter
Dualwert/Radiusreihenfolge/Quellvektor/Stromableitung sowie erhaltener Eingabesatz
bei absichtlich unterbrochenem Solver. Insgesamt elf neue Modellkontrollen bestanden.
Noch keine echte Modell- oder Feldrechnung; nach Commit zunächst alle sechs
Modelle und ihren Audit schließen, danach die bereits festgelegten nativen
Ableitungs- und Kontrollschritte. Keine Anpassung der Radien aus LP-Ergebnissen.
Gesamte Regression645 Tests bestanden,144 bekannte Fixture-DeprecationWarnings;
Ruff/Dokumentstruktur/Diffprüfung bestanden. Strenge Importqualifikation weiterhin offen.
