# Direkter SLSQP-Konstruktionspilot — 2026-09-11

Vorab festgelegtes Protokoll und Suchimplementierung: 3eda449. Unabhängige
Auswahl-/Budgetprüfung und zusätzliche native Holdout-Implementierung: 062f3d8.
Eingefrorene Suchergebnisse und Audit: ccf8015. Kein Kandidaten-Holdout wurde
in einen dieser Läufe zurückgespielt.

## Suchverlauf und festgelegte Auswahl

Beide Wiederholungen verbrauchen exakt 256 vollständige Werte-/Jacobian-Bundles,
einschließlich neun Richtungsproben. Je 715 Anforderungen: 458 exakte Cachetreffer,
256 Auswertungen und eine Budgetverweigerung, kein fehlgeschlagenes Bundle.
Alle Vorschlags-Hashes, Werte, Auswahlkriterien und logischen Arbeitszähler sind
identisch. Laufzeiten 130,04 / 133,58 s sind dokumentiert, aber kein kontrollierter
Zeitvergleich gegen die anders formulierten früheren Experimente.

Kein Vorschlag erreicht den internen Auswahlschirm v<=1e-8. Daher gewinnt gemäß
Protokoll der geringste maximale Verstoß und erst danach der Fluxwert:
Vorschlag 119, v=3.404441634e-6, Roh-Flux 2.330933800e-7 auf dem Suchgitter.
Nur die interne Längengrenze ist dort verletzt. Beide gespeicherten Felder sind
byte-identisch. Das Audit berechnet Auswahl und Parameteridentität unabhängig nach.

Am letzten Vorschlag ist der Suchgitter-Flux zwar kleiner (1.406656905e-7), der
maximale Verstoß aber größer (3.864038810e-5). Dieser Vorschlag ist nach der
vorher festgelegten Regel nicht ausgewählt und hat keinen eigenständigen
Feld-Holdout. Der Lauf endet am Budget, nicht mit nachgewiesener Konvergenz.
Die Auswahl wird nicht nachträglich angepasst, um den kleineren Flux vorzuzeigen.

## Unabhängiger Holdout beider ausgewählter Felder

Die Zahlen stimmen zwischen beiden Wiederholungen überein.

| Größe | Ergebnis | Feste Akzeptanz | Urteil |
| --- | ---: | ---: | --- |
| Roh-Flux, 128x128 Oberfläche / 800 Spulenpunkte | 2.330822133e-7 | <=1e-8 | Nicht bestanden; Faktor 23,308 |
| Gesamtlänge der vier eindeutigen Spulen, Reaktorskala | 219.900748637 m | <=220 m | Bestanden |
| Kontinuierliche Krümmungsobergrenze | 0.976993064 /m | <=1 /m | Bestanden |
| Kontinuierliche Spulenabstandsuntergrenze | 1.090413138 m | >=1.06 m | Bestanden |
| Feinster Spule/Plasma-Abstand, Stichprobe | 3.167567124 m | >=1.3 m | Bestanden |
| Höchste native MSC, finale Auflösung | 7.038896584 | <=10.100286075 | Bestanden |
| Höchste native Bogenlängenvarianz, finale Auflösung | 3.252397878 | <=102.015778794 | Bestanden |
| Native Linking Number bei 200 und 800 Punkten | 0 / 0 | jeweils 0 | Bestanden |

Flux-Oberflächen-/Spulenverfeinerung und native Metrikverfeinerung bestehen.
MSC und Varianz wurden bei 200, 800 und 3200 Punkten geprüft. Die kontinuierliche
Krümmung ist bei N=200 zunächst unaufgelöst, ab N=400 bestanden; alle Ebenen sind
erhalten. Die kontinuierlichen Schranken benutzen Gleitkommapolster, keine
gerichtete Rundung. Das sind keine Zertifikate für vollständige Wicklungspakete,
Selbstüberschneidung, nichtlineare Mechanik oder Teilchentransport.

## Bewertung und Folgearbeit

Diese neue Konstruktion bringt einen geringeren Fehler mit brauchbaren
Geometriemargen, aber weiterhin keine zulässige Baseline. Sie verändert die
Zielformulierung und Auswahlregel: kein isolierter Algorithmusvergleich und
keine allgemeine SLSQP-Überlegenheit gegenüber TRF. G2 bleibt offen.

Vor einer größeren Fortsetzung sind Suchkonvergenz und aktive Randbedingungen
zu diagnostizieren. Ein abgebrochener SLSQP-Lauf darf nicht als lokales Optimum
gedeutet werden. Der heutige Stand ist kein SoTA-Fortschritt und keine
SQuID-C-Bereitschaft.

Evidenz: `evidence/direct-slsqp-pilot-v1/`,
`evidence/direct-slsqp-pilot-v1-audit.json`,
`evidence/direct-slsqp-pilot-v1-holdout.json`,
`evidence/direct-slsqp-pilot-v1-curvature.json`,
`evidence/direct-slsqp-pilot-v1-clearance.json`,
`evidence/direct-slsqp-pilot-v1-native.json`.
