# Begrenzte lokale Proben: lineares Modell überschätzt große Schritte

Datum 2026-09-11. Ursprüngliches Protokoll d0f0b8d, vorher festgelegter
zusammengesetzter Prüfweg c1ca108, Umsetzung f151b80. Evidenz:
`evidence/direct-descent-diagnostic-v2-composite.json`.

Der ursprüngliche vollständige Differenzentest bleibt explizit **falsch**.
Die unveränderten Nicht-Paar-Zeilen und unabhängig komplex geprüften Paarzeilen
bestehen den getrennten Prüfweg. Alle früheren Zustände, Vektoren und Jacobians
werden in derselben physikalischen Basis gegengeprüft. Sechs adversariale Tests
verhindern, dass allein eine grüne Berichtszusammenfassung diesen Prüfweg freigibt.

## Lineares Modell gegen tatsächlich ausgewertetes Feld

Alle Änderungen beziehen sich auf das Suchziel f=Roh-Flux/1e-6, nicht unmittelbar
auf Kraftwerksleistung oder physikalische Zulässigkeit. Die physikalische
Parameteränderung ist 0.01*p mit |p_i|<=rho.

| Zustand | rho | Lineare Vorhersage Delta f | Tatsächliches Delta f | Kleinste nichtlineare Bedingung g |
| --- | ---: | ---: | ---: | ---: |
| Ursprünglicher Start | 1e-4 | Lineares Modell unzulässig | Nicht ausgewertet | — |
| Ursprünglicher Start | 1e-3 | Lineares Modell unzulässig | Nicht ausgewertet | — |
| Ursprünglicher Start | 1e-2 | -0.0761563 | +1.74083 | -3.779e-5 |
| Ausgewählter Punkt 119 | 1e-4 | -0.000395667 | -0.0000700683 | -3.149e-10 |
| Ausgewählter Punkt 119 | 1e-3 | -0.00441029 | +0.0337823 | -3.228e-8 |
| Ausgewählter Punkt 119 | 1e-2 | -0.0443755 | +3.87126 | -3.325e-6 |

Alle vier erfolgreichen linearen Lösungen bestehen die unabhängige primale
Prüfung. Zwei kleine Modelle am ursprünglichen, leicht unzulässigen Start sind
innerhalb ihrer Schrittbox unzulässig; das ist kein Stationaritätsbeweis.

Die kleinste ausgewertete Änderung am ausgewählten Punkt reduziert den Flux
leicht und bleibt innerhalb des internen 1e-8-Auswahlschirms. Die beiden größeren
Schritte zeigen dagegen starke positive Krümmung des Feldziels und verlieren
nichtlineare Zulässigkeit. Keine dieser Probes ersetzt den vorher ausgewählten
Kandidaten; es wurde kein hochauflösender Kandidaten-Holdout auf ihnen ausgeführt.

## Folgerung

Ein rein lineares Abstiegsmodell ist selbst bei geometrisch kleinen Änderungen
hier keine zuverlässige Vorhersage des Fluxziels. Das beweist keine allgemeine
Schwäche von SLSQP, das selbst Krümmungsinformationen iterativ approximiert.
Vor einer neuen Optimierung: das natürliche quadratische Modell des räumlichen
Feldfehlers auf allen bereits eingefrorenen Probes prüfen. Diese Untersuchung
ist keine Aussage über globales Optimum, SoTA oder eine zulässige Baseline.
