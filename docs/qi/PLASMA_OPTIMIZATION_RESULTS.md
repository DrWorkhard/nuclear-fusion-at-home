# Eigene QI-nahe Plasmaoberfläche: Arbeitsstand und Bedienung

Stand: 14. September2026. [Festes Protokoll](PLASMA_OPTIMIZATION_PROTOCOL.md).
**Schritt3 noch offen; erster Entwurf unabhängig abgelehnt.** Die ausgewählte
Oberfläche verbessert den Trainingswert um14,35%, verschlechtert aber die
erweiterte Zielgröße um15,53% und verletzt20 lokale Wirkungsgrenzen.
Die vollständige numerische Abnahme ist beendet. Die früheren Schritte1/2
und sämtliche alten negativen Forschungsdaten bleiben unverändert.

## Implementierung vor erster Rechnung

Vier explizite Randmoden, zwei deterministische Pollrunden mit Cache-/Arbeits-
zählern, separate Kaltwiederholung und201/401-Endpunkte. Jeder Solver schreibt
Input, Request, Log, Wout, Kraftreste und terminalen Zustand. Zeit-/Platzwächter
beenden nur den selbst gestarteten Prozess. Alte Inputs/Wouts werden nicht überschrieben.

Die Zielgröße ordnet je zwei vollständige Teilchenmulden ihren Feldperioden zu.
Alle angefragten s/q-Zellen werden versucht; fehlende/zensierte Mulden erhalten
Fehlereinträge und können keine scheinbaren Nullkosten erzeugen. Der separate
Auditor rekonstruiert die gesamte Pollfolge, prüft Quellen und Änderungen aller
Eingabefelder, kontrolliert gespeicherte Traces durch skalare Fourier-/Geometrie-
Stichproben und integriert Aktionen mit separater64-Punkt-Gaussquadratur.
Physische Zulassung, Prozessabschluss und Vorteil bleiben eigene Aussagen.

27 gezielte Kontrollen bestehen, einschließlich analytisch bekannter Varianz,
fehlender Mulden/Zellen, NaN, falscher Modenzuordnung, manipulierter Auswahl,
unzureichend aufgelöstem Vorteil und falschen Zulassungsflags. Der erste Testlauf
fand eine fehlende Winkelendpunktprüfung im separaten Integrator (24/25 bestanden);
vor jeder neuen Physikrechnung korrigiert. Ein zusätzlicher skalarer Quellencheck
am erhaltenen Wout besteht und weist manipuliertes B zurück. Kandidateninput
durchläuft die echte VMEC++-Modellkonversion unverändert, ohne Solve.

Gesamtsuite vor der letzten zusätzlichen Quellenkontrolle:745 Tests/144 bekannte
Warnungen in68,54s. Danach26 gezielte Tests in0,27s. Ruff besteht. Bekannte
netCDF-/NumPy-Grenzen werden nicht als behoben ausgegeben. Dokument-/Diffprüfung
und lokaler Implementierungscommit erfolgen vor dem ersten neuen Solve.

## Abgeschlossene Auswahl und erhaltene Zwischenbefunde

Lauf `plasma-design-v2` bei90cdc57:17 Anfragen,16 neue201er Suchgleichgewichte,
ein exakter Cachetreffer. Alle16 erfüllen laut gespeicherten Produzentenberichten
die numerischen/Domänen-/Konstruktionswächter. Jede Runde wertet alle acht
Richtungen aus; gewählte Indizes3 und11. Keine behauptete Suchkonvergenz.

| Größe | Frische Referenz | Ausgewählter Entwurf |
| --- | ---: | ---: |
| Änderung zbs(1,1) gegenüber Autoreninput |0m|+0,0004m|
| Übrige drei registrierte Änderungen |0m|0m|
| Trainings-S |1,1546244999075371e-5|9,889668968130651e-6|
| Relativer Trainingsvorteil |—|14,347314%|

Der separate201er Kaltstart liefert denselben S-Wert; direkter unabhängiger
Vergleich aller13 registrierten Gleichgewichts-/Solverarrays ist exakt. Die
gesamte Poll-/Cache-/Auswahlfolge und alle referenzierten Dateihashes sind separat
nachgerechnet/geprüft. Alle19 Kaltstarts einschließlich beider401er Endpunkte sind
abgeschlossen; längster Zellaufwand206,96s, kleinste beobachtete Reserve
11054202880Bytes. Auf401 Flächen lauten die Trainingswerte1,1566931154823263e-5
und9,913012143094501e-6. Die damals ausstehende erweiterte Abnahme ist unten abgeschlossen.
Auswahlergebnisse bleiben danach eingefroren; feinere Abnahme kann ablehnen,
aber keine andere Form nachträglich zum ausgewählten Kandidaten machen.
Aktives Journal: `evidence/plasma-design-v2/summary.json`, Rohdaten in
`artifacts/plasma-design-v2/`. Der Suchbericht ist jetzt final und wird unverändert
committet. Die vollständigen401er Eingaben für
[Referenz](../../evidence/plasma-design-v2/reference-input-401.json) und
[ausgewählte Form](../../evidence/plasma-design-v2/selected-input-401.json) werden
zusätzlich bytegleich in Git gehalten; beide Kopien mit `cmp` geprüft. Große
Rohdateien bleiben lokal erhalten und über den Bericht hashgebunden. Es gibt
weiterhin keinen bestätigten Vorteil auf der erweiterten Domäne.

## Unabhängige Abnahme: vollständiger negativer Entwurfsbefund

