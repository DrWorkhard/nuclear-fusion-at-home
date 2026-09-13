# Neuer klassischer GN-Lauf vom qualifizierten SLSQP-Stromminimum

Vor neuer physikalischer Startqualifikation/Suche registriert,2026-09-13.
Die [geschlossene Krümmungsdiagnose](GEOMETRIC_CURVATURE_RESULTS.md) erklärt
alle sechs gescheiterten linearen Schritte. Jetzt ein gesonderter klassischer
Suchversuch, keine Verlängerung oder rückwirkende Änderung früherer GN-Läufe.

## Feste Quelle und unveränderte Physik

Ausschließlich das bereits vor dieser Entscheidung ausgewählte SLSQP-Stromminimum:
`artifacts/fixed-currents-v1/slsqp/current_minimizer.json`,SHA256
`bb3dc24e817765b8505f539e2e2ca64f4189e280ae0643be3cddcca163f49028`.
Geschlossene Strom-/Holdout-, geometrische Modell-/Probe- und Krümmungsstudien
samt unabhängigen Audits müssen committed und hashgebunden sein.

Gleiche LPQA-Oberfläche, a0=10,100286074838271,207 explizit benannte DOFs:
204 geometrische Ordnung8-Koeffizienten und drei freie Ströme; vier Grundspulen,
16 Kopien, feste Basisstromsumme1250075,624635464A, interne Stromskalierung1e7.
Keine Rangabschneidung, Gaugebeseitigung, Stromelimination oder neue Skalierung.
Alle bisherigen138 direkten Werte und analytischen Gradienten bleiben unverändert.
Feld32²-Halbperiode/200 Spulenpunkte, volle64²-Plasmageometrie/1600κ-Punkte.

Konstruktion: Fluxziel8e-9, Länge219,9m, κ0,99/m, konservativer glatter
Spulenabstand1,1m, Plasmaabstand1,3m, bestehende MSC-/Arcgrenzen.
Auswahltoleranz1e-8 auf den137 normierten g>=0-Bedingungen; keine Relaxation
der unabhängigen physikalischen Abnahme: Flux<=1e-8, Länge<=220m, κ<=1/m,
kontinuierlicher Spulenabstand>=1,06m, Plasmaabstand>=1,3m samt nativem Zusatzgate.

## Startqualifikation innerhalb jedes Budgets

An genau den16 vorhandenen SLSQP-Ereignissen der geometrischen Probestudie
dieselben Punkte/volle138 Werte erneut berechnen, Reihenfolge unverändert.
Alle Werte normiert<=1e-12 gegen die archivierten Bundles; am ersten Punkt
voller138x207-Jacobian<=1e-12 gegen die geschlossene Stromquelle. Explizite
physikalische Zuordnung, identischer serialisierter Ausgangszustand/16 Kopien.
Zusätzlich initiales H_GN gegen das Gramprodukt der unabhängig qualifizierten
nativen1024x207-Quellmatrix normiert<=1e-10 prüfen und speichern.

Das ist ein **eigenes Gate** aus vollständiger Startwiedergabe und der bereits
geschlossenen zusammengesetzten Qualifikation aller drei geometrischen Richtungen,
nativer kompletter Feldmatrix und affiner Stromableitungen. Kein neuer günstiger
FD-Schritt und keine Umdeutung des historischen gescheiterten Allzeilen-FD-Tests.
Alle16 Wiederholungsbundles werden im jeweiligen Suchbudget bezahlt. Ein negativer
Starttest stoppt vor Solverstart; Fehlerpunkt und fertige Daten bleiben erhalten.

## Feste klassische Suchmethode und Budgets

Unveränderter nativer-Kovektor-GN-Kern: f=Φ/1e-6,H_GN=DᵀD/1e-6, vollständige
analytische direkte Gradienten. Je Bundle dieselben Feld-/Gradientidentitäten
<=1e-10, ungekuppelte Projektionsabweichung weiter sichtbar. Gauss-Newton ist
nicht die volle Hessematrix der nichtlinearen Zielfunktion.

