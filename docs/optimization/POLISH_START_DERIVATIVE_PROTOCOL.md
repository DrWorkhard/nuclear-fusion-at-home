# Nachoptimierungsstart: unabhängige Prüfung der120 Abstand-Ableitungen

Vor neuer Physikrechnung registriert, 2026-09-12; gezielte Reaktion auf den
[unveränderten gescheiterten Startup-Test](SLSQP_POLISH_RESULTS.md).
Keine neue Suchinitialisierung, Optimierung oder Reparatur alter Evidenz.

## Festgelegter Zustand und Richtungen

Genau `evidence/slsqp-polish-v1/summary.json`/`physical_start`, Feldhash
`65b9b85e942fa3ce54467ad29c319b92f1c2756489df4f668e563aa49d5836eb`.
Das ist der übernommene AL-Kandidat, **nicht** die ausgewählte Differenzentest-Probe.
Bestandener separater Postmortem v2 und alle ursprünglichen neun Bundles binden.
Benannte207-DOF-Quellbasis dieses fehlgeschlagenen Starts beibehalten. Darin
Seed46 (exakt gescheiterte Richtung) und Seed47, jeweils normiert, festlegen.
Explizite physische Kurven-/Strombaumzuordnung bei erneuter nativer Vorbereitung;
Jacobi-Spalten in die Quellbasis zurückführen, keine zufällige Runtime-Sortierung.

Genau ein neues vollständiges natives Wert-/Jacobi-Bundle am festen Zustand
speichern. Alle138 Werte gegen den ersten alten Ledgerpunkt, die Seed46-
Richtungsableitung gegen alle alten138 analytischen Einträge prüfen: normiert
jeweils<=1e-12. Kein erneuter realer FD-Lauf oder günstigere Schrittweitenwahl.
Die18 Nicht-Paar-Zeilen müssen weiter den originalen letzten FD-Schirm1e-6
bestehen; die vier gescheiterten Paarzeilen bleiben als solche gespeichert.

## Unabhängige Paarrechnung und Kriterien

Vorhandenen, unveränderten komplexen Fourier-/Abstandskern benutzen:
16 physische Kurven,200 Punkte, dieselbe a0-Skalierung und ungeänderte
Log-Sum-Exp-Bedingung mit beta512 und1,10m-Abstand. Koeffizienten aus benannten
Quell-DOFs und expliziten Symmetrietransformationen; keine nativen Positions-
oder Geometrieableitungen in dieser Wertrechnung. Zusätzlich alle16 nativen
Positionen mit unabhängiger Fourierrekonstruktion normiert<=1e-12 vergleichen.

Reelle120 Werte gegen neues natives Bundle: normiert<=1e-10.
Feste reelle Anker am ungestörten Zustand. Für beide Richtungen alle komplexen
Schritte1e-12/1e-20/1e-28 auswerten, ohne Konjugation im quadratischen Abstand.
Jede der120 Richtungsableitungen muss normiert<=1e-9 vom nativen Jacobian
abweichen, alle drei Schritte untereinander<=1e-10. Alle drei Stromspalten
der120 geometrischen Zeilen müssen exakt null sein. Alle Arrays/Fehler speichern.

Separater Auditor rekonstruiert Positionen und Richtungspositionen durch explizite
Sinus-/Kosinus-Schleifen. Er berechnet reelle Abstände und Richtungsableitungen
unabhängig über die Kettenregel (gewichtetes Mittel der quadratischen
Abstandsableitungen), ohne komplexen Kern und ohne native Geometrieableitungen.
Alle Werte<=1e-10, alle Ableitungen<=1e-9 gegen nativ und<=1e-10 gegen jede
komplexe Schrittweite; Arithmetik/Klassifikation, Quellbasis und Hashes auditieren.
Einfache analytische Kontrollen und Mutationen vor echter Rechnung.

## Aufwand und Folgerung

Genau ein neues natives Bundle,16 zusätzliche native Positionsabfragen,
sieben unabhängige Paarwert-Auswertungen (33,6 Millionen quadratische
Distanzstichproben); unabhängigen Auditoraufwand separat zählen.
Keine Installation, mindestens2GiB überwachte Reserve, keine parallele schwere
Rechnung. Bei Fehlschlag keine weitere Suchfreigabe.

Auch bei Erfolg bleibt der ursprüngliche all-row-FD-Test negativ. Erst danach
darf ein **separat registrierter** neuer Suchlauf mit zusammengesetztem Gate
vorbereitet werden: unverändertes1e-6 für Nicht-Paar-Zeilen und unabhängig
qualifizierte Paarableitungen statt instabiler Differenzen. Nicht schon aus
dieser Diagnose eine neue zulässige Baseline ableiten.
