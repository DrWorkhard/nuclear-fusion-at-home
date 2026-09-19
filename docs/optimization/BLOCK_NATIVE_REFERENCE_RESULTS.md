# Blockweise native Abstandsreferenz: Abschluss

19. September2026. [Vorabprotokoll](BLOCK_NATIVE_REFERENCE_PROTOCOL.md).

Die vollständige vorherige Referenzrechnung ist mathematisch korrekt, überschreitet
aber in drei von vier dichten nativen Fällen den registrierten Speicherrahmen.
Alle vier eigenen Sparse-Fälle bestehen. Dieser Folgeversuch testet eine andere
Ausführung derselben nativen Formel bei unverändert vollständigen Daten und
unveränderten Schirmen. Die alten negativen Entscheidungen bleiben erhalten.

Zwei getrennte unabhängige lesende Agentenreviews bestätigen die gewichtete
Blocksumme beider Kovektoren und den Vergleich aller Zustände mit beiden alten
Backends. Hauptfallen: versehentliche doppelte Mittelung, normalisierte statt
parametrischer Flächennormalen, zurückgehaltene asynchrone JAX-Arrays,
versteckte Ableitungsarbeit auf Wertprobes und unvollständige Mindestabstände.
Viele Kernelstarts können außerdem die unveränderte120-s-Grenze verletzen.

Gewählt: vier neue Block-Native-Worker, keine Kernelcachegutschriften, alle
336 Vergleiche mit den unveränderten alten Gegenstücken. Fehlende Persistenz
während harter Unterbrechung wird als konservativ begrenzte unvollständige Arbeit
ausgewiesen, nicht als null oder exakt vollständig. Kein damaliger Dense-RAM-Fail
wird zum Pass erklärt. Implementierung und vollständige Ressourcenmessung sind
inzwischen unabhängig angenommen; beide Phasen sind unten dokumentiert.

Nach dem Protokollcommit wurden additive native Referenz, Quellenbinder,
begrenzter Runner und unabhängige Annahme synthetisch qualifiziert. Noch keine
Projektfelder, kein Gesamt-Startup oder Schritt4-Abschluss.

## Implementierung vor neuer Ressourcenmessung

Quellenbinder zunächst14 reine Kontrollen bestanden. Zusätzlicher lesender
Smoke-Test auf dem erhaltenen Ressourcenlauf bindet alle435 Referenzen und
reproduziert die acht numerischen Workerprüfungen, die vier Backendvergleiche
und exakt die drei alten Dense-RAM-Fehler. Alte Sparse-/native Quellen und
Versionen stimmen weiter überein. Das ist eine Prüfung gespeicherter Daten,
kein neuer nativer Versuch und noch kein Pass der Blockimplementierung.
Ruff nach Formatierung bestanden; erster Aufruf vor Formatierung meldete eine
überlange Zeile, keine numerische Änderung oder Grenzwertanpassung.

Native Blockklasse:33 kleine synthetische Kontrollen bestanden in3,57s.
Unveränderte native/Sparse-Werte und volle VJPs, beide FD-Schrittweiten,
Symmetrien, ungleiche Kurvenraster, vollständige Blockpartition und Fehlerpfade
einschließlich Synchronisation/Kernel/VJP/Minimum/Dateiausgabe geprüft.
Eine erste Testrunde hatte30 Pass und einen veralteten JAX-Test-API-Aufruf;
auf das lokal vorhandene Kontextmanager-API korrigiert, keine Rechenformel geändert.

Runner:24 reine Mock-/Buchführungskontrollen bestanden in4,78s. Separater
Integrationsreview ergänzt laufende Elternprozessprüfung vor Zuständen und
Kurvenphasen sowie strenge Einbettung der Fortschrittszeiten in die zugehörigen
Aufrufe. Elternverlust stoppt neue Arbeit; letzter erfolgreicher Checkpoint bleibt
unverändert. Producer-Checks dürfen wahr sein, autoritative Annahmeflags bleiben
bis zum separaten Auditor ausdrücklich falsch. Keine tatsächliche Ressourcenmatrix
ausgeführt und keine Pflichtprüfung durch diese kleinen Tests ersetzt.

Der neue unabhängige Auditor bestätigt zusätzlich rein lesend alle104 alten
Rohzustände und acht Oberflächen gegen eigene Fourier-/Normalenrechnung:
maximale Abweichung1,7764e-15 an der Oberfläche,4,4409e-16 an Kurvenpositionen,
8,8818e-16 an Tangenten. Seine vollständige Legacy-Abnahme reproduziert acht
mathematische Pässe und genau die drei alten RAM-Fehler. Neue synthetische
Gesamtworkflow-Prüfung nun bestanden:64 Kontrollen in6,65s, einschließlich
vollständigem komprimiertem8+4-Worker-Datensatz mit Produktionsdimensionen,
336 neuen/168 alten Gegenvergleichen,32 neuen FD-Prüfungen, Arbeits-/Zeit-/
Quellen-/Wiederholungs-/RAM-Mutationen und CLI-Ausgabe. Fixture einmal pro Modul,
keine mehrfachen großen Rohkopien je Negativfall. Spätere reine Änderungen an
Git-Metadaten verhindern keine erneute gespeicherte Abnahme; sämtliche
numerischen Quelldaten bleiben dabei exakt gebunden. Die gemeinsame abschließende
Regression besteht vor Codecommit und erster neuer Vier-Zellen-Messung:
**1470 Tests,334 bekannte Warnungen, keine Fehler oder Skips,177,31s.**
135 neue Kontrollen gegenüber dem letzten Stand (33/14/24/64).
Repository-Ruff, Dokumentstruktur und Diffprüfung bestanden. Quellhashes und
JUnit-Bericht: [Qualifikationsbeleg](../../evidence/block-native-reference-v1-qualification.json).