SciPy1.18.1 `trust-constr`, affine Koordinaten x=x0+0,01y; richtige Gradient-/
Hessian-Kettenregel. Nichtlineare Ungleichungen mit analytischer Jacobimatrix,
BFGS-Constraint-Hessian, `keep_feasible=False`. Fest wie im bisherigen GN-Pilot:
gtol/xtol1e-12,barrier_tol1e-10,initial_tr_radius0,1,
initial_constr_penalty1,initial_barrier_parameter/initial_barrier_tolerance1e-3,
QRFactorization,sparse_jacobian=False,maxiter10000.

**Zwei getrennte Wiederholungen, jeweils maximal2048 vollständige Bundleversuche**
einschließlich Startqualifikation, Wiederanfragen ohne Cachetreffer und Fehler.
Abgelehnte Budgetanfrage verbraucht keine neue Physik. Keine Budgeterhöhung nach
Zwischenergebnissen. Alternativer Stopp: Solver kehrt zurück oder akzeptierter
Schritt erreicht f<=0,008 bei min(g)>=0. Zielstopp ist keine Konvergenzbehauptung.
Auswahl genau durch bisherigen Lexikographieschlüssel: Konstruktionspass zuerst,
dann Verletzung, dann f; Gleichstand erster gespeicherter Zustand. Holdouts bleiben
vollständig von Auswahl/Suche getrennt, auch wenn die Konstruktion noch scheitert.

Eine analytische beschränkte quadratische Kontrollaufgabe und synthetische
vollständige138/207-Abläufe samt absichtlichen Gate-/Budget-/Backendfehlern vor
realer Suche prüfen. Neue Treiber/Auditoren vor physikalischer Rechnung committen.

## Evidenz, Ressourcen, unabhängige Abnahme

Beide vollständigen Punkt-/Wert-Ledger, Zähler, Start-Jacobians/H_GN, ausgewählten
serialisierten Felder und akzeptierten Iterationen speichern. Native direkte
Arbeit und zusätzliche gebündelte Spulenableitungen/Strom-VJPs/Kovektor-B-Anfragen
getrennt zählen, inklusive Cacheleseanfragen. Bei Fehler vollständiges zuletzt
fertiges direktes Bundle sowie vorhandene Matrixdaten/Fehlerpunkt erhalten.
Keine Speicherung sämtlicher dichten Suchmatrizen vorausgesetzt; qualifizierter
Code, Ausgangsmatrix, alle Identitätswerte und Wiederholung bilden die Prüfkette.

Separater Auditor prüft alle138-Werte-Auswahlen, physikalische Parameterhashes,
Startquellen/Gramformen, feste Optionen/Budgets, Arbeit und sämtliche akzeptierten
Iterationen. Beide vollständigen Historien samt Zählern/Identitätschecks müssen
exakt wiederholbar sein. Kein altes Suchpräfix von einem anderen Start verlangen.
Vier unveränderte unabhängige Feld-/Krümmungs-/Abstands-/native Holdoutphasen für
beide ausgewählten Felder vollständig ausführen und auditieren, auch bei Ablehnung.

Vorarbeiten nicht kostenlos: Konstruktion bis zur Quelle nominell1033 AL+2048
SLSQP-Bundles pro Pfad plus separat dokumentierte Start-/Strom-/Geometrie-/
Krümmungsdiagnosen und Holdouts. Das ist eine hybride Warmstart-Untersuchung,
kein fairer Gleichbudgetvergleich zur historischen Suche oder allgemeines Ranking.

3GiB Start-/2GiB laufende Reserve; je ein schwerer Prozess, keine parallelen
Installationen/Studien. Protokoll, aktive Kerne, SciPy-Solverquellen/Versionen,
Native-Umgebung und Threads binden; Fortschritt/Fehler regelmäßig sichern.
Schritt1/2 erst bei ihren echten Kriterien schließen; keine Zulassung durch
Solvererfolg, wiederholbare Ledger oder bestandene Softwaretests.
