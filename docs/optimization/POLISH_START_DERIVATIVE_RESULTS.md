# Ableitungen am festen Nachoptimierungsstart: unabhängig qualifiziert

## Abgeschlossenes Ergebnis, 2026-09-12

Rechnung und Audit bei42ca07e. Alle120 Paarzeilen bestehen für beide vorher
festgelegten Quellbasis-Richtungen und alle drei komplexen Schrittweiten.
Die ursprüngliche all-row-FD-Qualifikation bleibt fehlgeschlagen. Genau der
ursprüngliche AL-Start wurde geprüft, nicht die beste Differenzentest-Probe.

| Gegenprüfung | Größte normierte Abweichung |
| --- | ---: |
| Neues natives Bundle /138 alte Startwerte |0 exakt|
| Neue / alte analytische Seed46-Richtung |1,066e-14|
| Unabhängige /16 native Positionen |1,111e-15|
| Komplexer reeller Wert / native120 Paarwerte |3,300e-15|
| Komplexe Ableitung / nativ, Seed46 |4,063e-11|
| Komplexe Ableitung / nativ, Seed47 |1,596e-12|
| Drei komplexe Schritte untereinander |1,594e-14|
| Separate reelle Kettenregel / nativ |4,063e-11|
| Separate reelle Kettenregel / komplex |2,804e-11|

Alle1e-9-Ableitungs- und1e-10-Stabilitäts-/Methodenvergleichsgrenzen bestehen.
Alle drei Stromspalten der120 geometrischen Zeilen sind exakt null. Die18
Nicht-Paar-Zeilen bestehen weiterhin ihren unveränderten alten letzten1e-8-
Differenzentest mit maximal2,752e-7 normiert. Der separate Auditor bestätigt
35 Prüfungen: vollständige Arrays, benannte Parameter, JSON-Symmetrien, Quellen,
alte Werte/Ableitungen, reelle Kettenregel, alle komplexen Schritte und Aufwand.

Die unabhängigen Rechnungen stützen die Erklärung des alten Fehlers durch
numerische Auslöschung, nicht durch falsche Paarableitungen. Das ist eine
Zwei-Richtungen-Prüfung an einem Zustand, keine globale Jacobian- oder
Optimierungskonvergenz-Garantie. Keine Physik-/Zulässigkeitsgrenze verändert.

Aufwand: ein neues vollständiges natives Bundle plus16 Positionsabfragen;
sieben komplexkern-basierte Paarwertrechnungen,33,6 Millionen Distanzstichproben.
Auditor separat4,8 Millionen reelle quadratische Distanzstichproben und9,6 Millionen
Richtungsdistanzstichproben, keine nativen oder komplexen Physikaufrufe.
Vorbereitung weiterhin explizit außerhalb eines Suchbudgets; noch keine Suche.

Evidenz: `evidence/polish-start-derivatives-v1.json`, zugehöriger `-driver`,
`evidence/polish-start-derivatives-v1-audit.json`; Roharrays im gleichnamigen
`artifacts/`-Ordner. Vollständige Regression559 Tests bestanden mit69 bekannten
Fixture-DeprecationWarnings; Ruff/Dokumentstruktur/Diffprüfung bestanden.
Die separate strenge netCDF-Importwarnung bleibt ungelöst.

Nächster Schritt: einen neuen SLSQP-Versuch mit zusammengesetztem Startgate
vorab registrieren: unveränderte Nicht-Paar-FD-Grenze, unabhängig qualifizierte
Paarableitungen und erneuter vollständiger Start-Jacobian-Replay. Alle alten
Fehlerberichte aufbewahren; gleiche Physik, neue Suchpfade und unabhängige Abnahme.

## Aufbewahrte Vorbereitung

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
