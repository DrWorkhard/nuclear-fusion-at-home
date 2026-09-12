# Quadratisches Feldmodell an eingefrorenen Testschritten — 2026-09-12

Vorabfestlegung vor jeder neuen physikalischen Auswertung. Keine Optimierung,
keine Änderung der bereits gespeicherten vier nichtlinearen Testschritte aus
`evidence/direct-descent-diagnostic-v2-composite.json`, keine Kandidatenzulassung.

## Frage und Modell

Erklärt das natürliche Gauss-Newton-Modell des räumlichen Feldfehlers die starke
Abweichung der linearen Fluxvorhersage? Für den unveränderten diskreten Fehler z,
seine Jacobimatrix D und s=1e-6 gilt:

    f(x) = z.T z / (2s)
    grad f = D.T z / s
    q(delta) = ||z + D delta||² / (2s)
    H_GN = D.T D / s

H_GN ist positiv semidefinit, aber bei nichtlinearem z nicht die vollständige
Hessematrix. Der ausgelassene Rest wird explizit gemessen. Für
e=z(x+delta)-(z+D delta) gilt exakt:

    f(x+delta) - q(delta) = ((z+D delta).T e + e.T e/2) / s.

## Feste Daten und Qualifikation

- Originalzustand und ausgewählter SLSQP-Punkt 119; unveränderte 207 benannte
  freie Parameter, 16 physikalische Spulen, Feldgitter 32x32, Spulenquadratur 200.
- Alle Eingangsberichte und Roharrays gehasht; gespeicherte Laufzeitreihenfolge
  über die ursprüngliche physikalische Namensbasis in die neue Reihenfolge abbilden.
  Originalzustand und serialisiertes Kandidatenfeld müssen exakt übereinstimmen.
- Alle 138 Werte und ihre Jacobimatrix gegen den gespeicherten Diagnosezustand
  wiederholen: komponentenweise |neu-alt|/max(1,|alt|) <=1e-10.
- An beiden Zuständen die gebündelte räumliche Matrix erneut gegen jede Zeile
  einer nativen Einzelpunkt-VJP prüfen, normiert mit max(1,max|Referenz|): <=1e-10.
  z gegen native Feldprojektion <=1e-10; relativer Fluxfehler <=1e-10; skalierter
  Fluxgradient gegen den direkten Backendgradienten <=1e-10. Feldpunkte unverändert.
- Zwei neue festgelegte Richtungen (Seeds 49, 50) in der ursprünglichen
  Parameterbasis, zentrale Differenzen mit h=1e-4,1e-5,1e-6; alle Stufen behalten,
  maximale komponentenweise normierte Fehler der feinsten Stufe <=1e-6.
- Erst nach diesen Prüfungen alle vier früheren erfolgreichen LP-Testschritte
  wiederholen. Die zwei unzulässigen LPs bleiben ohne Testschritt. Keine Auswahl
  nach den neuen Modellfehlern, keine zusätzlichen Schrittweiten oder Richtungen.

## Auswertung und Entscheidung

Für jeden Testschritt alle 138 nichtlinearen Werte gegen das alte Array prüfen
(<=1e-10 wie oben), dann lineare Änderung, nichtnegativen GN-Krümmungsterm,
quadratische Änderung und tatsächlich gemessene Änderung angeben. Quadratisches
Modell durch direkte Norm und Matrixform gegenprüfen; Restidentität <=1e-10.

Die vorab festgelegte enge Nützlichkeitsprüfung besteht nur, wenn **alle vier**
quadratischen Vorhersagen das richtige Vorzeichen der tatsächlichen Änderung
haben und ihr absoluter Fehler höchstens 10% des jeweiligen linearen Fehlers
beträgt. Andernfalls das negative Ergebnis behalten. Diese Prüfung ist getrennt
von der Qualifikation der Implementierung: Ein korrekt berechnetes Modell kann
schlecht vorhersagen. Keine allgemeine Solverüberlegenheit folgt aus vier Proben.

Reine Kernkontrollen: exaktes affines Residuum, nichtlineares Residuum mit
unabhängiger Restidentität, fehlender Residual-Hessenanteil, Permutations- und
Skalenkonsistenz sowie Zurückweisung ungültiger/nichtendlicher Daten.

Versionen, Code-/Eingangshashes, Laufzeiten, native Komplettauswertungen,
gebündelte Spulenkontraktionen und zusätzliche Einzelpunkt-/Richtungsprüfungen
getrennt erfassen. Neue Rohdateien enthalten x, z, D und Referenzmatrix sowie
alle Testschrittresiduen; spätere Kern-Replays dürfen keine nativen Solver brauchen.

Bei bestandenem Modelltest einen neuen krümmungsinformierten Optimierungsversuch
getrennt planen und committen. Die alten Flux-/Geometriegrenzen bleiben unverändert.

## Herkunftskorrektur vor physikalischem Lauf

Der erste Start bei c81fdbd stoppt vor dem Aufbau: Zwei Skripte der historischen
gebündelten Qualifikation haben nach der dokumentierten Ordnerumstellung andere
Bytes. Keine Rohdateien oder physikalischen Auswertungen entstanden. Historische
Prüfskripte werden deshalb gegen ihren aufgezeichneten Git-Stand geprüft; alle
tatsächlich ausgeführten Kerne und das aktuelle qualifizierte Backend müssen
weiterhin gegen die aktuellen Bytes bestehen. Keine numerische Grenze ändert sich.
