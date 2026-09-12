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

Noch offen: unabhängiger Studienprüfer für das neue explizite Methodenprofil,
danach zwei physikalische Wiederholungen und alle feinen Abnahmen. Der
unveränderte Recovery-Lauf und dessen Holdouts werden zuvor abgeschlossen und
dokumentiert. Keine neue zulässige Baseline und kein Methodenfortschritt behauptet.
