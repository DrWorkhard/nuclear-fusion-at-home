# Festgelegter alternativer LPQA-Konstruktionsstart

Vor neuer Rechnung registriert, 2026-09-12. Ausschließlich Eintrag1 der bereits
vor den Feldrechnungen festgelegten Inventarrangfolge verwenden:
`auto/2026-02-17_083339_92598/order_8/biot_savart_optimized.json`, SHA-256
`40c3abd2c172fdfc94be6a2b5de05ef2e29c3f37c8b4fbd04c6fdb47eef69b4a`.
Die anderen vier Quellen nicht anhand neuer Holdouts auswählen. Die geschlossene
statische Quellenprüfung bleibt unverändert erhalten.

## Explizite Starttransformation und Qualifikation

Vier Fourierkurven der Ordnung8 unverändert übernehmen;16 Kopien mit nfp2 und
Stellaratormetrie,200 Quadraturpunkten. Alle Quellströme gemeinsam mit
`1250075.624635464 / sum(I_source)` skalieren. Erste drei freie Ströme als
`Current(I/1e7)*1e7`, vierter als fester Gesamtstrom minus Summe der ersten drei.
Damit dieselbe feste Stromsumme und207 Freiheitsgrade wie bisher, nicht vier
feste Einzelströme. Quellregulierungen erhalten; keine Gleichsetzung ihrer
Ingenieurbedeutung mit früherem Start oder qualifizierter Mechanik behaupten.

Exaktes bisheriges LPQA-Ziel, Fallkonfiguration und Grenzwerte; geschützte
Konstruktionsziele219,9m/0,99m^-1/8e-9, konservative Spulenabstandsgrenze1,1m.
Unabhängige Abnahme weiterhin220m/1m^-1/1,06m/1,3m und Roh-Flux1e-8.
Neue Vorbereitung ist additiv; alte Quell-/Solver-/Prüfkerne unverändert lassen.

Vor Suche prüfen: autoritative serialisierte Koeffizienten exakt erhalten;
alle16 Ströme relativ zum gemeinsamen Faktor mit normierter Abweichung<=1e-12;
64 bereits festgelegte8x8-Oberflächenpunkte bei200 Spulenpunkten erfüllen
`B_new = factor * B_source` mit normierter Vektorabweichung<=1e-12.
Kanonische Gesamtstromkonstante gegen alte feste Current-DOF-Serialisierung
prüfen; neue Datei über unabhängigen JSON-Graphleser gegen Laufzeitzustand prüfen.
Schwellen/Gitter/207 DOFs explizit prüfen, Namen und Parameterarrays speichern.

Alle138 analytischen Zeilen am neuen Start gegen zentrale Richtungsdifferenzen
mit Seed46, normierter Richtung und Schritten1e-5/1e-6/1e-7/1e-8 prüfen;
letzter normierter Fehler<=1e-6. Unveränderte unabhängige/native Geometrie-/Flux-
Metrikprüfungen<=1e-10, native gekoppelte Feld-/Gradientidentität<=1e-10.
Alle Stufen, Punktfelder, Arrays, Zähler, Quell-/Codehashes und Fehler speichern.
Ableitungsfehler stoppen die Freigabe; keine nachträgliche Toleranzlockerung.

## Anschließender begrenzter Konstruktionsversuch

Nur nach bestandener, unabhängig auditierter und dokumentierter Startprüfung:
unveränderten Jacobispalten-skalierten natürlichen AL-Kern wiederverwenden,
zwei frische identische Wiederholungen mit je1033 Bundles (neun Startproben und
acht getrennte128-Bundle-Stufen), unveränderte Optionen, Auswahl und Schutztests.
Neue Vorbereitung/Qualifikation/Protokoll explizit binden; kein historischer
Suchpräfix zum absichtlich anderen Start erforderlich. Zwei neue Pfade müssen
exakt übereinstimmen. Kein höheres Budget, keine Ordnungserhöhung in diesem Lauf.
Danach unverändert alle vier feinen Abnahmephasen für beide ausgewählten Felder.
Auch negative Ergebnisse dokumentieren. Dies ist ein neuer Start, weder fünf
unabhängige Starts noch allgemeiner Methodenvergleich oder SoTA-Nachweis.

Mindestens2GiB laufend überwachter freier Platz; keine parallele schwere Suche
oder Installation. Vorbereitung/Qualifikation getrennt vom Suchbudget ausweisen;
keine kontrollierte Laufzeitüberlegenheit aus diesen Rechnungen ableiten.
