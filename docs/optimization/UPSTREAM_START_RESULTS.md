# Alternativer LPQA-Start: vollständig geprüft, Flux weiter unzulässig

2026-09-12: [Protokoll](UPSTREAM_START_PROTOCOL.md) vor neuer Rechnung festgelegt.
Der erste, vor den statischen Feldtests ausgewählte Archiveintrag wird auf die
bisherige feste Gesamtstromsumme abgebildet. Auswahl nicht anhand neuer feiner
Abstände/Fluxwerte verändern. Die neue Startqualifikation ist bestanden; noch
die neue Suche samt unabhängigem Audit ebenfalls abgeschlossen. Die ursprünglichen
fünf Quellen bleiben unzulässig; auch der neue grobe Flux überschreitet die Grenze.

Additive Vorbereitung, Feld-/Ableitungsqualifikation und separater arithmetischer
Auditor sind implementiert. Zehn reine Strom-/Serialisierungskontrollen und fünf
Kontrollen für vollständige/manipulierte Differenzenberichte bestehen. Die
native Feldrechnung ist inzwischen ausgeführt. Der Auditor rekonstruiert die
gemeinsame Stromskalierung, Quelle/Parameter, Feldskalierung und alle138
Richtungszeilen aus gespeicherten Arrays, ohne den nativen Auswerter aufzurufen.
Alte numerische Kerne bleiben unverändert; neue Quellhashes werden gebunden.

## Gemessene Startprüfung und Gegenprüfung

Ausführung bei e4c576f, Bericht
`evidence/upstream-start-qualification-v1.json`, separater Audit
`evidence/upstream-start-qualification-v1-audit.json`, Ressourcenbericht im
gleichnamigen `-driver`-Verzeichnis; Roharrays unter
`artifacts/upstream-start-qualification-v1/`. Keine Optimierung.

- Gemeinsamer Stromfaktor1,0000611027020105, feste Summe1250075,624635464A.
  Alle16 Ströme passen bis1,4220e-16 normierter Abweichung; Fourierkoeffizienten
  und Regulierungen exakt erhalten. Neue serialisierte/nativ benannte Zustände gleich.
- Feldskalierung an64 festen Punkten: Fehler4,487194411460773e-16, Grenze1e-12.
- Neun komplette Feld-/Jacobi-Bundles: maximale gekoppelte Gradientabweichung
  2,0519696100526215e-13. Zusätzlicher nativer Roh-Flux-Gradientvergleich
  7,3508e-12, Grenze1e-10. Alle unabhängigen geometrischen Metriken bestehen.
- Richtungsfehler bei1e-5/1e-6/1e-7/1e-8:
  9,7050e-6 /9,7559e-8 /4,3371e-8 /4,3514e-7.
  Letzter Wert besteht die vorab feste1e-6-Grenze; alle138 Zeilen behalten.
  Nicht monoton bei den kleinsten Schritten, konsistent mit Rundungseinfluss,
  aber keine zusätzliche Ursachenqualifikation oder Toleranzänderung.
- Separater Auditor bestätigt23 Quellen-/Parameter-/Feld-/Ableitungsprüfungen;
  keine zusätzlichen physikalischen Aufrufe. Native Arbeit zusätzlich ausdrücklich
  gezählt: Skalierungsfeld, Roh-Flux J/dJ,120 Paarminima, Plasmaabstand, Linking.

Der grobe Roh-Flux ist1,0001222082961255e-6: **keine Zulässigkeit**. Diese Prüfung
qualifiziert den explizit transformierten Start, nicht einen Entwurfsfortschritt.
Nächster Schritt: registrierten klassischen1033-Bundle-Versuch ausführen, beide
Pfade unabhängig auditieren und ausgewählte Felder vollständig fein prüfen.
Der additive Studienrunner und sein unabhängiger Auditor sind vorbereitet:
`scripts/run_upstream_start.py`, `scripts/audit_upstream_study.py`. Sie binden
die abgeschlossene Startprüfung und prüfen erste Parametervektoren explizit;
das eigentliche Suchverfahren bleibt der unveränderte alte Armkern. Die gesamte
Suite besteht mit469 Tests/20 bekannten Warnungen; Ruff/Dokumentprüfung bestehen.

