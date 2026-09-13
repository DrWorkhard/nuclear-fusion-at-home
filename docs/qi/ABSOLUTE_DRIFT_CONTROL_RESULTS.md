# Absolute Drift am analytischen Spiegel: Aufbau

2026-09-13; [vorab registriertes Protokoll](ABSOLUTE_DRIFT_CONTROL_PROTOCOL.md)
bei2b713c3. Die81-Zellen-Matrix und ihr skalarer Audit sind noch nicht ausgeführt.

## Reine Kontrollen

Der kartesische Rechner bildet Feld, vollen Jacobian, Feldstärkegradient,
Feldlinienkrümmung und beide Clebsch-Gradienten direkt ab. Die allgemeine
erste Driftordnung behält Gradienten- und Krümmungsanteil getrennt. Ein eigener
Einheitenhelfer liefert Einwegwirkung, Transitzeit, Winkel und Frequenz.

Neun Tests bestehen: Clebsch-/Divergenz-/Kraftgleichgewichtsidentitäten,
unabhängige kartesische Differenzen bei beiden festen Schrittweiten,
verschwindende radiale Drift und azimutale Kovarianz, SI-/Ladungs-/Energie-/
Massenskalierung einschließlich Einweg/Vollbounce sowie ungültige Eingaben.
Eine absichtlich verwendete Vakuumvereinfachung liefert hier ein anderes Ergebnis;
dieser stromtragende Kontrollfall verlangt die allgemeine Driftformel.

Keine native Feldrechnung, Gleichgewichtsrechnung oder neue QI-Abnahme.
Ruff, Dokumentstruktur und Diffprüfung bestehen. Die allgemeine Regression bleibt
bis zum nächsten vollständigen Lauf bei dem zuletzt belegten Stand667 Tests;
die neun kleinen Kontrollen sind separat geprüft. Beide READMEs/Status/Plan
geprüft, Gesamturteil unverändert.

## Quadratur-/Auditaufbau vor der Matrix

Der feste81-Zellen-Runner speichert sämtliche kartesischen Felder, Jacobimatrizen,
Clebsch-Gradienten, Driftanteile, Quadraturgewichte und Integranden. Rootaufrufe,
angefragte/fertige Feldpunkte, Warnungen und fehlgeschlagene Zellen werden erhalten;
ein Zellenfehler überspringt nicht die folgenden Auflösungen.

Separater skalarer Weg verwendet eigene Feldliniengeometrie und Root in z statt
der kubischen Root in S, adaptive Einwegintegrale und beide festen Flussdifferenzen.
Die neun Grundfälle werden ausdrücklich per Achsensymmetrie für die drei Winkel
wiederverwendet;45 skalare Root-/Dreifachintegrationsläufe insgesamt, nicht81
unabhängige Geometrien. Jeder angefangene skalare Lauf wird vor seinem Aufruf
ins Ledger aufgenommen; bei Abbruch bleiben Zähler, fertige Integrale und Warnungen.
Ein separater Arrays-/Summen-/Einheiten-/Quellencheck prüft die gespeicherten Werte.

Acht neue Kontrollen bestehen (zusammen mit den neun Grundtests17): unabhängige
skalare Wirkung plus beide FD-Stufen, kleiner Gesamtworkflow mit allen drei
Auflösungen, Vorzeichen/Faktor-zwei/Einheiten-/fehlende-Stufe-Mutationen,
Zellenabbruch ohne Unterdrückung späterer Stufen, ungültige Eingaben, unvollständige
Verfeinerung und abgebrochene skalare/kartesische Arbeit. Testparameter
psi0,02/Bstar1,4 gehören nicht zur registrierten81-Zellen-Matrix. Initiale
Lintbefunde zur Schleifenbindung/Formatierung wurden vor Auswertung korrigiert.
Ruff/Dokumentstruktur/Diff bestehen; gesamte Matrix weiterhin nicht ausgeführt.

Nächster Schritt: den kontrollierten Aufbau committen, dann feste Matrix und
unabhängigen Audit ausführen. GN-Suche und alle Holdouts sind bereits beendet.
Bestehen würde nur den analytischen Normierungsweg qualifizieren, nicht Schritt1.
