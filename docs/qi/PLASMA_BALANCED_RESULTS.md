# Zwei Wirkungsdomänen: Schritt3-Abschluss und Bedienung

14. September2026. [Registriertes Folgeprotokoll](PLASMA_BALANCED_PROTOCOL.md).
**Schritt3 im registrierten QI-nahen Vakuumumfang abgeschlossen.** Der eigene
Goodman-nfp2-Randentwurf senkt die relative Bouncewirkungsvarianz auf dem feinsten
registrierten Raster um11,1700%; alle zehn Abschlussgates bestehen. Die erste
Form bleibt [unabhängig abgelehnt](PLASMA_OPTIMIZATION_RESULTS.md). Beide Domänen
und lokale Wirkungsgrenzen wurden im Folgeversuch schon bei der Konstruktion
berücksichtigt, keine physische Endgrenze gelockert. Dieser Bericht trennt die
Zwischenphasen von der abschließenden Zulassung unten.

## Vor Ausführung geprüfte Implementierung

Getrennte unveränderliche Phasenberichte für Archivauswertung, bedingte
Vorschlagssuche und Kaltendpunkte. Jeder native Solve verwendet unveränderten
alten Worker, Eingabemapper und Ressourcenwächter; zusätzliche breite Diagnostik
und Auswahl werden separat gespeichert. Keine alte numerische Datei geändert.
Der explizit markierte Diagnoseadapter nutzt den vorhandenen Vier-Zustands-
Auswerter, behauptet aber keinen alten Zwei-Poll-Suchlauf. Eigener Gesamtauditor
prüft tatsächliche Quellen, Phasenbedingungen und Auswahl vor physischen Gates.

Das gemeinsame lineare Vorschlagsmodell speichert alle zentralen Differenzen,
142 Nebenbedingungen, Bounds, primalen und dualen Zustand. Der unabhängige
Prüfweg rekonstruiert die Matrix und kontrolliert Zulässigkeit, Dualzeichen,
Stationarität, Komplementarität und Dualitätslücke; keine Gleichsetzung mit
physischer Optimalität. Negative oder unvollständige Daten können keinen
Zulassungspass erzeugen. Eine Archivform verhindert zusätzliche Differenzsolves,
wenn sie bereits die vorab festgelegten Auswahlbedingungen erfüllt.

19 neue Kontrollen beziehungsweise46 zusammen mit dem ersten Plasmalauf bestehen
in0,73s; vollständige Gesamtsuite766 Tests/144 bekannte Warnungen in54,05s.
Ruff besteht. Ein erster neuer Testlauf fand die Python-Tupel-/JSON-Listenform
der LP-Bounds; vor jeder neuen Rechnung vereinheitlicht. Die LP-Threadoption wird
von SciPy mit einem Weiterleitungswarnhinweis an HiGHS gegeben; Warntext wird im
Modellbericht gespeichert, nicht als physische Fehlermeldung oder Warnungsfreiheit
umgedeutet. Keine Installation, kein externer Quelleneingriff.

## Phase A: keine auswählbare Archivform

Bei8693339 alle16 vorhandenen Formen auf sämtlichen35 breiten Zellen gemessen,
ohne einen neuen Gleichgewichtssolve. Keine fehlenden Domänenzellen. Der separate
Audit bestätigt Quellen, alte native Datensätze, alle neuen Aktionen durch
Gaussquadratur, Zellstatistik, Konstruktionsklassifikation und Auswahl: kein Index
zulässig. Einzige Form mit beiden erforderlichen Kostenvorteilen ist Index10;
sie verletzt die lokale Mittelwirkungsgrenze. Kein Ausblenden dieser Grenze,
kein nachträgliches Absenken des Auswahlschirms.