Alle vier Zustände und16 erweiterte Messgitter abgeschlossen,280 Konturprüfungen,
24 native/Clebsch-Gitter sowie beide Autoren-Tracing-Gegenrechnungen bestanden.
Alle20 Winkel-/Alpha-/Radial-Verfeinerungsvergleiche bestehen. Größte zugeordnete
Aktionsänderung4,5361e-4 relativ, unter1e-3. Separater Auditor bestätigt alle
Quellen, Modenänderungen, Pollauswahl, vollständigen Domänen und Aktionsarithmetik;
größter ausgewiesener Holdout-Gaussfehler1,6944e-9 relativ, unter1e-6.

| Feinste erweiterte Größe | Referenz | Ausgewählte Form |
| --- | ---: | ---: |
| S bei401/3201/64, unverschoben |2,3894265674165405e-4|2,760471268245426e-4|
| Änderung |—|15,5286% schlechter|
| Maximale relative Änderung mittlerer A |—|34,9135%, erlaubt2%|

20 von70 s/q/Periodenzellen überschreiten die2%-Mittelwirkungsgrenze; vier davon
zusätzlich die Enveloppegrenze. Die maximale normierte Grenzüberschreitung der
Enveloppe beträgt1,0321. Tief gefangene q=0,03-Zellen liefern bereits bei der
Referenz rund95,8% des erweiterten S; ihr Beitrag steigt von2,2885e-4 auf2,6698e-4.
Sie waren nicht im Training enthalten. Auch q=0,1-Mittelwirkungen ändern sich
unzulässig, obwohl die bloßen Volumen-/iota-Wächter bestehen.

Die beobachtete numerische Unsicherheitssumme ist7,6543e-7; die Verschlechterung
ist rund48,5-mal so groß. Keine Erklärung durch hier untersuchte Gitterfehler.
Zulassungsflags: Quellen/Arithmetik, neue Form, Wiederholung, Geometrie, Felder,
Konturen, Tracer, Verfeinerung und Trainingsvorteil bestehen; lokale Wirkungs-
schirme, erweiterter Vorteil und aufgelöster positiver Vorteil scheitern.
Auditor-Exit2 ist ein regulärer negativer Befund, kein Programmfehler.

Evidenz: `evidence/plasma-design-v2-holdout.json`, `-audit.json`, `-diagnosis.json`;
Rohdaten in `artifacts/plasma-design-v2-holdout`. Diagnose rechnet ausschließlich
bereits auditierten Zelltabellen nach, ohne neue Feldaufrufe. Die historische
Autorenroutine erzeugt beim Parsen eine sichtbare SyntaxWarning zu `\\p`; keine
Quelldatei verändert oder Warnungsfreiheit behauptet.27 gezielte Tests, Ruff,
Dokument- und Diffprüfung bestehen nach Abschluss erneut.

Folgerung: Die enge Trainingsdomäne und nur globale Geometriewächter reichen
nicht. Ein separat vorab registrierter Folgeversuch muss tiefe Mulden und lokale
mittlere Wirkung schon bei der Konstruktion berücksichtigen; beide bisherigen
Domänen sollen profitieren. Kein alter Grenzwert oder Fehlschlag wird geändert.

## Erhaltener erster Startfehler

Bei c9801ba verlangte die neue Quellenprüfung einen direkten Git-Eintrag des
historischen Rohinputs. Er liegt absichtlich im ignorierten Artefaktbaum; seine
Bytes sind bereits durch den committeten Originalbericht gebunden. Der Start
endete vor Verzeichniserzeugung oder Solve. Terminalbefund ist ausdrücklich als
manuelle Übertragung in `evidence/plasma-design-v1-preflight-error.json` erhalten.
Korrektur: direkter Commitnachweis für Berichte/Code/Protokoll, unverändert strenger
SHA-Nachweis für Rohdaten. Zusätzlicher Test schützt diese Trennung. Kein Input,
keine alte Evidenz, keine physische Schwelle verändert. Nächster frischer Lauf: v2.

## Bedienung auf den vorhandenen gesperrten Umgebungen

Alle drei Phasen nacheinander, keine konkurrierenden schweren Rechnungen. Vorher
Code/Protokoll committen und mindestens3GiB frei halten; währenddessen2GiB.
Neue, noch nicht vorhandene Ergebnisverzeichnisse und Berichtsdateien verwenden.
Für jeden Aufruf gilt dieser Umgebungspräfix:

```sh
export PYTHONPATH=src
export MPLCONFIGDIR=/private/tmp/fusion-mpl-cache
export OMPI_MCA_btl=self
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
.venv/bin/python scripts/run_plasma_search.py evidence/plasma-design-v2 artifacts/plasma-design-v2
.venv/bin/python scripts/validate_plasma_design.py evidence/plasma-design-v2 evidence/plasma-design-v2-holdout.json artifacts/plasma-design-v2-holdout
.venv/bin/python scripts/audit_plasma_design.py evidence/plasma-design-v2/summary.json evidence/plasma-design-v2-holdout.json evidence/plasma-design-v2-audit.json
```

Kein Installationsschritt. Ein negatives Auditorergebnis bleibt erhalten und
schließt Schritt3 nicht; keine nachträgliche Grenzwertänderung. Die gespeicherte
ausgewählte Inputdatei ist der reproduzierbare Entwurf, nicht eine Abbildung oder
ein bloßes Parameterarray. Diese drei v2-Aufrufe sind abgeschlossen und können
nur unter frischen Pfaden wiederholt werden. Nächster Schritt: einen gezielten
Folgeversuch mit beiden Domänen und lokalen Wirkungswächtern vorab registrieren.
