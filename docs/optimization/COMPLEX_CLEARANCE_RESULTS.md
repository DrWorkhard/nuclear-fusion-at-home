# Unabhängige Abstand-Ableitungen bestätigt — 2026-09-11

Protokoll und Implementierung c1ca108, danach Auswertung beider eingefrorenen
Zustände. Evidenz: `evidence/complex-clearance-qualification-v1.json`.
Der vorherige vollständige Finite-Differenzen-Test bleibt fehlgeschlagen.

Die neue Wertberechnung rekonstruiert alle 16 Fourier-Kurven unabhängig und
verwendet weder native Positionen noch native Geometrie-Ableitungen. Reelle Werte
aller 120 glatten Paarabstandsbedingungen stimmen bis zu normiert 6.44e-15 mit
den gespeicherten Werten überein. Die zugehörigen Stromspalten sind exakt null.

Für zwei feste Richtungen je Zustand und alle Schritte h=1e-12,1e-20,1e-28:

| Zustand | Größte normierte Abweichung zur analytischen Richtungsableitung | Größte Abweichung zwischen Schrittweiten |
| --- | ---: | ---: |
| Ursprünglicher Start | 2.402e-12 | 1.166e-14 |
| Ausgewählter SLSQP-Kandidat 119 | 4.459e-13 | 4.997e-15 |

Alle vorab festgelegten Grenzen (1e-9 für Ableitungen, 1e-10 für Stabilität)
werden eingehalten. Jede einzelne Zeile und Schrittweite ist gespeichert.
Das sind Richtungsprüfungen an zwei festen Zuständen, keine globale Aussage über
alle denkbaren Entwürfe oder die gesamte nichtlineare Ingenieurphysik.

Die frühere 1.207e-6-Abweichung beim realen 1e-8-Schritt ist somit kein belastbarer
Hinweis auf eine falsche analytische Abstand-Ableitung. Die unabhängige Rechnung
und Schrittweitenstabilität stützen die Erklärung durch Rundungsauslöschung.
Beim Kernkontrollfall zeigt eine getrennte Differenzenfolge außerdem den erwarteten
quadratischen Abschneidefehler bei größeren Schritten und steiler Glättung.

Die 18 Nicht-Paar-Zeilen des alten Seed-47-Tests bestehen unverändert mit maximal
4.167e-7. Damit ist der vorher festgelegte zusammengesetzte Prüfweg möglich:
unveränderte Differenzengrenze für diese Zeilen, unabhängige komplexe-Schritt-
Qualifikation für alle Paarzeilen. Nur ein neu benannter Diagnoselauf darf darauf
aufbauen; kein Umschreiben oder Umdeklarieren der fehlgeschlagenen v1-Evidenz.

Aufwand: 14 Paarwert-Auswertungen, 67.2 Millionen quadratische Distanzstichproben,
keine nativen Geometrie-Ableitungsaufrufe. Koeffizienten, Richtungen und Anker sind
als gehashte Arrays gespeichert, sodass der reine Kern separat reproduzierbar ist.