## Vollständiger klassischer Suchversuch

Gestartet bei3f88576, `evidence/upstream-start-study-v1/summary.json`, separate
Arithmetik-/Profilprüfung `evidence/upstream-start-study-v1-audit.json`,
Ressourcenbericht im `-driver`-Verzeichnis. Beide1033-Bundle-Pfade exakt gleich,
auch Auswahl, Stufen, Zähler und native Arbeit. Je1898 Anforderungen/865 Cachetreffer,
keine fehlgeschlagene oder global abgewiesene Auswertung; acht feste Stufenbudgets.

Ausgewählt wird jeweils Bundle1033, grober Roh-Flux8,95478252250164e-8,
interne Ungleichungsverletzung0. Der unabhängige Audit besteht29 Prüfungen pro
Arm und11 Profil-/Kontrollprüfungen. Gekoppelte Gradientabweichung maximal
5,1288e-13. Serialisierte Endfelder und Parameterarchive jeweils bytegleich:
Feldhash `6ee2a013254b2f30195291dfd4d13c6a166d06d5286cb966db92a2646db2fb5f`,
Arrayhash `31dab61fb28d060c9e9f6c21905396cc469dad738c6931928dfe39fa4e250d14`.

Wächterminimum6096891904Bytes. Laufzeiten798,895/865,760s sind keine kontrollierte
Laufzeitstudie; kleine QI-Diagnosen/Tests liefen daneben, keine schwere Suche oder
Installation. Kein Konvergenz- oder Zulässigkeitsnachweis. Jetzt alle vier feinen
Abnahmephasen für beide ausgewählten Felder sind inzwischen abgeschlossen, ohne Suchfeedback.

## Unveränderte feine Abnahme

Bei121dbaa abgeschlossen, Berichte unter
`evidence/upstream-start-study-v1-validation/`. Alle vier Phasen vollständig,
Exitcodes2/0/0/0: reguläre Fluxablehnung, kontinuierliche Geometrie und native
Zusatzprüfungen bestehen. Beide ausgewählten Felder liefern identische Zahlen:

| Größe | Feines Ergebnis | Feste Grenze |
| --- | --- | --- |
| Roh-Quadratic-Flux | 8,955120977790992e-8 | <=1e-8: abgelehnt |
| Oberflächenmittel von Betrag B | 0,9461249614024069T | Diagnose, keine neue Schwelle |
| Gesamtlänge der vier Basisspulen | 219,89799235560042m | <=220m |
| Kontinuierliche Krümmungsobergrenze | 0,8552868623641945/m | <=1/m |
| Kontinuierliche Spulenabstandsuntergrenze | 1,0824041113058178m | >=1,06m |
| Feinster Plasmaabstand | 3,1076995201531807m | >=1,3m; Gittertest |

Alle Krümmungsstufen200 bis12800 bestehen diesmal. Die Krümmungsdatei enthält
auch die unveränderte Quelle; für Kandidatenzahlen ausschließlich `direct-r1/r2`
und ihre konkreten Feldhashes verwenden, nicht den ersten Quelleneintrag.
Native maximale MSC6,74727 und Bogenlängenvarianz2,24392, alle Metrik-/Linking-
und Verfeinerungstests bestanden. Wächterminimum6101098496Bytes.

Der Flux ist rund2,67-fach kleiner als beim gleichen AL-Verfahren am früheren
Start, bei praktisch gleicher mittlerer Feldstärke. Das ist ein Startvergleich,
kein isolierter Methodenfortschritt. Länge/Abstände sind nicht sämtlich besser:
keine behauptete Pareto-Dominanz. Noch Faktor8,955 über der Zulässigkeitsgrenze;
kein Konvergenznachweis, keine allgemeine Methodenrangfolge oder Ingenieurfreigabe.
Dieser registrierte Versuch ist vollständig geschlossen. Eine neue Konstruktion
braucht ein neues vorab festgelegtes Problem-/Solver-/Budgetprotokoll; ursprüngliche
Grenzen und alle negativen Ergebnisse bleiben erhalten.
