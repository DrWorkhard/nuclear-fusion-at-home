# Lokale Diagnostik am Ableitungsgate gestoppt — 2026-09-11

Protokoll/Implementierung d0f0b8d. Evidenz:
`evidence/direct-descent-diagnostic-v1.json`. Ergebnis: **nicht qualifiziert**;
kein nichtlinearer Abstiegs-Testschritt wurde ausgeführt. Der analytische
zweidimensionale LP-Kontrollfall besteht. Beide eingefrorenen 138-Zeilen-Vektoren
und das gespeicherte Kandidatenfeld lassen sich korrekt wiederherstellen.

Die neue Seed-47-Prüfung am ausgewählten Kandidaten ergibt maximale normierte
Richtungsfehler von 3.4282e-5, 3.4251e-7, 1.0360e-7 und 1.2070e-6 bei
eps=1e-5,1e-6,1e-7,1e-8. Der vorgeschriebene feinste Schritt überschreitet 1e-6.
Der kleinere Fehler bei eps=1e-7 ist keine nachträgliche Ausnahme vom Protokoll.
Die nichtmonotone Folge ist mit Rundungsauslöschung vereinbar, beweist diese
Ursache aber nicht. Eine unabhängig implementierte Ableitungsprüfung ist nötig.

Eine vorher betrachtete Skalierungsvermutung wird nicht unterstützt: Die freien
Stromparameter sind bereits intern skaliert. Ursprüngliche Werte 0.02619,
0.03838,0.02070 entsprechen physischen Strömen von etwa 262,384,207 kA, nicht
unskalierten Ampere-Freiheitsgraden. Die Fluxgradienten-Normen der Strom-/Geometrie-
Blöcke betragen ursprünglich 61.8 / 75.7, am ausgewählten Punkt 93.6 / 32.7.
Eine zusätzliche willkürliche Megaampere-Skalierung wäre hier nicht begründet.

Nächster Schritt: separat festgelegte komplexe-Schritt-Prüfung mit eigenständiger
Wertberechnung. Ursprüngliche Fehlermeldung, Toleranz und ausgebliebene Probes
bleiben erhalten. Kein Stationaritäts-, Zulässigkeits- oder SoTA-Schluss.
