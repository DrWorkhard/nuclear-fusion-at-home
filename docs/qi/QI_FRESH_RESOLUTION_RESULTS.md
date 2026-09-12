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

Noch kein Ergebnis der neuen Gleichgewichte oder Feld-/Driftfreigabe. Nächster
Schritt: alle16 Kaltstarts ausführen, neue Wouts separat auswerten/auditieren.
