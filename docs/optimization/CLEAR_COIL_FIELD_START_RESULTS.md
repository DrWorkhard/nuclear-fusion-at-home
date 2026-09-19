# Feldstarts aus geometrisch angenommenen Konturen: numerischer Abschluss

19. September2026. [Protokoll](CLEAR_COIL_FIELD_START_PROTOCOL.md).

**Alle vier tatsächlichen Feldstarts bestehen die vollständige unabhängige
numerische Abnahme; keine der vier Startformen besteht die physische Zulassung.**
Der saubere Codecommit7b1a501 rechnet beide Plasmaformen mit den exakt ausgewählten
n6/n8-shape-d100mm-Geometrien. Acht N/V-Ableitungsschirme, alle20 Verfeinerungen,
768 direkte Einzel-B/A-Vergleiche und252 Flussgates bestehen. Geometrie und Strom
bleiben zulässig, Normal-/Innenfeldfehler viel zu groß. Keine Suche, kein neues
Gleichgewicht, keine Transfer- oder Schritt4-Annahme. Als Nächstes einen eigenen
begrenzten Feldfit mit Schutz der jetzt sicheren Geometrie registrieren.

Die vorherige Geometrieabnahme bei323cfdd und separate positive
[block-native Ressourcenqualifikation](BLOCK_NATIVE_REFERENCE_RESULTS.md)
bleiben Quellen. Die drei ursprünglichen dichten Speicherfehler bleiben negativ.
Implementierung vor Feldsichtung:1640 Gesamttests,334 bekannte Warnungen.

## Vier reale Zellen und unabhängige Abnahme

Alle vier frischen Worker schließen mit exaktem Exit0 ab; Quellen vor/nach
identisch bei sauberem7b1a501. Elternzeiten30,064/35,139/30,040/34,657s gegenüber
1800s je Zelle. Kleinste beobachtete Plattenreserve9.083.727.872Bytes,
Rohdaten167.519.469Bytes. Ein Thread, keine schweren parallelen Projektjobs.
Keine allgemeine Leistungsrangfolge aus diesen Einzelmessungen.

Je Zelle zehn tatsächlich initialisierte Modelle,44 gespeicherte Operationen,
262 vollständige native Requests mit524 Attempt-/Completed-Ereignissen.
Gesamt80 Vollbundles,24 Diagnosen,72 Flussraster,40 Initialisierungen,
**1048 Requests =808 Werte +240 VJPs**. Auch Zusatzpotentiale/Initialisierungen
und wiederholte Punkte zählen, ohne Cachegutschriften. Producerstatus ist nur
vollständig/pending; numerische und physische Entscheidung stammen vom Auditor.

Der getrennte CLI-Auditor bindet2434 Referenzdateien und rekonstruiert96 B/A-Paare
je Zelle auf jeweils64 Punkten (384 Paare/768 Einzelvergleiche insgesamt).
Maximaler relativer Komponentenfehler5,2942e-15 gegenüber5e-10. Alle32
Richtungs-/Schrittweitenchecks bestehen sowohl mit aufgezeichneten als auch
eigenständig rekonstruierten J-Werten (64 numerische Vergleiche): maximal
2,5941e-11 absolut/1,4486e-9 relativ. Alle acht Startwiederholungen exakt;
N/V-Felder, physische Ströme und B² jeweils identisch.

Alle20 vorab festgelegten Rasterverfeinerungen bestehen; größter relativer
Unterschied0,019508% gegenüber1%, absolut7,0533e-5 beim inneren Vektor-RMS.
Alle252 Flussgates bestehen (216 blockinterne plus36 Spulenrastervergleiche),
maximaler relativer Fehler8,8349e-16 gegenüber1e-6. Signierte Linien-/Fanflächen,
Radial- und alle drei Winkelpaare eingeschlossen. Auf keiner feinen Stufe neu
normiert; unveränderter Strom aus dem ursprünglichen N0-Snapshot.

| Ziel / Grundspulen | Normal-RMS, Stufe3 | Normal-Max, Stufe3 | Innenvektor-RMS, Stufe5 | Strom (kA) |
| --- | ---: | ---: | ---: | ---: |
| Referenz /6 |0,2760512695|0,5980210929|0,3712379826|294,9665|
| Referenz /8 |0,2691494984|0,6014775212|0,3615001893|216,6287|
| Schritt3-Entwurf /6 |0,2761091852|0,5979237991|0,3722297176|295,6837|
| Schritt3-Entwurf /8 |0,2692089667|0,6016319166|0,3623789334|217,1572|
| Unveränderte Grenze |0,0001|0,001|0,01|500|

