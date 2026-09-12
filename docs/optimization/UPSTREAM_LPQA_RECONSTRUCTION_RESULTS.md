# Fünf LPQA-Archivfelder korrekt rekonstruiert, alle an Roh-Fluxgrenze abgelehnt

Stand 2026-09-12. [Vorabfestlegung](UPSTREAM_LPQA_RECONSTRUCTION_PROTOCOL.md),
Ausführung bei `aa8741d`, erst nach abgeschlossenem committetem Jacobi-Versuch.
Alle fünf vorab ausgewählten Felder unverändert verwendet; keine neue Auswahl,
keine Optimierung und keine Anpassung ihrer Ströme oder Geometrie.

## Ergebnis und Gegenprüfung

Für alle fünf stimmen die vier Fourier-Koeffizientensätze, sämtliche16 Ströme
und die Basisregularisierungen mit einer unabhängigen direkten JSON-Auswertung
überein. Der neue200-Punkte-Quadraturklon reproduziert alle16 Originalkurven
an257 Parametern exakt; Ströme bleiben exakt. Alle64 Kontrollpunktfelder auf
beiden200/800-Quadraturen stimmen zwischen nativer und direkter unabhängiger
Fourier-/Biot-Savart-Summe überein: maximale normierte Abweichung
5,533820417961848e-16 bei fester1e-12-Grenze.

Die vollständigen vier feinen Fluxgitter und alle festgelegten Geometrie-/
Plasmagitter sind ausgewertet. Alle geometrischen und Verfeinerungsschirme
bestehen; **alle fünf Felder scheitern ausschließlich am Roh-Fluxlimit1e-8**.
Die folgenden Längen/Krümmungen/Abstände sind Gitterwerte, keine neuen
kontinuierlichen oder vollständigen Ingenieurzertifikate.

| Vorab festgelegte Reihenfolge | Feinster Roh-Flux | Länge [m] | Maximale Krümmung [1/m] | Spulenabstand [m] |
| --- | --- | --- | --- | --- |
| 92598 | 9,999529352313868e-7 | 199,99891745 | 0,34688613 | 1,10192648 |
| 39220 | 9,999744163366487e-7 | 199,99959473 | 0,35416201 | 1,14876117 |
| 68534 | 9,999578302063890e-7 | 200,00005246 | 0,34331254 | 1,15971525 |
| 46837 | 9,999590680858370e-7 | 199,99898620 | 0,33959286 | 1,13364054 |
| 52359 | 9,999661562286623e-7 | 199,99945243 | 0,33586955 | 1,11611916 |

Spulen-Plasma-Abstände2,79595–3,07630m. Die Roh-Fluxwerte liegen knapp unter
der jeweils gemeldeten1e-6-Abschaltschwelle, aber99,995–99,997-mal über unserer
1e-8-Abnahme. Die alten Nullmeldungen dürfen deshalb nicht als gelöste
Magnetfeldaufgabe übernommen werden. Dies ist keine Aussage, dass sämtliche
5301 Archiveinträge unzulässig wären: tatsächlich berechnet wurden nur diese fünf.

## Korrektur zur Vergleichbarkeit der Feldstärke

Unsere feinen Oberflächenmittel von |B| betragen0,94606157–0,94606783T, nicht
die alten gemeldeten Werte um1,0963T. Die frühere Inventareinordnung dieser
Meldungen als mit unserem Oberflächenmittel vergleichbare Feldstärke war zu
weitgehend. Unterschiedliche Messorte/-definitionen müssen getrennt bleiben;
aus den alten Meldungen folgt kein rund16%iger physikalischer Feldstärkeunterschied.
Die aktuelle StellCoilBench-Auswertung kennt insbesondere eine Messung auf dem
großen Radius. Die exakte historische Produzentenrevision `50ec27637` ist im
lokalen SIMSOPT-Checkout nicht auflösbar; sie wurde nicht nachgeladen oder
rückwirkend als reproduziert bezeichnet. Die abweichende Stromsumme bleibt
unverändert1249999,2463040038A gegenüber1250075,624635464A im bisherigen Start.

## Audit, Aufwand und Grenzen

- `evidence/upstream-lpqa-reconstruction-v1.json`: fünf vollständige Ergebnisse,
  Quell-/Ableitungs-/Arrayhashes und alle Auswerteauflösungen.
- `evidence/upstream-lpqa-reconstruction-v1-driver/`: Befehl, Log, Exit0 und
  überwachte minimale freie Kapazität6209859584Bytes >2GiB. Exit0 bedeutet
  vollständige Prüfung, ausdrücklich keine bestandene physikalische Abnahme.
- `evidence/upstream-lpqa-reconstruction-v1-audit.json`: unabhängige Prüfung
  unveränderter serialisierter Parameter, erneute komponentenweise Feldsummen
  aus gespeicherten Quadraturen, Gittervollständigkeit und Abnahmearithmetik;
  alle fünf bestehen jeweils acht Prüfungen. Größte native Feldabweichung der
  zweiten Summationsimplementierung1,0488523176472411e-15, weiterhin unter1e-12.
  Keine erneute feine Geometrieberechnung im Audit.
- 30 neue native Feldgitter und10 unabhängige NumPy-Feldgitter; der Endaudit
  berechnet zusätzlich10 Feldgitter aus gespeicherten Quadraturdaten, ohne neue
  native Feldaufrufe. Sämtliche Quellfelder und Roharrays bleiben erhalten.

Dieser statische Versuch ist vollständig geschlossen; kein Kandidat erreicht
die Schwelle für weitergehende kontinuierliche/native Designfreigabe. Er
qualifiziert mögliche Ausgangsdaten, nicht eine neue zulässige Baseline oder
einen fairen Methodenvergleich. Der erste, bereits vor jeder Feldrechnung
ausgewählte Archiveintrag ist ein möglicher getrennt zu registrierender
Konstruktionsstart; keine nachträgliche Auswahl anhand dieser feinen Ergebnisse.
Langfristige Schritte1 und2 bleiben offen.
