# Kumulative Spulengeometrieschranke: qualifizierte Software

20. September2026. [Festes Protokoll](COIL_PERTURBATION_PROTOCOL.md) beiafb9307,
[Methodenentscheidung mit zwei Reviews](../optimization/GEOMETRY_PRESERVING_SEARCH_OPTIONS.md).
Die reale52-Zustandsmatrix ist noch nicht ausgeführt. Keine neuen Felder,
Gleichgewichte, LPs oder Suchaufrufe. Feldstartabschluss3334f1e unverändert.

## Implementierung vor der realen Perturbationsmatrix

Konstruktionsroutine und eigenständige mathematische Abnahme wurden durch
getrennte Agenten implementiert. Die reine mathematische API erhält den
originalen Geometriesnapshot, zugehörigen originalen Auditset und neue
Koeffizienten. Sie prüft Schema, Namen, Symmetrie und vorhandene Support-/Export-
Beweiskette, behauptet aber keine kryptografische Herkunft aus erfundenen
Snapshotreferenzen im alten Report. Diesen Teil übernimmt ein eigener Quellenbinder.

Der neue Binder besteht37 reine Kontrollen. Er bindet die bei3334f1e
committeten Lauf-/Auditbytes und jede einzelne positive N/V-/Raster-/Flussprüfung,
alle vier unverändert negativen physischen Feldentscheidungen sowie die exakten
ausgewählten Geometriesnapshots/reportindices3/9. Ganzer aktueller Rohgraph wird
gehasht, frühere Versionsgrenzen bleiben erhalten. Lesender tatsächlicher
Vorgänger-Replay ebenfalls bestanden; keine neue Kandidatengeometrie dafür.
Die Konstruktion besteht55 Tests, der getrennte mathematische Auditor108;
zwölf synthetische Fälle vergleichen die vollständigen Berichte beider Wege.
Geprüft sind unter anderem Null-/ULP-Änderung, Translation, Rotation, hohe Moden,
kumulative statt zurückgesetzter Änderungen, fehlende/gefälschte Beweisketten,
getrennte analytische Abstandsgrenzen und JSON-sichere negative Zertifikate.
Der reine Auditor importiert den neuen Konstruktor nicht. Beide verwenden
bewusst dieselben eingefrorenen Hilfen für den bereits qualifizierten alten
Seedbeweis; keine behauptete vollständige Unabhängigkeit dieser Vorgeschichte.

Ein zusätzlicher rein lesender Agentenreview findet keinen mathematischen Blocker:
Geschwindigkeits-/Kreuzprodukt-/Krümmungshüllen, homotoper Projektionsbeweis,
Symmetrierundung und beide Abstandstransfers sind schlüssig. Keine externe
wissenschaftliche Begutachtung. Quellenbinder bleibt zwingend; ein negatives
Zertifikat beweist keine reale Verletzung, Gleitkommapolster sind keine
gerichtete Intervallarithmetik.

[Softwarequalifikation](../../evidence/coil-perturbation-v1-primitives.json):
**1840 Tests bestanden**,334 bekannte Warnungen,0 Fehler/Skips,201,57s.
Davon200 neue Tests. Vollständiges JUnit unter
`artifacts/coil-perturbation-v1-primitives-qualification/regression.xml`, Hash
`275cad352bd79ccf4c162142e9e846f244f5ba905d1965f10bd95375b23f7a00`.
Repository-Ruff, Dokumentstruktur und Diffprüfung bestanden.

## Präzisierung der Symmetrierundung vor neuer Numerik

Bei nfp2 ist die ideale physische Kopie durch eine exakt orthogonale signierte
DiagonalmatrixQ* für Periode/Flip definiert. Die tatsächlich gespeicherte
MatrixQ=matrix.T kann kleine sin(π)-Reste enthalten. Normale, V0/A0 und
geerbte v0/S0/κ0/L0 aufQ* beziehen; Differenzhülle achsen-/koeffizientenweise aus

```
abs(Q @ candidate - Q @ seed) + abs((Q - Q*) @ seed) + pad
```

ableiten. Sie deckt sowohl die Bewegung gegenüber der tatsächlichen gespeicherten
physischen Seedkopie für direkte Abstände als auch die Bewegung gegenüber der
exakt orthogonalen Kopie für den Ableitungs-/Projektionsbeweis. Zusätzlicher
Rundungsverbrauch ist konservativ; kein stilles Gleichsetzen einer float-Matrix
mit perfekter Orthogonalität und keine doppelte Wiederverwendung der alten
Exportabweichung. Die Protokollbytes und physikalischen Grenzen bleiben unverändert.

## Offene Abnahme