Phase/Audit in `evidence/plasma-balanced-v1/archive.json` und `archive-audit.json`,
Rohtraces unter `artifacts/plasma-balanced-v1/archive`.46 gezielte Kontrollen
bestehen danach erneut in0,66s; Dokument-/Diffprüfung bestanden. Gesamtaussage
bleibt unverändert: Schritt3 offen. Damit ist die vorab festgelegte Bedingung
für Phase B erfüllt: acht kleine neue Differenzsolves, anschließend höchstens
drei reale gemeinsame Vorschläge, ohne weitere Suche in diesem Experiment.

## Phase B: gemeinsamer tatsächlicher Vorteil auf dem Konstruktionsraster

Bei f700b57 acht vollständige +/-10µm-Differenzsolves und alle drei tatsächlichen
Vorschläge abgeschlossen. Keine fehlenden Domänenzellen oder Solverfehler. Alle
drei Probes erfüllen die festgelegten Konstruktionsschirme; ausgewählt wird
Probe0/Index8 als kleinster breiter S-Wert. Die Delta-Koeffizienten in Metern:

| rbc(1,1) | zbs(1,1) | rbc(2,0) | zbs(2,0) |
| ---: | ---: | ---: | ---: |
|-1e-4|+5,12303771890279e-5|-1e-4|+1e-4|

Enge Zielgröße1,0986179404311691e-5:4,85063% besser als die Referenz. Breite
Konstruktionszielgröße2,1138442410077716e-4:11,15680% besser. Größte Änderung
mittlerer A1,01866%, unter2%; alle Enveloppe-/Geometriegrenzen bestehen dort.
Das sind echte neue Gleichgewichtsrechnungen, noch keine feinere Endabnahme.

Separater Phasenaudit bestätigt sämtliche Quellen, tatsächlichen Differenz-
und Probezustände, Aktionsquadratur, Gradienten-/Matrixarithmetik, alle
Konstruktionsklassifikationen und die Auswahl. Primal-/Dual-/Komplementaritäts-
fehler höchstens1,0409e-17 versus1e-8. Modellprognose für gemeinsamen relativen
Abstieg9,4484%; die kleinere tatsächliche enge Verbesserung zeigt ausdrücklich
die Grenze des lokalen Modells. Es wird nicht als qualifizierte exakte Ableitung
oder physisches Optimum bezeichnet.

Berichte `propose.json` und `propose-audit.json` im Evidenzordner.11 neue Solves
verbraucht, genau zwei für Kaltwiederholung und401er Kandidat verbleiben. Auswahl
ist eingefroren.46 gezielte Tests, Dokument-/Diffprüfung bestehen vor diesem
Zwischencommit erneut; keine numerischen Dateien während des Experiments verändert.

## Kaltendpunkte: exakte Wiederholung innerhalb des Budgets

Bei83deca6 genau zwei weitere Kaltstarts beendet, damit13 neue Solves insgesamt.
Wiederholung stimmt in allen13 registrierten Wout-/Solvergrößen und zusätzlich
allen breiten Aktionsarrays exakt überein. Keine Endpointfehler. Auf401 Flächen
beträgt der enge Trainingswert1,100894343118703e-5, der breite801/16-Wert
2,116352700615963e-4. Noch kein Ersatz für die weiter verfeinerten Diagnosen.
Letzte Zelle187,98s, Reserve mindestens10340872192Bytes.

Die [vollständige neue401er Eingabe](../../evidence/plasma-balanced-v1/selected-input-401.json)
ist zusätzlich bytegleich in Git exportiert, mit `cmp` gegen die tatsächlich
gerechnete Eingabe geprüft. Die unveränderte
[401er Referenzeingabe](../../evidence/plasma-design-v2/reference-input-401.json)
bleibt getrennt. Endpointbericht in `endpoints.json`;46 Kontrollen bestehen
erneut in0,89s, Dokument-/Diffprüfung ebenfalls. Danach kompletter Vier-Zustands-
Auswerter und unabhängiger Gesamtaudit, ohne weitere Auswahl oder Solves.

## Vollständige feinere Abnahme: alle zehn Gates bestanden