Stufe3:128² Rand,512 Spulenpunkte, halbe Zelle versetzt; Stufe5:64² innere
Targets bei512 Spulenpunkten. Physische Entscheidung prüft trotzdem **alle sechs**
Stufen, nicht nur diese Tabelle. Alle vier Formen verfehlen ausschließlich
die drei Feldfehlerkriterien; Strom, Längen, Krümmung, Spulen-/Plasmaabstand und
numerischer Startup bestehen. Die Gitterminima im Plasmaabstand liegen bei
130,350–130,542mm; die unveränderten strengeren kontinuierlichen Seed-Zertifikate
garantieren mindestens98,214mm. Gitterminimum ist nicht kontinuierliche Untergrenze.

Das schließt die numerische Startstudie, nicht Schritt4A. Fehlerfaktor beim
Normal-RMS rund2691–2761, beim inneren Vektor36,15–37,22. Die etwas günstigeren
n8-Werte sind nur Startdiagnostik: kein fairer Optimierungssieg, keine neue
zulässige Baseline und kein Gegenbeweis zur Realisierbarkeit der Plasmen.
Alle Such-/Transfer-/Schritt4-Flags bleiben ausdrücklich false. Nach diesem
Ergebniscommit erst über einen neuen begrenzten Suchversuch entscheiden.

Belege: [bytegleicher vollständiger Laufspiegel](../../evidence/clear-coil-field-start-v1-run.json),
SHA256`e4949a9be9518c9acaa727c3f6de238703028e9baca16bf89ec15bb145cb9714`;
[eigenständiger Gesamtaudit](../../evidence/clear-coil-field-start-v1-audit.json),
SHA256`e6fa7cda853cc2576f9660501043fc6f8c0d7121c1ce0a819df47544fd262fd8`.
Die Rohdateien bleiben unter`artifacts/clear-coil-field-start-v1` unverändert.

Zusätzlicher unabhängiger lesender Agent prüft ausschließlich mit Standardbibliothek
alle2434 Referenzen/385.333.037Bytes, Codebytes gegen Git7b1a501, Quellenzeiten,
sämtliche Modell-/Operations-/Feldpräfixe und eingefrorene feine Normierung.
Alle oben genannten Arbeitszahlen und exakten N/V-/Startwiederholungen bestätigt;
sechs alte negative Coilaudits bytegleich zu4f3c2fa, drei alte RAM-Fehler erhalten.
Keine neue Feld-/Geometrierechnung für diesen Buchhaltungs-/Provenienzreview;
er ergänzt die getrennte wissenschaftliche CLI-Abnahme, ersetzt sie nicht.
Erneuter gespeicherter CLI-Audit nach reinen Dokumentänderungen reproduziert
alle Berichtsfelder exakt bis auf den aktuellen Git-Metadatensatz des Auditors.
Replay unter`artifacts/clear-coil-field-start-v1-reaudit.json`, SHA256
`612026341222cae4d009af020530fe124c43341fc997acf41abf754ce72472e6`.
Neun Dokumenttests, Repository-Ruff, Struktur- und Diffprüfung erneut bestanden.
Keine numerischen Codeänderungen seit dem1640-Test-Stand; Ergebnis lokal sichern.

**Dokumentarisches Erratum, keine nachträgliche Laufänderung:** Im historischen
[Softwarequalifikationsbeleg](../../evidence/clear-coil-field-start-v1-workflow.json)
steht unter`saved_predecessor_replay.reference_and_selected_target_flux` versehentlich
−0,031415926535897934Wb (−Python-π/100). Beide gebundenen Inputs und sämtliche
tatsächlichen N0-Snapshots enthalten korrekt−0,03141592653589793Wb. Differenz
−6,938893903907228e-18Wb, exakt eine ULP. Das zusammenfassende Metadatum wird
nirgends als Recheneingabe benutzt; quellgebundene Laufnormierung und Abnahme
sind unverändert richtig. Unabhängiger lesender Review bestätigt dies; der
historische Beleg bleibt mit diesem additiven Erratum erhalten.

