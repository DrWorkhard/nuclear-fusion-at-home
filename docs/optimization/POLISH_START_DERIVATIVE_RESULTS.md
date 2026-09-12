# Ableitungen am festen Nachoptimierungsstart: Vorbereitung

2026-09-12, [Protokoll](POLISH_START_DERIVATIVE_PROTOCOL.md) bei11e3c3f
vorab registriert. Ein neuer Runner berechnet genau ein natives Bundle und
sieben unabhängige Paarwert-Auswertungen am ursprünglichen festen Start.
Explizite benannte Quell-/Zielpermutation; die gescheiterte Seed46-Richtung
wird in ihrer ursprünglichen physischen Basis wiederverwendet.

Der separate Auditor benutzt eine reelle Sinus-/Kosinus-Schleife und die
gewichtete Kettenregel statt des komplexen Kerns. Physische Symmetriekopien
werden zusätzlich skalar aus JSON-Winkel/Reflexion rekonstruiert statt native
Rotationsmatrizen zu übernehmen. Alle120 Zeilen und beide Richtungen bleiben
im vollständigen Vergleich. Keine Änderung alter Geometrie-/Suchkerne.

Kontrollen: konstante analytische Distanz samt Log-Sum-Exp-Offset, gemeinsame
Translation, zufällige Fourierkurven gegen komplexen Kern, benannte Permutation,
feste Koeffizienten, verschachtelte Rotation/Reflexion sowie ungültige Eingaben.
Alle18 gezielten Kontrollen und Ruff/Dokument-/Diffprüfung bestehen.
Noch kein reales Qualifikationsergebnis oder neuer Suchlauf.