Diagnostik und separater Gesamtaudit bei f285fbd abgeschlossen, normaler Exit0:
`arithmetic_and_source_pass:true`, `step3_pass:true`. Der Auditor prüft zuerst
alle16 Archivformen, acht Differenzen, drei Vorschläge und die eingefrorene
Auswahl erneut; erst danach die Kaltendpunkte und endgültigen physischen Gates.
Alle Quellen-/Eingabe-/Quadratur-/Zellstatistikprüfungen bestehen. Kein bloßes
Übernehmen des Produzenten-Passflags. Getrennte Prüfimplementierung auf demselben
Rechner, keine externe wissenschaftliche Begutachtung oder zweite MHD-Solverfamilie.

Feinster Vergleich:401 radiale Flächen,3201 phi-Punkte,64 alpha-Linien, zwei
Feldperioden; s=(0,1;0,25;0,5;0,75;0,9), q=(0,03;0,1;0,3;0,5;0,7;0,9;0,97).
Das dimensionslose S mittelt die relative Varianz der positiven Einwegwirkung
über diese35 Zellen und ihre jeweils zwei periodenzugeordneten Muldenfamilien.
Dieselbe feste Bstar(q)-Skala und dieselbe Autorenreferenzeingabe, frisch mit
demselben VMEC++0.7.3 gerechnet; kein Vergleich gegen behauptete historische Bitidentität.

| Abschlussgate | Tatsächlicher Prüfwert / Nachweis | Unveränderte Grenze |
| --- | --- | --- |
| Neue Form | Vier benannte Änderungen wie oben, vollständige401er Eingabe gespeichert | Nichtidentischer Rand, nur erlaubte Moden und Profile |
| Wiederholung | Alle13 registrierten Wout-/Solvergrößen und enge Aktionen exakt; breite Arrays zuvor ebenfalls exakt geprüft | Separater realer201er Kaltstart |
| Geometrie | Volumenänderung−0,0074481%; maximale absolute iota-Änderung0,000324754 | Betrag≤1% beziehungsweise≤0,02 |
| Feld / Konturen |24 Feldgitter und280 Konturzellen bestehen, keine fehlende Messzelle | Sämtliche registrierten Domänen und beide Konturauflösungen |
| Anderer Tracer | Beide401er Zustände bestehen; größtes relatives B-Delta2,1354e-12, normiertes Längen-Delta2,5332e-6, A-Delta7,8889e-6 | B≤1e-8; Länge/A≤1e-3 |
| Verfeinerung | Alle20 Vergleiche bestehen; größtes zugeordnetes relatives A-Delta3,0222e-4 | A≤1e-3; S≤5% beziehungsweise1e-12 absolut |
| Lokale Wirkungsgrenzen | Alle70 Zellen bestehen; größte mittlere A-Änderung1,01834%; maximale Enveloppe/Grenze0,976693 | A-Mittel≤2%; Enveloppe≤max(1,1×Referenz,Referenz+0,002) |
| Enger Trainingsvorteil |1,154624499907537e-5 →1,0986179404311693e-5:4,85063% | Mindestens0,5% |
| Feinster breiter Vorteil |2,3894265674165413e-4 →2,122527071486505e-4:11,17002% | Mindestens0,5% |
| Numerisch aufgelöster Vorteil | Absoluter S-Gewinn2,6689949593e-5;47,3762×Unsicherheitssumme5,6336157065e-7 | Gewinn>5×Summe beobachteter Verfeinerungsänderungen |

Vollständige Abdeckung: vier Zustände mal vier Tracegitter, also16 Raster mit
je35 s/q-Zellen;40 Konturgitter/280 Klassifikationen,24 Feldgitter, zwei
Autoren-Tracer-Gegenprüfungen mit jeweils drei Radien. Auch das verschobene
alpha-Raster und sämtliche radialen Vergleiche sind erhalten. Fehlende oder
zensierte Mulden hätten abgelehnt werden müssen; keine traten auf. Größter
relativer Unterschied zur unabhängigen64-Punkt-Gaussquadratur1,29894e-9 versus1e-6.
Größter physischer Feldidentitätsfehler2,08129e-6 versus1e-3; größte Änderung
dieses Fehlers bei Feldgitterverfeinerung6,39122e-8 versus1e-5.