## Erhaltene Implementierungsgeschichte vor neuen Projektfeldern

Nach positivem Ressourcenabschluss bei1b6f6b1 folgt der additive Quellenbinder,
begrenzte Ausführungslauf und eigenständige Gesamtauditor. Zwei getrennte Agenten
implementieren Ausführung beziehungsweise Abnahme; ein weiterer lesender Review
prüft die Integration. Keine alten Rechenkerne oder quellengebundenen Protokolle
ändern. Zu diesem Implementierungszeitpunkt gab es noch keine neuen Feldwerte;
der inzwischen ausgeführte Versuch steht oben.

Vor Codefreeze und erster neuer Feldsichtung wird die im Protokoll geforderte
Winkelprüfung explizit festgelegt: **alle drei Paare256→512,512→1024,256→1024**
für die Randlinie sowie jede der beiden radialen Fanreihen. Dazu je Spulenraster
drei Radial16→32-Paare, neun Zielflussfehler, sechs Stokes-Vergleiche und zwischen
Spulen256/512 neun korrespondierende Flüsse. Grenze überall unverändert1e-6.
Die ursprünglichen Protokollbytes und alten negativen Ergebnisse bleiben erhalten.

API-Vorabreview bestätigt die vollständige native Arbeit je physischer Zelle:
zwei Qualifikationsmodelle mit je1+10×9=91 Requests, sechs Diagnosemodelle mit
je1+6=7 und zwei Flussmodelle mit je1+18=19; insgesamt262, davon202 Werte und
60 VJPs, einschließlich zehn initialen A-Aufrufen. Vier Zellen also1048 native
Requests. Zusätzliche unabhängige direkte B/A-Paarrekonstruktionen96 je Zelle
sind gesonderte Prüfarbeit, keine nativen Produceraufrufe. Kein Cachebonus.

Wichtige Integrationsschutzregeln: Diagnosearrays explizit mit dem eingefrorenen
Strom aus N0 und festem B² abrufen; kein späterer neu normierter Snapshot.
Direkte B/A-Prüfung streng relativ≤5e-10 mit positivem Nenner, kein absoluter
Toleranzausweg. Alter Flusswrapper erzeugt eine ungezählte BiotSavart-Instanz und
falsche128/512-Raster; deshalb ausschließlich seinen reinen signierten
Geometriehelper übernehmen. Elternwächter muss1800s selbst erzwingen, auch über
Imports/Quellenbinder/Konstruktoren. Persistierte Modellversuche vor erstem Feldaufruf.

Quellenbinder zunächst41 reine Kontrollen bestanden. Lesender realer
Vorgänger-Smoke bindet beide exakten ausgewählten Snapshots, alle zwölf positiven
Geometriesätze/168 LPs und die separate Blockreferenz samt drei alten RAM-Fehlern.
Acht tatsächlich installierte native Python-Dateien stimmen bytegleich mit den
gebundenen Checkoutquellen überein; kein universeller transitiver ABI-Nachweis.
Kanonisches archiviertes B²: Referenz1,6293829620247962T²,
Entwurf1,6313464444829588T². Keine neue Feldrechnung dafür; vollständiger
Workflowtest und Codecommit bleiben vor realem Startup erforderlich.

Nach Quellenreview44 Binderkontrollen: drei zusätzliche Tests sichern verknüpfte
JSON→Rohdaten, einmalige Graphausweitung und historische Versionsgrenzen.
Die zunächst nur flache Referenzprüfung hätte beschädigte neue Block-Workerdateien
übersehen. Vollständige aktuelle Rohgraphen sind nun gebunden. Ein zuerst zu weit
reichender Replay beliebiger historischer Quellberichte verlangte dagegen eine
alte Version von`measure_radial_action.py` am heutigen Pfad und wurde abgelehnt.
Korrekte Grenze: eingebettete Quellreferenzen weiter hashen, vergangene
Metadataberichte ihren bereits qualifizierten Quellenbindern überlassen, aktuelle
Raw-JSON-Ketten vollständig öffnen. Kein Ausnahmehash für eine geänderte Datei.
Der reale lesende Vorgängercheck besteht danach. Separat bestätigt der neue
Auditor aus beiden vorhandenen Archiven die obigen B²-Werte und Zielfluss−π/100Wb.
Kein neuer Feld- oder Gleichgewichtsaufruf für diese Nachprüfungen.

