# Jacobiskalierte AL: analytische Kontrolle, physikalischer Versuch noch offen

Stand 2026-09-12. [Vorabfestlegung](NATURAL_AUGLAG_JAC_PROTOCOL.md), Ausführung
bei `2061cee`. Bericht: `evidence/natural-auglag-jac-control-v1.json`.

Die echte achtstufige Steuerung mit `x_scale=jac` besteht dieselbe analytisch
lösbare beschränkte Quadratik wie der unskalierte Ansatz. Ergebnis
x=(1,0000000046650739; -4,665073823490974e-9), maximale Verletzung
4,665073882748061e-9, letzte Lagrangegradient-Maxnorm
5,551115123125783e-16. Damit bestehen die unveränderten Grenzen von1e-5 für den
Lösungsfehler,1e-8 für die Verletzung und1e-6 für die Stationarität.

13 vollständige analytische Auswertungen,40 Anfragen,27 Cachetreffer, keine
verweigerte oder fehlgeschlagene Auswertung. Alle acht Stufen abgeschlossen;
das sind keine Magnetfeldrechnungen und kein fairer Laufzeitvergleich. Effektive
Solveroptionen, acht verwendete Projektquellen und drei SciPy-Quellen sind im
Bericht hashgebunden. `control_completed` und `qualification_pass=false`
unterscheiden die bestandene Kontrollrechnung von einer qualifizierten
physikalischen Studie. Fünf reine Adapterkontrollen bestehen bereits.

Der separate analytische Audit berechnet Zielfunktion, Randbedingungen,
Lagrangegradient, Multiplikatorvorzeichen und Komplementarität aus x und den
gespeicherten Multiplikatoren neu, ohne den Solver zu importieren. Alle neun
Prüfungen bestehen, einschließlich Quellhashes und Kontrollfall-Abgrenzung:
`evidence/natural-auglag-jac-control-v1-audit.json`. Dies prüft den analytischen
Endpunkt, nicht den gesamten inneren Solverpfad und keine Plasmaphysik.

Der neue separate Studienprüfer übernimmt die unveränderte unabhängige
Stufen-/Budget-/Auswahl-/Feldidentitätsrechnung und verlangt zusätzlich das
registrierte Methodenprofil, alle effektiven Optionen, beide korrekten
Wiederholungsnummern und unveränderte Quellen/Protokoll gegenüber der
Kontrollrechnung. Der ursprüngliche Auditor bleibt bytegleich. 22 reine
Kontrollen prüfen insbesondere die Ablehnung abweichender Optionen, Methoden,
Threads, Koordinatenskalen und falscher analytischer Erfolgsflags.

Der separate Startdriver verlangt jetzt den vollständig gespeicherten und
committeten Recovery-Abschluss, alle vier feinen Berichte mit passenden
Exitcodes, ihre Hashes und die committete Ergebnisdokumentation. Er verweigert
unvollständige, doppelte oder fehlgeschlagene Phasen und Feedbacknutzung;
sieben reine Steuerungskontrollen bestehen. Die neue Suche und ihr Audit laufen
sequenziell unter der2-GiB-Reserve, ohne Änderungen am alten oder neuen Suchkernel.

Die [unveränderte Recovery](NATURAL_AUGLAG_RECOVERY_RESULTS.md) ist nun samt
allen Holdouts abgeschlossen: Geometrie/nativ bestehen, Flux Faktor26,9859 zu
hoch. Nach deren Commit sind zwei neue physikalische Wiederholungen und ihre
feinen Abnahmen der nächste Arbeitsschritt. Keine neue zulässige Baseline und
kein Methodenfortschritt behauptet.
