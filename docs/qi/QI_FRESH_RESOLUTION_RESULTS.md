# Frische QI-Auflösung: abgeschlossene Matrix und unabhängige Prüfung

## Ergebnis, 2026-09-12

Alle16 Kaltstarts sind vollständig gespeichert und erfüllen alle drei
Solverresiduen<=1e-12. Alle96 Feldgitter wurden ausgewertet und unabhängig
arithmetisch geprüft. Die feinere Solver-Winkelauflösung beseitigt die hier
geprüfte Clebsch-Inkonsistenz: alle48 zugehörigen Auswertungsgitter bestehen1e-3.
Das ist **keine Gesamtfreigabe**: nur9/16 Zellen bestehen die vorab verlangte
64/128-Auswertungsverfeinerung, nur2/16 den Vergleich mit historischen Feldern.
Keine Zelle besteht gleichzeitig alle drei Schirme. Alte19/24 bleiben unverändert.

Maximaler normierter poloidaler Identitätsfehler je Zelle, über drei Radien und
beide Auswertungsgitter; die Spalten sind die vier vorab festgelegten Kaltstarts:

| Autorenfall |201/Winkel1|401/Winkel1|201/Winkel2|401/Winkel2|
| --- | ---: | ---: | ---: | ---: |
| nfp2 Vakuum |1,0528e-3|1,0476e-3|2,0766e-6|5,0631e-7|
| nfp2 beta2 |8,7761e-4|8,7341e-4|2,5841e-6|6,4296e-7|
| nfp3 Vakuum |5,7857e-4|5,6275e-4|7,0162e-7|3,4625e-7|
| nfp3 beta2 |4,7818e-4|7,5133e-4|1,1414e-6|1,1510e-6|

Die Winkelverdopplung senkt diese Restgröße in jedem gepaarten Vergleich stark.
Radialverdopplung allein tut das nicht durchgehend: insbesondere nfp3 beta2
wird nicht monoton besser. Das unterstützt einen Einfluss der numerischen
Winkelauflösung, nicht eine vollständige Erklärung historischer VMEC9.0-Ausgaben.
Die geometrische mpol/ntor-Basis wurde nicht verfeinert.

92/96 Gitter bestehen sämtliche vier physikalischen Identitäten und beide
Negativkontrollen. Die vier Fehler liegen bei nfp2 Vakuum/Winkel1/s=0,75 auf
beiden Radial- und Auswertungsgittern. Alle gemeinsamen64/128-Punktwerte stimmen
exakt überein; sieben Winkel1-Zellen verfehlen jedoch die vorab festgelegte
1e-5-Grenze für die Änderung der *maximalen Fehlergröße* (bis3,5817e-5).
Das Berichtsflag `all_arithmetic_screens_pass=false` umfasst diesen
Auswertungs-Auflösungsschirm; es bedeutet hier keinen festgestellten Rechenfehler
des Auswerters. Der Treiber-Exit2 bleibt als reguläres negatives Ergebnis erhalten.

Nur die beiden nfp2-Vakuum/Winkel1-Zellen bestehen den gesamten1e-3-
Fidelitätsschirm gegen die historische Datei. Die größte Abweichung liegt bei
nfp3 beta2/201/Winkel1:8,3978% im normierten Vergleich der poloidalen
Ortsableitung,1,2497% bei |B|,0,8625% bei R/Z und0,0011596 absolut bei iota.
Das sind Vergleiche an gleichen VMEC-Koordinaten, keine koordinatenunabhängige
Abstandsmetrik zwischen Plasmaoberflächen. Bei Winkel2/401 bleibt für diesen
Fall die Tangentenabweichung4,0892% und die |B|-Abweichung0,6013%.
Das Volumen stimmt überall innerhalb6,114e-12 relativ überein; das allein
belegt weder die innere Feldgeometrie noch das richtige Druckgleichgewicht.

## Gegenprüfung und Evidenz

- Alle24 alten16/32-Gitter durch den neuen Matrixrechner reproduziert,
  maximale normierte Abweichung3,852e-15.
- Separater alter Schleifen-Fourierrechner:12 historische und48 neue
  Wout/Radius-Kombinationen bei32x32 gemeinsamen Punkten; maximale neue
  Abweichung9,076e-15. Vollständige64/128-Arrays separat arithmetisch geprüft.
- Autoren-Namelist, erlaubte numerische Änderungen, Randkoeffizienten,
  Fluss, Dimensionen, Solverresiduen, Volumen, Negativkontrollen, Verfeinerungs-
  und Fidelitätsklassifikation unabhängig bestätigt; Audit `all_pass=true`.
  Beide Feldrechner lesen dieselben Wouts: kein zweiter Gleichgewichtssolver.
