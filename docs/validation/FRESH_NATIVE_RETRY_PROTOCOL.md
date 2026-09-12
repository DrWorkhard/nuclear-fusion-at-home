# Nativer Neuaufbau: ressourcenbegrenzter Wiederholungsversuch

Vor neuer Ausführung festgelegt, 2026-09-12. Der erste Versuch db6abf5 bleibt als
[Fehlschlag](RESOURCE_INTERRUPTION.md) erhalten. Neue leere Arbeitskopie und neue
Berichtkennung; keine Übernahme alter Solverausgaben, Binärdateien oder Umgebungen.
Physik, Quellpins, Paketlocks, W7-X-Eingabe, Residualgrenzen und strikte sechs
Prüfungen bleiben wie im [ursprünglichen Protokoll](FRESH_NATIVE_INTEGRATION_PROTOCOL.md).

## Geänderte Ressourcensteuerung, nicht geänderte Physik

- Lokale Quell-Clones immer ohne sofortigen Checkout. StellCoilBench wird vor
  dem Checkout auf Root-Metadaten, `src`, `plasma_surfaces` und die beiden
  festgelegten `basic_LandremanPaulQA.yaml`/`basic_W7X.yaml` beschränkt. Keine
  `submissions` oder übrigen großen Fallarchive. Andere Quellrepos bleiben vollständig.
- Beobachteter Bedarf: Quell-Gitobjekte zusammen rund 0,6 GiB, übrige Quelldateien
  deutlich unter 0,3 GiB; bestehende native/VMEC++-Umgebungen rund 1,3 GiB.
  Planungsbudget 3 GiB zusätzlich umfasst geschätzte Build-/Outputkosten; das ist
  eine Schätzung, kein bewiesener oberer Grenzwert. Mindestens 5 GiB frei vor Start.
- Während jeder eigenen Unterprozessphase wird alle 0,5 s eine Reserve von
  2 GiB geprüft, einschließlich Kontrolle nach Prozessende. Unterschreitung:
  eigene Prozessgruppe stoppen, Fehler protokollieren, nicht weitermachen.
  Das schützt nicht gegen beliebig schnelle fremde Schreibvorgänge; freie
  Minimalwerte sind abgetastete Beobachtungen, keine kontinuierlichen Schranken.
- Keine parallele schwere Such-/Installations-/Buildarbeit. Lesende Audits und
  kurze Kernkontrollen sind erlaubt, ohne Geschwindigkeitsaussagen.
- Scheitert ein Abschluss-Checkpoint, bleibt eine ursprüngliche Ausnahme sichtbar;
  vorherige Berichte werden nicht als erfolgreicher Abschluss behandelt.

## Kontrollen vor dem Lauf

Synthetischer Git-Checkout muss Pin und Referenzdateien erhalten, Archive
ausschließen und schmutzige Quelldateien unverändert lassen/nicht kopieren.
Ungültige Pfade und fehlende Platzreserve werden zurückgewiesen. Kontrollierter
Platzverlust stoppt ausschließlich den vom Test selbst erzeugten Unterprozess;
normale Prozessfehler bleiben erhalten. Danach Ruff, gesamte Kernsuite,
Dokumentprüfung und Commit, bevor der neue native Versuch beginnt.

Kein Beweis unabhängiger Hardware, kein frischer SIMSOPT-C++-Build bei Nutzung
eines erlaubten gecachten Wheels, keine globale QI-/Ingenieurqualifikation.
