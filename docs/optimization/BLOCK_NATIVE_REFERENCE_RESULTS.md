# Blockweise native Abstandsreferenz: Arbeitsstand

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
wird zum Pass erklärt. Die Implementierungsqualifikation ist unten dokumentiert;
die neue vollständige Ressourcenmessung steht noch aus.

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

Nach diesem Codecommit folgen vier frische Ressourcenprozesse und separat die
unabhängige Abnahme. Bis dahin kein`bounded_reference_pass` und keine Freigabe
für tatsächliche Projekt-Feldstarts. Alle Originaldateien bleiben unverändert.
