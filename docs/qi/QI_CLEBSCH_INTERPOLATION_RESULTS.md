# Clebsch-Produktinterpolation erklärt die Restfehler nicht

2026-09-12: [Diagnoseprotokoll](QI_CLEBSCH_INTERPOLATION_PROTOCOL.md) registriert.
Auswertung und unabhängiger Audit abgeschlossen. Alle24 alten Gitter werden erhalten; beide angrenzenden
Halbflächen und der reine Produktinterpolationsbeitrag werden getrennt geprüft.
Die ursprünglichen fünf poloidalen Fehler bleiben bestehen.

Matrix-Fourierauswerter, Produktzerlegung und separater Punktinterpolationsauditor
sind vorbereitet. Zehn reine Produkt-/Gewichtskontrollen und eine separate
Auditkontrolle bestehen; zusammen mit Clebsch-Feldkontrollen21 Tests bestanden.
Alte Tracer-/Feldkerne unverändert erhalten.

## Ergebnis und Gegenprüfung

Ausführung bei fbaec49. Alle24 ursprünglichen Gitter und48 angrenzenden
Halbflächengitter gerechnet. Bericht `evidence/qi-clebsch-interpolation-v1.json`,
separater Audit `evidence/qi-clebsch-interpolation-v1-audit.json`, Wächterbericht
im `-driver`-Verzeichnis; Arrays unter `artifacts/qi-clebsch-interpolation-v1/`.
Wächterexit0, kleinster beobachteter freier Platz6137118720Bytes.

Der neue Matrix-Fourierweg reproduziert die alten interpolierten Punktwerte mit
maximal4,8829e-15 normierter Abweichung. Residuenzerlegung stimmt bis4,5054e-15;
der separate Produkt-/Punktinterpolationsauditor bestätigt alle24 Rechnungen.
Das ist eine erfolgreiche Ursachentrennung, keine nachträgliche Feldfreigabe.

| Fall | Max. poloidaler Halbflächenrest | Max. reiner Produktterm | Abgelehnte Halbflächengitter |
| --- | --- | --- | --- |
| nfp2 Vakuum | 1,0315740e-3 | 2,0493855e-6 | 4/12 |
| nfp2 beta2 | 8,4230894e-4 | 2,5206772e-6 | 0/12 |
| nfp3 Vakuum | 6,1367543e-4 | 6,9212128e-7 | 0/12 |
| nfp3 beta2 | 1,6114275e-3 | 3,6134086e-6 | 6/12 |

Alle48 toroidalen Halbflächengitter bestehen die unveränderte1e-3-Grenze.
Bei den poloidalen Gleichungen fallen dagegen10/48 schon ohne radiale
Interpolation durch. Die reinen Produktterme sind viel kleiner als diese
Restabweichungen. **Radiale Produktinterpolation allein ist damit als Ursache
ausgeschlossen.** Keine additive Prozentzerlegung von Maximalnormen behauptet.

Offen sind insbesondere die spektrale Trunkierung der Wout-Feldkomponenten und
deren genaue Ausgabekonventionen. Dafür zunächst Quellcode und Modengrenzen
prüfen, anschließend ggf. einen getrennten Spektraltest vorab festlegen. Der
ursprüngliche19/24-Normierungstest bleibt negativ; absolute Drift, geometrischer
Radial-Jacobian und globale QI-Bewertung sind weiterhin unqualifiziert.