Die Unsicherheitssumme ist ein vorab definierter empirischer numerischer Schirm,
keine rigorose Fehlerschranke oder statistisches Konfidenzintervall. Ein niedrigerer
Gesamtwert bedeutet nicht Verbesserung jeder einzelnen Zelle; deren mögliche
Verschlechterung bleibt durch die separat geprüften lokalen Grenzen beschränkt.

## Evidenz, Kosten und Abschlusskontrollen

- [Finaler separater Audit](../../evidence/plasma-balanced-v1/final-audit.json):
  alle zehn Gates, genaue Scores/Verfeinerungen, Quellen und Auswahlherkunft.
- [Vollständige Diagnostik](../../evidence/plasma-balanced-v1/validation.json)
  mit [explizitem Adapter](../../evidence/plasma-balanced-v1/diagnostic-adapter/summary.json):
  alle Raster und Rohdatenhashes, kein behaupteter alter Zwei-Poll-Suchlauf.
- [Archivaudit](../../evidence/plasma-balanced-v1/archive-audit.json),
  [Vorschlagsaudit](../../evidence/plasma-balanced-v1/propose-audit.json) und
  [Kaltendpunkte](../../evidence/plasma-balanced-v1/endpoints.json): vollständige
  vorgeschaltete Phasen, nicht als eigene physische Abschlusszulassungen umgedeutet.
- [Angenommene Eingabe](../../evidence/plasma-balanced-v1/selected-input-401.json)
  und [Referenzeingabe](../../evidence/plasma-design-v2/reference-input-401.json):
  vollständige tatsächlich gerechnete JSONs in Git. Der abgelehnte Kandidat im
  alten Evidenzordner bleibt erhalten und ist nicht mit dieser neuen Form zu verwechseln.
- [Abschluss-Snapshot](../../evidence/plasma-balanced-v1/closure-checks.json):
  finaler Audit und weiterhin negativer Vorgänger hashgebunden,766 JUnit-Fälle
  ohne Fehler/Skip, beide exportierten Eingaben bytegleich, historischer
  Dateierhalt und fünf externe Quellstände erneut lesend geprüft. Keine neue
  physische Zulassungsregel; Grundlage sind die zuvor registrierten Gates.

Genau13 neue Kaltstarts im Folgeversuch,779,19s summierte native Zelllaufzeit;
längste Zelle187,98s versus1800s-Kappe, niedrigste dort gemessene Reserve
10340872192Bytes. Einschließlich des vollständig erhaltenen ersten Versuchs
32 Kaltstarts und2018,00s summierte Zelllaufzeit. Das schließt Diagnose-/Auditzeit
nicht ein und ist kein fairer Methoden-Laufzeitvergleich. Keine Installation,
kein weiterer Solve und keine zusätzliche Suchrunde für die finale Abnahme.

Abschlussregression nach dem Gesamtaudit:766 Tests bestanden,144 bekannte
Fixture-Warnungen,55,38s; Roh-JUnit unter
`artifacts/plasma-balanced-v1/closure-regression.xml`. Ruff, Dokumentstruktur und
`git diff --check` bestehen. Alle1266 bei5971fee erfassten historischen Dateien
sind bis auf explizit erlaubte Übersichts-/Journalpflege erhalten; alle fünf
externen Quellen inklusive ihrer schon vorher bestehenden Änderungen stimmen
mit `foundation-acceptance-v2/run.json:external_before` überein. Keine historischen
numerischen Kerne oder Fehlschläge umgeschrieben. Der bekannte strenge netCDF-
Importwarnungsbefund bleibt offen; die historische Tracerquelle erzeugt beim
Parsen weiterhin die erhaltene Syntaxwarnung zum Escape, keine Warnungsfreiheit.