Mathematische Routinen und synthetische Gegenprüfung sind abgeschlossen;
begrenzter realer Runner und vollständiger unabhängiger Matrixauditor sind
nun ebenfalls softwarequalifiziert. Neuer additiver Quellenbinder besteht32 reine Tests und
bindet die primitive Qualifikation bei20e9b10 samt tatsächlicher JUnit-Datei,
alle sechs damaligen Programm-/Testdateien und das unveränderte Protokoll.
Die zehn neuen Workflowdateien werden vor realer Rechnung committet.
Die auf Nutzerwunsch dazwischengeschobene [gemeinsame CLI](../validation/PROJECT_ENTRYPOINTS.md)
ist inzwischen mit64 neuen Tests und echtem gespeicherten Audit abgeschlossen;
sie umgeht die ausstehende reale Qualifikation nicht. Nun nach dem
Implementierungscommit die feste reale Matrix ausführen und unabhängig abnehmen.
Vor einer
Suchfreigabe muss die gesamte hier registrierte feldfreie Studie abgeschlossen
sein. Selbst ihr Pass wäre weder ein Feldgewinn noch ein Schritt4-Abschluss;
ein echter Feldfit erhält danach ein separates Protokoll.

## Workflowpräzisierung vor der realen Matrix, 20. September

Die beiden vollen256²-Plasmaflächen werden **genau einmal gemeinsam** erzeugt:
innerhalb des ersten Klassenworkers und damit innerhalb seines vorhandenen
1800-s-Budgets. Zweiter Worker liest exakt dieselben gebundenen NPZ-Dateien;
keine zusätzliche Vorbereitungszeit oder stillschweigende Neuberechnung.
Fehlt das vollständige Flächenregister, bleibt die zweite Klasse ausdrücklich
nicht ausgeführt. Der unabhängige Auditor rekonstruiert beide Flächen einmalig
und zählt diese Arbeit gesondert. 52 Zustände/104 Zertifikatsaufrufe/208 direkte
Kurvenraster bleiben unverändert.

Direkte Daten speichern punktweise Ableitungsdifferenznormen, Geschwindigkeit,
Krümmung mit Verfügbarkeitsmaske und orientierte Projektion; zusätzlich alle
CP-Abstandsvektoren/Indices sowie jedes CC-Paarminimum samt Punktzeugen.
Keine dichte Kurve×Plasma-Distanzmatrix. Drei direkte Fourierauswertungen pro
Raster (Kandidat, gespeicherter Seed, ideale orthogonale Seedkopie) werden
explizit gezählt. Längen kontrollieren die Differenz zum gleichen Seedraster,
nicht ein Stichprobenintegral als exakte kontinuierliche Länge.
Neue Kandidatenkoeffizienten liegen separat; kein veränderter Snapshot erbt den
alten Geometriepass. Diese Präzisierungen verändern keine Schwelle oder Matrix.

Vor realen Daten ebenfalls explizit festgelegt: Direkte Einschließungen gelten
**streng gegen die bereits nach außen gepolsterten Zertifikatsgrenzen**, ohne
zusätzlichen Toleranzabzug. Die im Protokoll erlaubte Vergleichstoleranz
relativ5e-12 oder absolut1e-12 betrifft ausschließlich den Vergleich gespeicherter
mit unabhängig rekonstruierter Rechengrößen. Der Auditor hält die kleinste
verbleibende Marge jeder Einschließungsfamilie samt Anzahl fest. Physische Gates
und boolesche Klassifikationen bleiben unverändert exakt.

Der abschließende lesende Workflowreview prüft zusätzlich Zeitidentität,
vollständige gespeicherte Pläne und Checkpointpräfixe. Er findet vor realer
Numerik einen Unabhängigkeitspunkt: Nach dem tolerierten Rohpunktvergleich
muss die eigenständig rekonstruierte Quellfläche in die CP-Einschließungen
eingehen, nicht das innerhalb Vergleichstoleranz ähnliche Producerarray.
Diese Trennung ist samt gezielter Kontrolle umgesetzt; keine zusätzliche
Flächenarbeit und keine veränderte Geometriegrenze.

