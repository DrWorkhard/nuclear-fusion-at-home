# Geometrischer Abstieg: begrenzte lineare Modelle und echte Kontrollschritte

Vor jeder neuen Modelllösung oder Feldrechnung registriert,2026-09-12.
Nach F-076 sind die drei Ströme an beiden festen Formen praktisch optimal.
Jetzt unterscheiden: Gibt es in den204 Formparametern noch deutlichen lokalen
Abstieg, und bildet die Linearisierung zugleich die Geometrie ausreichend ab?
Keine Budgetverlängerung einer alten Suche; keine Behauptung eines neuen Solvers.

## Unveränderte Quellen und Abgrenzung

Genau beide Stromminimierer aus `evidence/fixed-currents-v1.json`, in Reihenfolge
AL/SLSQP, samt bestandenem Qualifikationsaudit, allen acht Feld-Holdouts und
deren separatem Audit. Feld-SHAs:

- AL: `d73b89913f2bc460e097a92ae58864419db6f5a10e661974ec0e02e26208d572`.
- SLSQP: `bb3dc24e817765b8505f539e2e2ca64f4189e280ae0643be3cddcca163f49028`.

Die Quellen behalten ihre jeweilige Stromverteilung, einschließlich aller16
Kopien und der festen Summe1250075,624635464A. Keine erneute innere Stromoptimierung.
Explizite Stromgraph-/DOF-Zuordnung; nur die204 komplementären geometrischen DOFs
dürfen sich ändern. Originalproblem mit207 DOFs, Ordnung8,32²-Feldgitter/200
Spulenpunkten, voller64²-Plasmaoberfläche, allen137 direkten Ungleichungen und
unveränderten physischen Annahmegrenzen. Quellabnahmen qualifizieren keine neue Form.

## Sechs vorab festgelegte lineare Teilprobleme

Je Zustand gespeicherte Werte `v` und vollständiges `J` aus der aktuellen
Stromqualifikation verwenden. `f=v[0]` ist Roh-Flux/1e-6, `g=v[1:]` sind die137
Konstruktionsbedingungen. `h=J[0,geom]`, `H=J[1:,geom]`. Drei feste Radien in
ursprünglichen Fourierkoeffizienten: `r = 1e-6, 1e-5, 1e-4`.

    min_s c^T s,   c=h/||h||₂,
    A s <= b,      A=-H, b=g/r,
    -1 <= s_i <= 1,
    d_geom = r*s,  d_current = 0.

Die Division der Ungleichung durchr vermeidet unnötig winzige Matrixeinträge;
keine Zeile entfällt, keine spätere Radiuswahl. Die Linearisierung verlangtg>=0,
nicht−1e-8. Die geerbte Auswahlkonvention bewertet echte Bundles weiterhin mit
maximaler Verletzung<=1e-8; das ist kein physikalisch gelockerter Grenzwert.
Ein exakt verschwindender Geometriegradient wird gesondert gemeldet, nicht
dividiert oder als globale Formoptimalität bezeichnet.

Solver: vorhandenes SciPy1.18.1 `linprog(method="highs-ds")`, presolve=True,
maxiter10000, time_limit60s je LP, primal/dual_feasibility_tolerance1e-10,
simplex_dual_edge_weight_strategy="steepest-devex". Kein Solver-/Toleranzwechsel
bei Fehlern. Alle sechs LP-Ausgaben, Marginalwerte, Primalpunkte und Kosten
speichern, auch bei Fehler oder ungültigem Zertifikat. Keine zweite LP-Suche im Audit.

Unabhängige skalare Summen prüfen primalen Rest, Vorzeichen der Marginalwerte,
Stationarität, Komplementarität und primal-duale Kostenlücke bis1e-9 normiert.
Primalzeilenrest normiert durchmax(1,|b_i|), Boxrest unskaliert; Stationarität
durchmax(1,|c_j|). Kostenlücke/Komplementaritätsprodukte durch
max(1,|Primalwert|,|Dualwert|). Marginal-Vorzeichen unskaliert.
FürSciPy-Marginalwerte `m<=0, l>=0, u<=0` gilt
`c-A^T m-l-u=0` und `Dualwert=b^T m-sum(l)+sum(u)`.
Ein Zertifikat gilt nur für dieses lineare Modell, nicht für die nichtlineare Form.

