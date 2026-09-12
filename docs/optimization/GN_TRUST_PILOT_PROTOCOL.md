# Klassischer Trust-Region-Pilot mit expliziter Fluxkrümmung — 2026-09-12

Vor neuer physikalischer Qualifikation/Suche festgelegt. Voraussetzung sind die
bestandene quadratische Feldmodelldiagnose und ihr unabhängiger Kern-Audit.
Dies ist ein neuer Konstruktionsversuch, keine Verlängerung alter SLSQP-Läufe.

## Unverändertes Problem, neue lokale Modellierung

Originaler LPQA-Warmstart, 207 freie Parameter, vier unabhängige/16 physikalische
Spulen, Ordnung 8, Feldquadratur 200 und 32x32-Flussgitter. Direkter Roh-Flux/1e-6
und alle 137 zuvor qualifizierten glatten Ungleichungen bleiben identisch.
Physikalische Koordinaten x=x0+0.01*y; keine zusätzliche Stromskalierung.

Jedes vollständige Bundle berechnet zusätzlich den qualifizierten räumlichen
Jacobian D. Feldwert und Gradient müssen bei **jedem** Vorschlag mit dem direkten
Backend bis relativ bzw. komponentenweise normiert 1e-10 übereinstimmen. Die
zusätzliche Matrix H_GN=D.T D/1e-6 wird in y-Koordinaten mit 0.01² multipliziert.
Keine komplette-Hesse-Behauptung, kein Verändern des Zielfunktionsgradienten.

Solver: gepinnte lokale SciPy-Version, `trust-constr`, analytische Ziel- und
Ungleichungsgradienten, Ziel-Hessematrix wie oben, BFGS-Aktualisierung für die
gewichtete Ungleichungs-Hessematrix. Alle 137 Zeilen bleiben erhalten, auch
symmetriebedingt doppelte; keine nachträgliche aktive Auswahl.

Festgelegte Optionen: gtol=1e-12, xtol=1e-12, barrier_tol=1e-10,
initial_tr_radius=0.1, initial_constr_penalty=1,
initial_barrier_parameter=initial_barrier_tolerance=1e-3,
factorization_method=QRFactorization, sparse_jacobian=False, maxiter=10000.
`keep_feasible=False` erlaubt den leicht unzulässigen Originalstart.

Die [offizielle Solver-Dokumentation](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-trustconstr.html)
und [NonlinearConstraint-Schnittstelle](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.NonlinearConstraint.html)
wurden am 12. September geprüft; die tatsächlich ausgeführten lokalen Quellen
werden zusätzlich gehasht. Ein Solver-Erfolgsflag ersetzt keine unabhängige Abnahme.

## Vorprüfungen, Budget und Auswahl

- Analytischer zweidimensionaler Kontrollfall:
  min ((x0-2)²+(x1+1)²)/2 bei x0<=1, x1>=0. Bekannte Lösung (1,0),
  maximale Abweichung <=1e-5, gemeldete Optimalität und Verletzung <=1e-8.
- Vor beiden Armen einmal Original und Punkt 119 gegen die eingefrorenen
  quadratischen Qualifikationsarrays abgleichen: benannte x exakt, alle 138
  Werte/Jacobians und H_GN bis komponentenweise normiert 1e-10. Dieser gemeinsame
  Aufbau wird getrennt gezählt und ist nicht Teil des Suchbudgets.
- Zwei sequenzielle Wiederholungen vom identischen Originalstart, je höchstens
  1024 vollständige Bundles. Erste neun Bundles sind die unveränderten Seed-46-
  Originalzustands-Differenzenprüfungen (h=1e-5,1e-6,1e-7,1e-8, feinste <=1e-6).
  Fehlversuche zählen; exakte letzte Punktwiederholungen sind Cachetreffer.
  Hesse-Anfragen an neue Punkte müssen über denselben vollständigen Budgetweg.
- Vorzeitiger Konstruktionsstopp nur, wenn ein akzeptierter Solver-Iterierter
  Roh-Flux<=8e-9 und jede glatte Ungleichung g>=0 erreicht. Dieser Stop ist
  ausdrücklich **kein Konvergenznachweis**. Sonst reguläre Solver-Rückkehr oder
  1024-Bundle-Grenze, keine Verlängerung anhand der Ergebnisse.
- Unveränderte lexikographische Auswahl: max(0,-min g)<=1e-8 zuerst, unter diesen
  kleinster Roh-Flux; sonst zuerst kleinste Verletzung, dann Flux, erste Bindung.
  Keine Auswahl anhand späterer Holdouts. Beide ausgewählten Felder speichern.

Vor Freigabe des Suchlaufs die Cache-/Hessematrix-Skalierung, Invalidation bei
Fehlern, komplette Budgetzählung und Feld-/Gradientidentität analytisch testen.
Je Arm alle Vorschläge, Arbeit, GN-Identitätsfehler, Iterationsdaten (Optimalität,
Verletzung, Trust-Radius, Barriere), Abbruchgrund und explizite physikalische
Parameterzuordnung erfassen. Wiederholungen müssen Zähler, Feldwerte und gesamte
Vorschlagsfolge exakt reproduzieren. Kein gleicher-Zeit-Methodenvergleich wird
aus zusätzlicher Matrixarbeit pro Bundle abgeleitet.

## Unabhängige Abnahme

Beide final ausgewählten Felder erhalten den unveränderten Holdout: Roh-Flux<=1e-8
auf 128x128/800, die bisherigen Gitterkonvergenzprüfungen, L<=220 m,
kontinuierlich begründete Krümmung<=1/m und Spulenabstand>=1.06 m,
Spulen-Plasma-Abstand>=1.3 m sowie native MSC/Arclängen-/Linking-Prüfungen.
Alle Auflösungen bleiben erhalten; nicht nur eine günstige Endauflösung berichten.

Ein bestandener Entwurf wäre eine zulässige Konstruktion für diese begrenzte
LPQA-Aufgabe, noch keine starke mehrstartige Vergleichsbaseline, globale
Ingenieurfreigabe, abgeschlossener Schritt 1/2 oder SoTA-Fortschritt.

## Analytische Vorbereitung, noch vor physikalischer Auswertung

Der erste Kontrolllauf mit dem zunächst vorgesehenen gtol=1e-8 stoppt bei
(0.9998141304, 0.0001158723), obwohl die Abweichung von der bekannten Lösung die
unveränderte 1e-5-Kontrollgrenze überschreitet. Gemeldete Optimalität 9.747e-9,
Verletzung null: Das Erfolgsflag allein reicht nicht. Vor dem physikalischen
Start wird gtol für Kontrolle und Suche auf 1e-12 verschärft; weder die
Kontrollgrenze noch eine physikalische Zulässigkeitsgrenze wird gelockert.