Die abgeschlossene gezielte Qualifikation umfasst151 neue Tests:32 Quellenbinder,
50 Runner/Stichproben und69 Gesamtauditor/direkte Abnahme (41/28). Alle bestehen;
die getrennten Implementierer melden für ihre abschließenden50/69 Kontrollen
3,67/2,73s und keine Warnungen. Ein früher Test verdrahtete einen Hilfsnamen
falsch (`runner.arrays` statt `runner.storage.arrays`):25 Pass/1 Fehler, korrigiert
ohne numerische Änderung. Der vollständige Producer→Auditor-Ablauftest verwendet
synthetische Quellen und ausdrücklich gemockte innere Geometrie; die eigentlichen
mathematischen und direkten Routinen besitzen separate analytische Kontrollen.
Kein solcher Test ist eine reale Projektmatrix. Abschließender rein lesender
Review findet nach den genannten Korrekturen keinen verbleibenden Blocker.
Die erste vollständige Projektregression besteht2055 Tests,334 bekannte
Warnungen,0 Fehler/Skips in203,66s; alle zehn Quellhashes bleiben unverändert.
JUnit `artifacts/coil-perturbation-v1-workflow-qualification/regression.xml`,
SHA256 `45149b6c9801945bed71273c19c9792cf2cedc622b3d908ab78987091fff0953`.
Trotzdem ist die Qualifikation zunächst blockiert: Die zusätzliche Root-Prüfung
findet einen bis dahin ungetesteten Wiederanlauffehler. Der erfolgreiche
Checkpoint enthält den Hash der veränderlichen `inflight.json`; der nächste
Versuch überschreibt diese Referenz. Bei anschließendem Fehler bleiben nur
Checkpointbytes, nicht ihr vollständiger Referenzgraph gültig. Drei getrennte
lesende Nachprüfungen bestätigen das. Vollständige erfolgreiche Läufe sind
nicht betroffen. Die erste JUnit-Datei bleibt erhalten. Erst nach Ende dieser
Regression werden unveränderliche Marker je erfolgreichem Zustand und gezielte
transitive Fehlerpfadprüfungen ergänzt; danach neue vollständige Regression.
Keine reale Projektmatrix vor dieser Korrektur und dem Implementierungscommit.

Die Korrektur ist implementiert: unveränderliche
`state-NN/checkpoint-inflight.json` vor jeder erfolgreichen Checkpointveröffentlichung,
separater veränderlicher Live-Marker. Der Auditor bindet beide Pfade/Hashes und
prüft den korrekten letzten Versuch unabhängig vom unveränderten restlichen
Checkpointpräfix. Neue Fehlerkontrollen prüfen den vollständigen Referenzgraphen
nach Zertifikatsfehler/Timeout sowie Fehler beim Schreiben des nächsten Markers
oder Checkpoints. Auch dann bleibt der vorige erfolgreiche Stand unverändert
und vollständig lesbar.160 gezielte Kontrollen bestehen:32 Binder,30 Workflow,
22 Sampler,48 Gesamtauditor,28 direkte Abnahme. Die zweite vollständige Regression
besteht **2064 Tests**,334 bekannte Warnungen,0 Fehler/Skips in205,19s.
JUnit `artifacts/coil-perturbation-v2-workflow-qualification/regression.xml`,
SHA256 `eb08470da78644933774dfa680f4a309ef77b0ab4c5a15095399367b4f5e9a78`.
Alle zehn Quellhashes vor/nach Regression identisch; keine Änderung der
mathematischen Routinen oder Schwellen. Ruff, Struktur- und Diffprüfung bestanden.
[Quellgebundene Gesamtqualifikation](../../evidence/coil-perturbation-v1-workflow-qualification.json)
bewahrt auch die erste Regression mit ihren damaligen Quellhashes und der
danach erkannten Lücke. Wiederanlaufregel zusätzlich dauerhaft als
[D-018](../logbook/DECISIONS.md#d-018--preserve-the-complete-checkpoint-reference-graph-not-only-its-bytes)
und in den Arbeitsanweisungen verankert. Reale52-Zustandsabnahme noch offen.

## Bedienung des softwarequalifizierten Gesamtworkflows

Additive Programme `scripts/run_coil_perturbation.py` und
`scripts/audit_coil_perturbation.py`; Quellenbinder
`scripts/coil_perturbation_workflow_inputs.py`. Vor realer Ausführung müssen
sämtliche neuen Dateien qualifiziert und committet sein. Keine Freigabe durch
die gemeinsame CLI: Deren Version1 enthält weiterhin nur das bereits
qualifizierte Feldstartprofil. Der feldfreie Spezialworkflow wird getrennt
ausgeführt, ohne einen universellen Entwurfsprüfer zu behaupten.

Für den Produzenten ist `--raw` ein **neuer absoluter Verzeichnispfad**, für den
Auditor sind `--run` und `--output` absolute Pfade; die Auditdatei muss neu sein.
Beide Aufrufe benötigen die gebundenen historischen Rohdaten und die vorhandene
qualifizierte Umgebung. Ein vollständiger Produzent meldet lediglich
`producer_complete=true` und `admission_status=pending-independent-audit`.
Erst der separate Auditor kann `qualification_pass=true` vergeben. Auch dann
bleiben `search_allowed`, `field_pass`, `transfer_pass` und `step4_pass` false.
Ein größerer Probe ohne Zertifikat ist kein Ausführungsfehler und kein Beweis
einer realen Grenzverletzung; seine Daten und alle vier Raster bleiben erhalten.