Primärgrundlagen: [SciPy-HiGHS-Dokumentation](https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs-ds.html)
und [HiGHS-Primal-/Dualbedingungen](https://ergo-code.github.io/HiGHS/dev/guide/kkt/),
Abruf2026-09-12; SciPy-Seite1.18.0, zusätzlich installierten1.18.1-Wrapper gelesen.
Die spezielle Marginal-Vorzeichenkonvention wird durch analytische Kontrollen
geprüft, nicht aus der Bezeichnung „Lagrange-Multiplikator“ geraten.

## Native Ableitungs- und Schrittprüfung

Je Zustand zunächst ein vollständiges natives Quellbundle; benannte Zuordnung
und alle gespeicherten Werte/Jacobispalten normiert<=1e-12 reproduzieren.
Für jeden erfolgreich zertifizierten LP-Punkt die geometrische Richtung
`p=d/||d||₂` verwenden. Bei exakt d=0 keinen künstlichen Schritt erzeugen.
Zwei zentrale Differenzen mit den festen eps1e-7 und1e-8: vier vollständige native
Bundles. Alle18 Nicht-Paar-Zeilen `[0:6] + [126:138]` müssen bei **beiden** eps
normiert<=1e-6 zum analytischen `J*p` passen. Keine nachträgliche Auswahl des
günstigeren Differenzenschritts.

Die120 Paarzeilen zusätzlich unabhängig aus serialisierten Fourierkoeffizienten
mit komplexen Schrittenh1e-12 und1e-20 prüfen; normierter Ableitungsfehler<=1e-9,
gegenseitige Schrittstabilität<=1e-10. Reelle Paarwerte<=1e-10 und native200-Punkte-
Positionen<=1e-12 rekonstruieren. Separater Audit benutzt explizite reelle
Fouriersummen und die gewichtete Kettenregel für alle sechs Richtungen, keine
Wiederverwendung der komplexen Ableitung als Gegenrechnung.

Nur nach bestandenem Quell-/LP-/Richtungsgate ein vollständiges natives Bundle
am einen Vorschlagx+d auswerten und dessen Feld speichern. Alle anderen festgelegten
Richtungen weiter prüfen; kein Verwerfen schlechter Resultate. Maximal32 vollständige
native Bundles:2 Quellen,24 FD-Probes,6 Kontrollschritte, jeweils Werte und gesamte
Jacobimatrix. Zwei zusätzliche native16-Kurven-Positionsabfragen; pro Zustand
ein unabhängiger reeller120-Paar-Wertlauf sowie sechs komplexe Paarläufe. Arbeit
genau zählen, frühere Studien als zusätzliche Vorarbeit verlinken, nicht „gratis“.

Berichten: LP-Kosten/aktive Zeilen/Marginalwerte, vorhergesagter und tatsächlicher
Fluxwechsel, maximale echte geometrische Verletzung, Fehler aller137
Geometrie-Linearisierungen und physikalisch unveränderte Einzelströme. Verhältnis
echte/vorhergesagte Verbesserung nur bei nichtverschwindender Vorhersage.
Keine Auswahl eines „besten neuen Entwurfs“ und keine feine Abnahme in dieser
Diagnose; eine anschließende Suche beziehungsweise Kandidatenqualifikation braucht
ein getrenntes Protokoll. Aus keinem Abstieg folgt kein globales Optimum; aus
modellseitigem Abstieg folgt keine echte Zulässigkeit.

Reine analytische LP-/Primal-Dual-/Fehlerkontrollen und synthetische Ablaufprüfungen
vorab. Alle Originalquellen/Code/Protokolle hashbinden; gesamte neue Eingabe und
angefragte Punkte bei Fehlern erhalten.3GiB Start-/2GiB laufende Reserve, keine
Installationen oder parallelen schweren Studien. Zwischenstände und unabhängige
Prüfung dokumentieren und committen; Schritt1/2 bleiben bis zu ihrer wirklichen
wissenschaftlichen Abnahme offen.