Lesender Nachreview bestätigt die geschlossene Rohdatenlücke:986 Referenzen im
Geometriegraph,660 im Blockgraph einschließlich aller56 neuen NPZ-Dateien.
Auch der neue Auditor bindet zusammen1648 Dateien und bestätigt beide Targets
ohne neue Feldrechnung. Überschneidungen der Graphen werden dabei berücksichtigt;
die genannten Zählungen haben unterschiedliche Einstiegspunkte.

Producer/Workflowtests zunächst19 Pass in1,48s mit einem bekannten netCDF-
Importhinweis. Zehn Konstruktoren,44 Operationen und262 Feldrequests über echte
CountedField-Ereignisse an einem Fake-Backend vollständig durchlaufen; falsche
Aufrufreihenfolge, Zusatzrequests, Elternverlust, verspätete Ausgabe und Fehler
werden gezielt geprüft. Ein Review korrigiert die Verwendung des alten starren
Drei-Feld-Referenzschemas für historische Zwei-Feld-Inputreferenzen, bevor ein
Projektfeld versucht wurde. Lokale/gesamte Arbeitslimits nun vor Dispatch, nicht
nur nachträglich kontrolliert. Anfangs fehlender Testimport ergänzt; Ruff/Syntax/
Diff danach bestanden. Producer-Dateien eingefroren, Gesamtabnahme noch in Prüfung.

Echte Mock-Producerdateien gehen anschließend durch den unabhängigen Ledger- und
Prozessauditor. Dabei Scope-/Flussmetadaten vereinheitlicht; zusätzliche unabhängige
Feldkennzahlen werden im Auditor erhalten, aber nicht irrtümlich vom Producer-
Schema verlangt. Vollständige Zellen-/Gesamtworkflow-/CLI-Kontrollen folgen vor
gemeinsamer Regression und Freigabe. Ein bestandener Mockworkflow ist kein
Projektfeld-Startup oder physischer Entwurfspass.

Die erste komplette Auditorrunde besteht90 Tests in8,21s (ein bekannter
Importhinweis), einschließlich tatsächlichem Vier-Zellen-Mockproducer bis CLI
und unverändert negativem physischen Seed. Teure innere Feldmathematik und
historische Vorbedingungen sind in diesem reinen Wiringtest ausdrücklich
kontrolliert ersetzt; ihre mathematischen Prüfungen laufen separat.

**Vor erster neuer Feldrechnung gefundene Protokollabweichung:** Die eingefrorene
Klasse rekonstruiert innere Zielwerte aus dem Wout; nahe Übereinstimmung innerhalb
5e-12 ist nicht das verlangte exakte Archiv-Subsampling. Zwei lesende Reviews
bestätigen die Korrektur im additiven Runner: unmittelbar nach dem einzigen
Konstruktor-Loop-A-Aufruf und vor jedem inneren Feldaufruf archivierte64²-Werte
eigenständig rekonstruieren/subsamplen, Wout-Replay vergleichen und unabhängige
aktive Kopien einsetzen. B² und Zielflussvorzeichen bleiben unverändert.
Der Gesamtauditor verlangt anschließend exakte Gleichheit der gespeicherten
Innenpunkte/Zielfelder mit seiner eigenen Archivrechnung. Alte Klasse/Protokolle
bleiben eingefroren. Abschließende Teilqualifikation:44 Binder-,32 Runner- und
94 Auditorprüfungen bestanden. Positive32/64-Fälle bestätigen exakte unabhängige
C-Kopien ohne zusätzliche Feldrequests; negative Fälle sichern falsche Quellen,
Vorzeichen, B², vorhandene Caches und fehlerhafte Initialisierung. Insbesondere
wird auch ein falsches Vorzeichen an einem im32er Subsampling ausgelassenen
64er Knoten erkannt. Der Auditor weist selbst1e-14-Abweichungen an inneren
Punkten/Zielfeldern ab. Letzter unabhängiger lesender Review bestätigt den Fix
ohne weitere Befunde. Gesamte Regression: **1640 Pass,334 bekannte Warnungen,
keine Fehler/Skips,191,33s**. Ruff, Dokumentstruktur und Diffprüfung bestanden.
[Qualifikationsbeleg](../../evidence/clear-coil-field-start-v1-workflow.json)
bindet alle sechs neuen Code-/Testdateien, unverändertes Protokoll und JUnit.
Vor dem echten Lauf folgt der lokale Codecommit; keinerlei neue native
Projekt-Feldaufrufe oder Gleichgewichte in dieser Implementierungsphase.

