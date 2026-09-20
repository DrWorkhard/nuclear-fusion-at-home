# Kumulative Spulengeometrieschranke: reale Qualifikation bestanden

20. September2026. [Festes Protokoll](COIL_PERTURBATION_PROTOCOL.md) beiafb9307,
[Methodenentscheidung mit zwei Reviews](../optimization/GEOMETRY_PRESERVING_SEARCH_OPTIONS.md).
Die reale52-Zustandsmatrix ist abgeschlossen und unabhängig angenommen.
Alle zwölf kleinsten signierten Probes und beide Seeds samt Repeats sind
zertifiziert; alle104 mathematischen Berichte und208 direkten Raster bestehen
die vorgesehenen Prüfungen. Größere Probes dürfen unzertifiziert bleiben.
Keine neuen Felder, Gleichgewichte, LPs oder Suchaufrufe; Feldstartabschluss
3334f1e und dessen vier physische Ablehnungen unverändert.

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

## Quellenbindung und abgegrenzter Abschluss

Mathematische Routinen und synthetische Gegenprüfung sind abgeschlossen;
begrenzter realer Runner und vollständiger unabhängiger Matrixauditor sind
nun ebenfalls softwarequalifiziert. Neuer additiver Quellenbinder besteht32 reine Tests und
bindet die primitive Qualifikation bei20e9b10 samt tatsächlicher JUnit-Datei,
alle sechs damaligen Programm-/Testdateien und das unveränderte Protokoll.
Die zehn neuen Workflowdateien sind vor realer Rechnung bei930580e committet.
Die auf Nutzerwunsch dazwischengeschobene [gemeinsame CLI](../validation/PROJECT_ENTRYPOINTS.md)
ist inzwischen mit64 neuen Tests und echtem gespeicherten Audit abgeschlossen;
sie ersetzt die getrennte reale Qualifikation nicht. Diese wurde anschließend
ausgeführt und ist nun bestanden. Ihr Pass ist weder ein Feldgewinn noch ein
Schritt4-Abschluss; ein echter Feldfit benötigt als nächstes ein separates
Such-/Auswahl-/Abnahmeprotokoll.

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
und in den Arbeitsanweisungen verankert. Die damals noch offene reale
52-Zustandsabnahme folgt im nächsten Abschnitt.

## Reale52-Zustandsmatrix und unabhängige Abnahme

Sauberer Implementierungscommit `930580eba53a30a974e53faa31b0b0c2557ea4f2`;
Quellen vor/nach beiden seriellen Workern exakt identisch. Alle52 Zustände,
104 Zertifikatsaufrufe und208 direkten Raster vollständig gespeichert.
Je Zustand zwei bytegleiche Zertifikate, am Ende jeder Klasse bitgleiche
Seedkoeffizienten, Zertifikate und direkte Roharrays. Alle mathematischen
Vergleiche und sämtliche verfügbaren direkten Einschließungen bestehen.

| Klasse | Zertifizierte Zustände inklusive Seed/Repeat | Unzertifiziert, vollständig geprüft | Workerzeit / Elternzeit |
| --- | --- | --- | --- |
| n6, Fourierordnung5 | 18 von26 | 8 | 73,223 /73,387s |
| n8, Fourierordnung7 | 16 von26 | 10 | 98,225 /98,385s |

Beide Seeds, beide Seed-Repeats und sämtliche zwölf signierten1e-5-Probes
bestehen die vorab vorgeschriebene Zertifizierung. Insgesamt30 von48 veränderten
Probes zertifiziert. Die18 übrigen sind legitime negative Schrankenentscheidungen,
nicht ausgelassene Zustände oder nachgewiesene physische Unzulässigkeit.

Für beide Vorzeichen ergeben die **fest vorgegebenen Stichprobenradien**:

| Richtung | Größter geprüfter zertifizierter Radius n6 | n8 |
| --- | --- | --- |
| Gedämpfte sin(k+1)-Richtung | 1mm | 1mm |
| Gedämpfte cos(k+1)-Richtung | 1mm | 1mm |
| Einzelne z-sin(M)-Mode an Grundspule0 | 0,1mm | 0,01mm |

Das sind keine optimierten maximalen Radien und kein allgemeiner Methodenvergleich.
Die n8-Hochmode bei0,1mm scheitert allein am Krümmungszertifikat:
Obergrenze12,98898/m gegenüber12/m. Daraus folgt nicht, dass die reale Kurve
diese Grenze verletzt. Bei den vier extremen30mm-Hochmodezuständen ist
v_lower≤0 an insgesamt16 physischen Kurven; ihre κ-Obergrenze bleibt wie
registriert `not_available`. Alle sonst wohldefinierten Größen werden dennoch
geprüft. Weder fehlende Divisionen als Null noch schwache Schranken als
Unmöglichkeitsbeweis behandeln. Niedrige/glatt gedämpfte Richtungen sind damit
ein begründeter Startpunkt für den nächsten begrenzten Feldfit, kein bewiesenes
Optimum oder übertragener Magnetfeldgewinn.

