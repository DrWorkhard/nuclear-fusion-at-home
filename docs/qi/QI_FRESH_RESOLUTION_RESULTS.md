# Frische QI-Auflösung: Implementierung und laufende Bilanz

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