Nach sauberem Commit ausführen, mit jeweils frischer absoluter Ausgabe:

```bash
PYTHONPATH=src MPLCONFIGDIR=/private/tmp/fusion-mpl-cache OMPI_MCA_btl=self \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python scripts/run_clear_coil_field_start.py --raw /ABSOLUTER/NEUER/RAWORDNER

PYTHONPATH=src MPLCONFIGDIR=/private/tmp/fusion-mpl-cache OMPI_MCA_btl=self \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python scripts/audit_clear_coil_field_start.py \
  --run /ABSOLUTER/NEUER/RAWORDNER/run.json --output /ABSOLUTER/NEUER/AUDIT.json
```

Während des kontrollierten Laufs weder Quellen noch Gitstand ändern und keine
schweren parallelen Projektjobs starten. Der Auditor trennt vollständige
Arithmetik-/Quellenprüfung, numerischen Startup und physische Seedannahme.
Keine Suche oder Schritt4-Freigabe durch diese Studie.

## Erhaltene Vorabreviews und Bausteinqualifikation

Zwei getrennte lesende Agentenreviews identifizieren dieselben Integrationsfallen:
der alte Konstruktor legt Startkoeffizienten und Flussorientierung bereits an
seinen Kreisen fest; seine Geometriefläche bleibt hart64×32. Auch Gesamtprüfung,
Initialisierungszählung und Flussraster sind nicht durch Umetikettieren übertragbar.
Deshalb additive Klasse mit echtem Geometrieseed vor dem ersten Feldaufruf,
neuem Binder/Workflow/Gesamtaudit und unveränderten alten numerischen Dateien.

Gewählt wird die begrenzte Sechs-Stufen-Prüfung je vier physischer Zellen;
N/V erhalten getrennte zehnteilige Ableitungsqualifikation. Ein Vorschlag für
Innenraster128² bleibt bewusst außerhalb: dafür fehlt hier ein entsprechend
qualifiziertes Targetarchiv. Kein stiller neuer QI-Qualifikationszweig. Beide
Reviewer bestätigen den engeren Startupumfang; spätere Suchpunkte brauchen
ihre eigene feinere unabhängige Abnahme. Strom und archivierter64²-B²-Maßstab
bleiben während sämtlicher Auflösungsprüfungen fest.

Native aktive CP-Strafen erzeugen dichte Paararrays. Schon256×128² benötigt
etwa101MB nur für Differenzkoordinaten einer aktiven Kurve, zuzüglich Distanz,
Gewicht und Ableitungstemporaries; sichere Starts würden diesen Pfad auslassen.
Ein mathematisch identischer KDTree-/punktweise ausgewerteter Adapter begrenzt
den Speicher. Vor Einsatz vollständige aktive24/32-Spulen-Kontrollen bei beiden
registrierten Spulenauflösungen, einschließlich nativer Werte/VJPs, Differenzen,
Peak-Speicher und Zeit. Der zusätzliche algebraische Review bestätigt beide
Kovektoren ohne Faktor1/2 oder Symmetriedivisor. Flächengewicht muss der Betrag
der unnormierten nativen Parameternormalen sein, nicht unitnormal oder auf Summe1
normiertes Gewicht; Nenner je KurveN_curve*N_surface. Dieser rohe Integralterm
hat wie die native Implementierung die SI-Dimensionm^5, bevor die festgehaltenen
Strafgewichte angewandt werden. Synthetische Implementierungsprüfung bleibt nötig.
Reviewpräzisierung vor Code: nur den Suchradius konservativ polstern, danach
den ursprünglichen Hinge exakt anwenden; deterministische Nachbarreihenfolge,
unveränderliche feste Flächendaten und vollständiger Mindestabstand auch bei
Nullstrafe. Keine fehlenden Flächenableitungen als Co-Designgradient ausgeben.

Nächster Schritt nach Protokoll-Commit: additive Implementierung und synthetische
Qualifikation. Noch kein neuer Start numerisch angenommen oder Feldfit gestartet.

## Implementierung vor Targetdaten