Der Produzent erzeugt genau zwei gemeinsame256²-Torusflächen im ersten Worker;
der zweite liest dieselben Dateien. Direkte Arbeit pro vollständigem Gesamtweg:
624 Fourierauswertungen mit12.300.288 Kurvenpunkt-Auswertungen,
416 volle CP-Abfragen mit8.200.192 Punktabständen,
80.288 CC-Paarabfragen mit56.522.752 Querypunkten. Der unabhängige Auditor
rekonstruiert beide Flächen,52 Zertifikate und208 Raster separat und zählt
seine identische direkte Stichprobenarbeit ausdrücklich zusätzlich.
104 gespeicherte Zertifikatsberichte werden gegen52 unabhängige Rechnungen geprüft.
Sein eigener Referenzcache bindet1371 Dateien; die historischen Vorgängergraphen
werden zusätzlich durch den vorgeschalteten Quellenbinder geprüft.

Alle Einschließungen verwenden **null zusätzliche Vergleichstoleranz**.
Kleinste beobachtete Restmargen der Änderungsnormen D0/D1/D2:
2,4603e-13m /3,4464e-12m pro t /7,5683e-11m pro t².
Keine beobachtete Schrankenverletzung. Diese Stichproben ersetzen nicht die
mathematische kontinuierliche Beweiskette oder gerichtete Intervallarithmetik.
Rohdatenvergleichstoleranzen bleiben ausschließlich für die getrennten
Implementierungsvergleiche; physische Grenzen unverändert.

1177 Rohdateien,280.504.950Bytes insgesamt gegenüber geschätzten≤0,5GiB.
Kleinste beobachtete freie Reserve8.844.005.376Bytes; beide Klassen unter1800s,
keine schweren parallelen Projektjobs. Keine Felder/VJPs, Gleichgewichte, LPs
oder Optimierungsaufrufe. `qualification_pass=true`, aber `search_allowed`,
`field_pass`, `transfer_pass` und `step4_pass` bleiben false.

Originaler Lauf: `artifacts/coil-perturbation-v1/run.json`, SHA256
`ce895f482e49d36d323c7c08bd2e004356cc2626005bc1cb0f85e44875e6afe6`.
[Vollständiger unabhängiger Audit](../../evidence/coil-perturbation-v1-audit.json),
SHA256 `9f8fd9a0c4ca1f93baa3b8896f803e1f1a3a6ae8cd409517abe5a24fda98c7e8`.
Die großen gebundenen Roharrays bleiben im lokalen Artefaktverzeichnis;
ein Git-Checkout allein enthält sie nicht.

Ein zusätzlicher unabhängiger, ausschließlich lesender Standardbibliotheksreview
bestätigt1371 Referenzen/369.900.527Bytes, alle17 gebundenen Programm-/Test-/
Protokolldateien gegen Git930580e, sämtliche Arbeitspräfixe, alle52 unveränderlichen
Zustandsmarker, beide finalen Worker-/Parentcheckpoints und bytegleiche
Seed-Replay-Arrayinhalte. Die beiden nicht separat referenzierten Quellen-
Spiegeldateien stimmen exakt mit den eingebetteten Originalpayloads überein.
Auch alle vier historischen Feldablehnungen unverändert. Das ist ein zusätzlicher
Quellen-/Buchhaltungsreview, keine weitere Geometrienachrechnung oder externe
wissenschaftliche Begutachtung.
Nach der Ergebnisdokumentation bestehen zusätzlich73 Dokument-/CLI-Kontrollen
in0,92s sowie Repository-Ruff, Struktur- und Diffprüfung; numerische Quellen
und die beiden kanonischen Ergebnisdateien unverändert.

## Bedienung des qualifizierten Gesamtworkflows

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

Ausgeführte Befehle (Pfade stehen exemplarisch für den bestehenden Forschungscheckout):

```bash
PYTHONPATH=src MPLCONFIGDIR=/private/tmp/fusion-mpl-cache OMPI_MCA_btl=self \
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python scripts/run_coil_perturbation.py \
  --raw /Users/sebastianwirkert/workspace/fusion/artifacts/coil-perturbation-v1

PYTHONPATH=src MPLCONFIGDIR=/private/tmp/fusion-mpl-cache OMPI_MCA_btl=self \
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python scripts/audit_coil_perturbation.py \
  --run /Users/sebastianwirkert/workspace/fusion/artifacts/coil-perturbation-v1/run.json \
  --output /Users/sebastianwirkert/workspace/fusion/evidence/coil-perturbation-v1-audit.json
```

Beide Exit0. Vorhandene Ausgabepfade nicht wiederverwenden. Keine erneute
Matrix für einen Bedienungstest; ein späterer gespeicherter Audit braucht
lediglich einen neuen Ausgabepfad und unveränderte gebundene Quellen.
