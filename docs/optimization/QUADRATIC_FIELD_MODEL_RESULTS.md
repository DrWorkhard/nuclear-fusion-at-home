# Quadratisches Feldmodell erklärt die lokalen Vorhersagefehler

Datum: 2026-09-12. Protokoll c81fdbd, Herkunftskorrektur vor physikalischem Lauf
5eb5c7f. Evidenz `evidence/quadratic-field-model-v1.json`, separater Kern-Audit
`evidence/quadratic-field-model-v1-core-audit.json`.

## Ergebnis und Gegenprüfung

Alle vier vorab festgelegten Testschritte bestehen die enge Modellprüfung:
richtiges Änderungs-Vorzeichen und mindestens 99,907% kleinerer absoluter
Vorhersagefehler als beim linearen Modell (gefordert: mindestens 90%).
Werte beziehen sich auf f=Roh-Flux/1e-6, nicht auf Kraftwerksleistung.

| Zustand / Schrittbox rho | Tatsächliches Delta f | Quadratisches Delta f | Fehler quadratisch / linear |
| --- | ---: | ---: | ---: |
| Original / 1e-2 | +1,740829812 | +1,739140609 | 9,297e-4 |
| Punkt 119 / 1e-4 | -7,006834815e-5 | -7,006785424e-5 | 1,517e-6 |
| Punkt 119 / 1e-3 | +0,033782348 | +0,033783529 | 3,094e-5 |
| Punkt 119 / 1e-2 | +3,871258261 | +3,871385326 | 3,245e-5 |

Die gebündelten räumlichen Jacobimatrizen stimmen an beiden Zuständen mit jeder
nativen Einzelpunkt-VJP-Zeile überein (maximal normiert 8,882e-16). Zwei neue feste
Richtungen je Zustand bestehen alle feinsten Prüfungen (maximal 3,867e-11).
Alle 138 Werte/Jacobians und vier Testschrittvektoren werden erneut bestätigt.
Matrixform und explizite Restidentität stimmen bis 6,492e-16 überein.

Der unabhängige NumPy-Audit importiert die untersuchte Modellfunktion nicht:
Er verwendet gespeicherte native Referenzzeilen, skalare Normsummen und neue
Berechnung der Prüfentscheidungen. Alle 23 Kontrollen bestehen. Sechs
synthetische/adversariale Audit-Tests prüfen manipulierte Zahlen, Matrizen,
Schritte, Entscheidungsflags und fehlende Proben. Kein Vertrauen allein in
grüne Berichtszusammenfassungen. Der erste Lint-Lauf fand eine überlange Zeile;
sie wurde vor dem Audit korrigiert.

Aufwand: 7,115 Sekunden; sechs direkte Backendauswertungen, davon zwei mit
voller Ableitung, zusätzlich 32 gebündelte Spulenkontraktionen, 30 Feldgitter-
Anfragen und 2048 native Einzelpunkt-Feld-/VJP-Anfragen. Die Einzelpunktmatrix
benötigt jeweils rund 1,052 s, die gebündelte 0,336 bzw. 0,343 s. Dies ist kein
kontrollierter Zeitvergleich mit den älteren Optimierungsläufen.

## Schluss und Grenzen

Der positive Gauss-Newton-Krümmungsterm erklärt hier weitgehend, warum größere
linear prognostizierte Abstiege den tatsächlichen Flux erhöhen. Das rechtfertigt
einen getrennt vorab festgelegten klassischen Optimierungsversuch, der dieses
Modell ausdrücklich nutzt. Es beweist weder eine globale Solverüberlegenheit
noch, dass der bisherige SLSQP-Lauf ausschließlich aus diesem Grund scheitert.

H_GN ist weiterhin nicht die vollständige nichtlineare Hessematrix. Die Proben
sind keine zugelassenen Kandidaten; Grenzwerte und alte Fehlversuche bleiben
unverändert. Eine zulässige Baseline und die langfristigen Schritte 1/2 sind offen.