## Aussagegrenzen und Übergabe

Belegt ist eine eigene geänderte Randform mit frisch gerechneten Gleichgewichten
und numerisch abgesicherter Verbesserung einer QI-relevanten Zielgröße auf der
registrierten Vakuumdomäne. **Nicht belegt sind11,17% besserer Teilcheneinschluss,
Fusionsleistung oder Kraftwerkswirkungsgrad.** Die Abnahme verwendet VMECs Annahme
verschachtelter Flussflächen; keine globale Omnigenität/QI oder vollständige
Topologiequalifikation. Maximum-J, endliche Teilchenbahnen, Transport/Turbulenz,
endlicher Plasmadruck, MHD-Stabilität, passende Spulen/Mechanik, SoTA-Vergleich und
SQuID-C-Reproduktion bleiben getrennte offene Aufgaben.

Beide bekannten Wirkungsdomänen gingen bereits in die Konstruktion ein. Die
unabhängigere Quadratur, feineren Raster, neue radiale Auflösung und der andere
Tracer prüfen numerische Tragfähigkeit, nicht blinde Generalisierung auf neue
Plasmabereiche. Keine globale oder lokale Optimalkonvergenz behauptet. Der Nutzen
des lokalen linearen Modells ist hier ein tatsächlich bestätigter gemeinsamer
Schritt; seine Prognose blieb ungenau. Die angenommene Form und alle negativen
Vorgänger sind nun Ausgangsmaterial für später gesondert registrierte Arbeit.

## Phasen ausführen und getrennt bewerten

Der Umgebungspräfix aus dem [ersten Runbook](PLASMA_OPTIMIZATION_RESULTS.md)
gilt unverändert. Neue Pfade verwenden, mindestens3GiB Reserve. Nach jeder
abgeschlossenen Phase Dokumentation/Checks/Commit, erst dann nächste Phase.

```sh
.venv/bin/python scripts/run_balanced_plasma.py archive evidence/plasma-balanced-v1 artifacts/plasma-balanced-v1
.venv/bin/python scripts/audit_balanced_plasma.py archive evidence/plasma-balanced-v1 evidence/plasma-balanced-v1/archive-audit.json
```

Nur wenn `archive.json` keinen ausgewählten Index enthält:

```sh
.venv/bin/python scripts/run_balanced_plasma.py propose evidence/plasma-balanced-v1 artifacts/plasma-balanced-v1
.venv/bin/python scripts/audit_balanced_plasma.py propose evidence/plasma-balanced-v1 evidence/plasma-balanced-v1/propose-audit.json
```

Nur mit tatsächlich ausgewähltem Kandidaten, nicht bei bloßem Modellabstieg:

```sh
.venv/bin/python scripts/run_balanced_plasma.py endpoints evidence/plasma-balanced-v1 artifacts/plasma-balanced-v1
.venv/bin/python scripts/validate_balanced_plasma.py evidence/plasma-balanced-v1 artifacts/plasma-balanced-v1/validation
.venv/bin/python scripts/audit_balanced_plasma.py final evidence/plasma-balanced-v1 evidence/plasma-balanced-v1/final-audit.json
```

Ein Phasenaudit-Pass ist ausdrücklich kein Schritt3-Pass. Nur das positive finale
Ergebnis mit allen unveränderten physischen Gates erlaubt den registrierten
Vakuumabschluss. SQuID-C, globale QI-/Orbitphysik und SoTA bleiben getrennt.

Schritt3 abgeschlossen; nach Dokumentation und lokalem Commit Übergabe.
Keine automatische Fortsetzung in Schritt4/5 oder weitere Suche. Die obigen
Befehle dokumentieren die Reproduktion, nicht die Aufforderung, bestehende
unveränderliche Pfade erneut zu verwenden oder den Abschluss neu zu definieren.