Erste15 synthetische Sparse-CP-Kontrollen bestehen in2,09s: aktive native
Werte/VJPs, beide zentralen Schrittweiten, Symmetriekopien, verschiedene
Spulenquadraturgrößen, Cacheinvalidierung bei Basisänderung, feste unnormierte
Flächengewichte, echter Mindestabstand bei Nullstrafe sowie ungültige/degenerierte
und cutoff-nahe Daten. Ruff besteht. Das ersetzt noch nicht die vollständige
128²-Ressourcenmatrix und keinen magnetischen Startupnachweis.

Vor deren erster Ausführung präzisiert: acht frische Prozesse, native und Sparse
getrennt für beide Klassen/Spulenauflösungen. Je13 festgelegte Zustände inklusive
voller Gradienten an fünf Kontrollzuständen, acht zentraler Wertprobes und
Cache-/Wiederherstellungskontrollen. Kanonischer B²-Zahlenweg explizit auf
rekonstruiertes(bt*et+bp*ep) der gebundenen64²-Archive festgelegt; keine strikte
Gleichheit unterschiedlicher Summationswege voraussetzen. Diese Präzisierungen
liegen vor der Ressourcenmatrix und vor neuen Projekt-Feldwerten.

Die übrigen Bausteine sind separat implementiert: frischer benannter Feldadapter
(40 erste Kontrollen), unabhängige Archiv-/Geometrie-/Zielfunktions-/FD- und
Auflösungsrechnung (64 Kontrollen) sowie Ressourcen-Elternwächter und genaue
Arbeitsbuchhaltung (43 leichte Kontrollen). Die erste gesamte Regression besteht
mit1334 Tests,334 unveränderten Warnungen in163,11s. Sie ersetzt ausdrücklich
nicht die acht separaten großformatigen Ressourcenläufe. Deren Aufrufe werden
nicht versteckt als gewöhnliche Unit-Tests oder übersprungene Pflichtprüfungen
behandelt.

Ein zusätzlicher unabhängiger lesender Review findet einen echten
Provenienz-Alias: der geerbte magnetische Snapshot teilt seine `sources` mit dem
internen Target. Die additive Klasse isoliert diese Rückgabe nun; ein eigener
Mutationstest belegt unveränderte Modell-/Seedquellen ohne zusätzliche native
Aufrufe. Alle41 Adaptertests bestehen nach der Korrektur in8,99s. Alte numerische
Klassen bleiben unverändert. Der erste1334-Testbericht bleibt als Zwischenstand
erhalten. Die abschließende gesamte Regression nach der Korrektur besteht:
**1335 Tests,334 Warnungen, keine Fehler oder Skips,164,25s.** Gegenüber dem
Geometrieabschluss sind163 Bausteinkontrollen hinzugekommen (15/41/64/43).
Ruff im gesamten Repository, Dokumentstruktur und Diffprüfung bestehen.
Quellenhashes und beide JUnit-Berichte stehen im
[Qualifikationsbeleg](../../evidence/clear-coil-field-start-v1-primitives.json).

Danach bei sauberem Codecommit`a5a007c` separat ausgeführter Befehl
(hier mit Platzhalter für einen frischen absoluten Ausgabeordner):

```bash
PYTHONPATH=src MPLCONFIGDIR=/private/tmp/fusion-mpl-cache OMPI_MCA_btl=self \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python scripts/qualify_sparse_coil_surface.py \
  --raw /ABSOLUTER/FRISCHER/RESSOURCENORDNER
```

Ergebnisse dieser Matrix stehen unten; weder die Testzahl noch die lesenden
Reviews ersetzen sie. Keine neuen Projekt-Feldwerte oder VMEC-Aufrufe in dieser Phase.

Zum damaligen Bausteinabschluss war der Gesamtworkflow noch **nicht** implementiert
oder qualifiziert (aktueller Stand oben). Sein separater Entwurf zählt zehn Modelle je physischer Zelle: zwei Qualifikationen,
sechs Diagnosen, zwei Flussmodelle. Vollständig ergibt das262 native Requests
je Zelle (202 Werte einschließlich zehn Initialisierungs-A,60 VJPs),1048 für
die ganze Matrix. Jedes rohe Ergebnis und jeder begonnene Aufruf wird gebunden;
Diagnosen und Flussblöcke verwenden unverändert den ersten N-Seed-Snapshot.
Radial-, Winkel- und Spulenverfeinerung sind direkte Paarprüfungen, nicht nur
Vergleiche aller Ergebnisse mit einem einzigen feinsten Wert. Diese Präzisierung
ist eine Implementierungsanforderung vor ersten Projekt-Feldwerten, kein Pass.