## Tatsächliche Vier-Zellen-Matrix und unabhängige Abnahme

Sauberer Codecommit3349ce5, vier neue Prozesse seriell mit einem Thread.
Quellzustand vor/nach dem Gesamtlauf exakt identisch. Alle52 Zustände vollständig,
104 öffentliche Werte-,40 Gradienten- und24 Mindestabstandsrequests abgeschlossen.
Keine neuen Projektfelder oder Gleichgewichte.

| Fall | Elternzeit [s] | Peak-RSS [Bytes] | Peak-RSS [GiB] | Rechnung/Ressourcen |
| --- | ---: | ---: | ---: | --- |
| n6 /256 |16,2870|408633344|0,38057|Pass|
| n6 /512 |26,4611|448626688|0,41782|Pass|
| n8 /256 |21,3985|406470656|0,37856|Pass|
| n8 /512 |38,1855|458391552|0,42691|Pass|

Unverändert120s und1,5GiB je frischem Worker. Gemessener Gesamtprozesspeak,
einschließlich Importen/JAX/CC; keine isolierte CP-Zeit oder statistisch wiederholte
Leistungsmessung. Neue Rohdaten28.701.721Bytes, kleinster beobachteter freier
Platz9.269.567.488Bytes. Keine Installation oder Rasterverkleinerung.

Separater CLI-Auditor prüft659 Referenzdateien, alle336 Gegenvergleiche mit
**beiden** alten Backends,32 eigene zentrale FD-Kontrollen, zwölf exakte
Wiederholungs-/Restorepaare und sämtliche Arbeits-/Geometrie-/Quellprüfungen.
Alle bestehen. Größte CP-Wertabweichung4,2284e-18, Gradient6,5053e-19;
CC und Mindestabstände exakt gleich. Maximaler FD-Absolutfehler1,7141e-11,
Relativfehler4,8206e-8. Keine Grenzwertänderung.

Genau93.184 native CP-Wertkerne, je35.840 Positions-/Tangentenkerne,
21.504 vollständige Abstandsblöcke und je560 native Kurven-VJPs abgeschlossen.
Alle Versuchszähler gleich Abschlusszählern, keine Cachegutschriften.
Die vier alten Sparse-Pässe und168 alten Paarvergleiche werden erneut geprüft;
die drei alten Dense-RAM-Fehler und`legacy_all_pass:false` bleiben erhalten.

Autoritative Entscheidung: **`bounded_reference_pass:true`**. Der Producer
belässt seine Abnahmeflags absichtlich auf false/pending; dessen positives
`producer_checks_pass` ersetzt den separaten Auditor nicht. `startup_pass`,
`physical_seed_pass`, `search_allowed`, `transfer_pass`, `step4_pass` bleiben false.

Belege: [byteidentische Laufkopie](../../evidence/block-native-reference-v1-resource.json)
(SHA256`8f6f37e90d2e76705727899753f369b242cb48c14a7fc2328f2beba6b511bece`),
[unabhängige Abnahme](../../evidence/block-native-reference-v1-audit.json)
(SHA256`5070d7df72e54edf4433df72af193f611c5605286895aebeb442d09d1e620f65`).
Originaldaten:`artifacts/block-native-reference-v1-resource/`.

Zusätzlicher unabhängiger Agentenreview rechnet ohne Projektimporte oder native
Aufrufe alle659 Hashbindungen,336 Vergleiche,32 FD, zwölf Wiederholungen und
2352 Reservierungen/4704 Ereignisse nach: keine Gegenbefunde. Dies ist kein
externer Peer-Review. Zweiter CLI-Replay nach ausschließlich dokumentarischen
Änderungen liefert sämtliche Berichtsfelder exakt identisch, außer dem aktuellen
Git-Metadatenfeld des Auditors. Erhalten als
`artifacts/block-native-reference-v1-reaudit.json`, SHA256
`a3b3204527ca8bfb20a5b4c8b9fcff0dec46bf21b60a9f9650f47658cec85beb`.
Neun Dokumenttests, Repository-Ruff, Struktur und Diff erneut bestanden;
keine numerische Quelle seit der1470-Test-Qualifikation geändert.

Nächster Schritt: den getrennt registrierten Gesamtworkflow der
[Feldstartstudie](CLEAR_COIL_FIELD_START_PROTOCOL.md) implementieren und synthetisch
qualifizieren. Seine Quellenbindung muss diese neue Annahme UND die unveränderte
negative Vorgängermessung bewahren. Erst danach vier tatsächliche Feldstartzellen;
kein direkter Suchlauf und kein Schritt4-Abschluss aus der Ressourcenprüfung.
