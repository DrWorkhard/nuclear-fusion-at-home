# Diagnose der Clebsch-Restfehler ohne nachträgliche Grenzänderung

Vor neuer Feldrechnung registriert, 2026-09-12. Alle24 Gitter des abgeschlossenen
[Normierungstests](QI_CLEBSCH_RESULTS.md) und deren Wout-Hashes unverändert verwenden.
Keine Auswahl nur der fünf fehlgeschlagenen Gitter. Originalberichte bleiben negativ.

Für jeden Radius die beiden einschließenden VMEC-Halbgitterflächen aus ns und
die lineare Gewichtung t ermitteln. In allen vier Dateien ist ns201; die Auswahl
erfolgt aus dem tatsächlichen Gitter, nicht durch Rundung eines Radialindex.
Auf beiden Halbflächen `g, B^theta, B^phi, lambda_theta, lambda_phi, iota`
aus den jeweiligen gespeicherten Fourierkoeffizienten berechnen. Neuer
Matrix-Fourierauswerter als Gegenweg zum alten komponentenweisen Tracer; alle
48 Endpunktgitter und ihre Quellen speichern.

## Vorab festgelegte Produktzerlegung

Für jede Komponente `R = g*b - psi_a*h`, mit `h_theta=iota-lambda_phi`,
`h_phi=1+lambda_theta`, gilt bei linearer Interpolation:

`R_interpoliert = (1-t)*R_links + t*R_rechts - t*(1-t)*(g_rechts-g_links)*(b_rechts-b_links)`.

Eigene algebraische Identität, keine externe physikalische Näherungsformel.
Zuerst analytische Zufalls-/Nullgradient-/Gewichtskontrollen. Die linear kombinierten
Punktwerte müssen die archivierten alten Werte bis normiert1e-12 reproduzieren;
Normierung max(1,max|Referenz|). Residuenzerlegung muss bis1e-12 relativ zur
alten physikalischen Norm (mindestens|psi_a|) stimmen. Alle Rohterme speichern.
Beide einzelnen Halbflächen separat an der unveränderten1e-3-Identitätsgrenze
bewerten. Normen von Beiträgen dürfen wegen möglicher Auslöschung nicht als
additive Prozentanteile interpretiert werden.

Unabhängiger Auditor rechnet aus den gespeicherten Arrays mit direkter
Punktinterpolation und Produktbildung erneut; alle Fehler-/Pass-Flags prüfen.
Ein negatives Halbflächenresultat widerlegt eine Erklärung allein durch radiale
Produktinterpolation. Kleine Zerlegungsfehler beweisen nur die arithmetische
Ursachentrennung. Spektraltrunkierung, andere VMEC-Ausgabekonventionen und radiale
Geometrieableitungen bleiben ggf. weitere Hypothesen. Keine absolute Driftfreigabe,
keine neuen Gleichgewichte und keine Änderung des laufenden Spulenversuchs.
Mindestens2GiB Reserve, kleine Diagnose ohne schwere parallele Suche/Installation.