## Vollständige Ressourcenmatrix: mathematischer Pass, Gesamtgate negativ

Alle acht frischen Prozesse schließen mit Exit0 und unveränderten Quellen ab;
alle104 Zustände,208 J-Anfragen,80 vollständigen Gradienten und48 Mindestabstände
sind erhalten. Alle64 FD-Prüfungen,24 exakten Wiederholungs-/Wiederherstellungspaare,
acht Symmetrie-/Cachekontrollen und168 direkten Backendvergleiche bestehen.
Größte absolute Differenz beim CP-Wert5,3669e-18, beim CP-Gradienten4,3369e-19;
größter FD-Absolutfehler1,7141e-11. Dies sind diskrete synthetische Tests,
keine neue geometrische oder magnetische Entwurfsannahme.

| Grundspulen / Quadratur | Native Zeit (s) | Sparse Zeit (s) | Native Peak (GiB) | Sparse Peak (GiB) | Unverändertes Ressourcenpaar |
| --- | ---: | ---: | ---: | ---: | --- |
| 6 /256 |18,340|9,693|1,4233|0,4742|bestanden|
| 6 /512 |40,252|18,341|2,1945|0,3926|**abgelehnt: native RAM**|
| 8 /256 |23,934|13,262|1,5237|0,4014|**abgelehnt: native RAM**|
| 8 /512 |50,442|27,523|1,8765|0,4070|**abgelehnt: native RAM**|

Zeit ist beobachtete Elternprozess-Wandzeit, Peak der gesamte jeweilige Worker
einschließlich Imports/JAX/CC, nicht isolierter CP-Speicher. Ein Durchlauf je Zelle
belegt keine statistisch abgesicherte allgemeine Leistungsrangfolge. Alle Zeiten
liegen unter120s; drei native Peaks überschreiten1,5GiB. Der Schirm war eine
nachträglich gemessene Qualifikationsgrenze, kein hartes OS-Speicherlimit.
Kleinste beobachtete Plattenreserve8.765.624.320Bytes; neue Rohdaten rund42MiB.

Der [vollständige Ergebnisbeleg](../../evidence/clear-coil-field-start-v1-resource.json)
ist bytegleich mit dem rohen`run.json` (SHA256`5c77723ee9f77de7a4b176de3a69f06ccc6af6d22ad7a4572c2c631ea013acdf`).
**`all_pass:false` bleibt unverändert.** Die vier Sparse-Ressourcenpässe und alle
mathematischen Gegenrechnungen berechtigen nicht, die ausdrücklich strengere
Gesamtanforderung stillschweigend aufzuheben oder Projekt-Feldwerte zu starten.

Als nächste methodische Option wurde die gleiche native Referenzformel blockweise
über sämtliche Oberflächenpunkte gewählt, ohne Punkte, Spulen, Ableitungen oder
Grenzen zu reduzieren. Das separate Protokoll, die synthetische Prüfung und
der Vergleich mit beiden erhaltenen Backends sind inzwischen
[positiv abgeschlossen](BLOCK_NATIVE_REFERENCE_RESULTS.md). Die drei dichten
Speicherfehlschläge bleiben erhalten; die Feldstart-Gesamtqualifikation steht oben.

Eine zusätzliche unabhängige lesende Nachrechnung bestätigt435 eindeutige
Referenzhashes/Dateigrößen, alle104 Zustände und Arbeitspräfixe,64 FD-Prüfungen,
24 Wiederholungspaare sowie168 Backendvergleiche. Größter relativer FD-Fehler
4,9101e-8; alle Prozesscodes und Zeiten korrekt. Die negative Gesamtklasse folgt
ausschließlich aus den drei genannten Speicherüberschreitungen. Kein neuer
nativer Aufruf für diesen Review; unabhängige Agentenprüfung, keine externe
wissenschaftliche Peer-Review. Nach Dokumentation erneut neun Dokumenttests,
Repository-Ruff, Struktur- und Diffprüfung bestanden; Code unverändert zur
1335-Test-Qualifikation. Der getestete Stand wird lokal committed.