- Solverlauf bei dd8b15a, Auswertung/Audit bei2a9e5b6; wiederverwendete
  Quellen und installierte Solverdateien explizit hashgebunden. Keine Änderung
  der beiden Umgebungen. Rohdateien zusammen409314445 Bytes, Reserve blieb
  über2GiB; keine parallele schwere Rechnung oder Installation.
- Abschlusskontrollen:19 QI-Tests bestanden,49 bekannte Fixture-
  DeprecationWarnings; Ruff, Dokumentstruktur und Diffprüfung bestanden.

Berichte: `evidence/qi-fresh-resolution-v1.json`,
`evidence/qi-fresh-resolution-v1-evaluation.json`,
`evidence/qi-fresh-resolution-v1-evaluation-audit.json` sowie ihre drei
Ressourcenwächter-Verzeichnisse. Rohdateien unter den gleichnamigen
Solver-/Auswertungsordnern in `artifacts/`. Keine Fehlerdatei überschrieben.

Nächster QI-Schritt: veränderte innere Gleichgewichte, radiale/Moden-Konvergenz
und Ausgabe-/Produzentenunterschiede getrennt eingrenzen; die feineren Felder
nicht ungeprüft an die Stelle der Autorenreferenz setzen. Absolute Drift,
vollständiger Invariantenbereich und QI-Zielgröße bleiben offen. Die geschlossene
Studie erlaubt jetzt die separat registrierte LPQA-SLSQP-Nachoptimierung.

## Aufbewahrte Vorbereitung und Zwischenstände

2026-09-12: [Protokoll](QI_FRESH_RESOLUTION_PROTOCOL.md) bei a369397 vor
neuen Gleichgewichten registriert. Die additive Ausführung hält alle16 Zellen,
Fehler/Timeouts und effektiven Eingaben getrennt fest. Die bekannte ursprüngliche
VMEC9.0-Quelle wird nicht durch neue VMEC++-Dateien ersetzt.

Neun reine Kontrollen bestehen: unveränderte physikalische JSON-Felder in
allen vier numerischen Varianten, Ablehnung unerlaubter Auflösung/Flussänderung,
unabhängige Namelist-m/n-Zuordnung und Ablehnung doppelter Moden. Der Root-
Treiber prüft die Autoren-Namelists über f90nml gegen den VMEC++-Parser, bevor
ein Solver startet. Beide Umgebungen bleiben unverändert; neue Rohpfade und
vorher gespeicherte, gehashte Inputs sind obligatorisch. Laufende2GiB-Reserve
durch äußeren Wächter,1800s-Zellgrenze im sequenziellen Treiber.
Außerdem bestehen acht echte VMEC++-Parser-/Kontroll-Roundtrips für die vier
Varianten von nfp2 Vakuum/nfp3 beta2, ohne Solveraufruf.

Die Kaltstarts laufen bei dd8b15a. Die ersten fünf Zellen konvergieren laut
gespeicherten Solverberichten; das ist ein Zwischenstand, kein vollständiges
Matrixergebnis oder Konsistenznachweis. Fortlaufende Bilanz:
`evidence/qi-fresh-resolution-v1.json`, Log im zugehörigen `-driver`-Ordner.

Der neue Matrix-Fourier-/Radialinterpolations-Auswerter ist additiv implementiert.
Ein separater Auditor verwendet den alten Schleifen-Fourierrechner an32x32
gemeinsamen Punkten jedes neuen Wouts und prüft vollständige gespeicherte
64/128-Winkelgitter, Fehlerarithmetik, Quellen, Randform und Klassifikation.
17 relevante Tests bestehen,33 bekannte NumPy/netCDF-DeprecationWarnings in
Testdaten-Erzeugung bleiben sichtbar. Keine Warnungs-/ABI-Freiheit behauptet.
Nächster Schritt: alle16 Kaltstarts schließen, neue Wouts separat auswerten/auditieren.

Vor physikalischer Feldauswertung nochmals vollständige Regression:
523 Tests bestanden,53 bekannte DeprecationWarnings, Ruff/Dokumentprüfung bestanden.
Auch wiederverwendete alte Feld-/Interpolationskerne werden im neuen Bericht
explizit hashgebunden, nicht nur durch den aktuellen Git-Stand implizit festgehalten.
Eine weitere Eingabesicherung lehnt doppelte und nichtganzzahlige geometrische/
Nyquist-Moden ab, bevor Matrixfelder entstehen. Beide zusätzlichen Mutations-
kontrollen bestehen; Grenzwerte und echte Felddaten wurden dafür nicht angepasst.
