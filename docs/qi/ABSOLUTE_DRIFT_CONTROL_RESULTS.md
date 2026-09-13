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

Nächster Schritt: feste Quadraturmatrix implementieren, separaten skalaren
Wirkungs-/Ableitungsaudit kontrollieren und vor der Auswertung committen.
Bestehen würde nur den analytischen Normierungsweg qualifizieren, nicht Schritt1.
