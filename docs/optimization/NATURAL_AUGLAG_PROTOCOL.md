# Natürliche Fluxresiduen mit klassischem Augmented Lagrangian

Vorab festgelegt am 2026-09-12, nach abgeschlossenem GN-1024-Lauf und während
der zweiten SLSQP-1024-Wiederholung; vor neuer physikalischer AL-Auswertung.

## Motivation und mathematische Identität

Der qualifizierte quadratische Feldterm soll auch einer klassischen
Least-Squares-Suche zugänglich sein. Frühere räumliche Residuen erhielten bewusst
die alte **quartische** Flux-Strafzielfunktion. Hier minimieren wir ausdrücklich
den **rohen** Flux f=||z||²/(2s), s=1e-6, unter denselben 137 g>=0. Kein
zielfunktionserhaltender Vergleich gegen jene alten quartischen Experimente.

Für lambda>=0, rho>0 ist die klassische Ungleichungs-AL-Funktion

`L = f + (||max(0,lambda-rho*g)||² - ||lambda||²)/(2*rho)`.

Das Residuum `r=[z/sqrt(s), sqrt(rho)*min(0,g-lambda/rho)]` hat
`0.5*r.T*r = L + ||lambda||²/(2*rho)`. Der fehlende Term ist während eines
inneren Laufs konstant. Der Gradient ist exakt
`Dz.T*z/s - Dg.T*max(0,lambda-rho*g)`; der Multiplikator wird mit
`lambda_new=max(0,lambda-rho*g)` aktualisiert. An einer Schaltstelle wird die
Residualableitung null gewählt; die quadratische Meritfunktion ist dort
differenzierbar. GN bleibt ein Modell, keine vollständige Hesse-Matrix.

Primärquellen: [Rockafellar, historische Einordnung und AL-Erweiterung](https://sites.math.washington.edu/~rtr/papers/rtr258-ExtendedALM.pdf)
und [SciPy: Least-Squares/TRF und Solveroptionen](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html).
Die hier verwendete Residuenidentität wird zusätzlich direkt algebraisch und
numerisch geprüft; die Methode ist klassisch, keine behauptete Neuerfindung.

## Fester Versuchsaufbau

Gleiche LPQA-Oberfläche, Originalstart, 207 DOFs, Ordnung 8, 16 Spulen, 137
konservative Ungleichungen, x=x0+0.01*y und identische unabhängige Abnahme wie
beim direkten Pilot. Native z plus qualifizierter batched Dz; gekoppelte
Wert-/Gradientidentität mit unverändertem 1e-10-Limit an **jedem** Bundle.

Zwei sequenzielle Wiederholungen vom Original. Je maximal **1033** vollständige
Bundles: neun Seed-46-Startprüfungen plus acht innere Stufen mit je maximal 128
neuen vollständigen Bundles. Ungenutzte Stufenbudgets werden nicht übertragen.
Jede neue Auswertung zählt, auch abgelehnte Trials oder Fehler; exakte letzte
Wiederholungen sind Cachetreffer. Zusatzarbeit für Dz, native Projektion,
Residualkomposition und Stufenbudgetverweigerungen separat erfassen.

Start lambda=0, rho=10, previous_violation=max(1,Verletzung am Original).
Innerer Solver: SciPy least_squares, method=trf, tr_solver=exact, loss=linear,
x_scale=1, ftol=xtol=gtol=1e-10, max_nfev=100000. Die benutzerseitige Bundlegrenze
beendet früher. Nach einer Stufe gewinnt der kleinste tatsächlich ausgewertete
AL-Residualnormwert dieser Stufe (erste Bindung), nicht die globale physikalische
Auswahl. Dieser Punkt ist Ausgangspunkt der nächsten Stufe; keine weiteren
physikalischen Auswertungen zur Auswahl. Dort lambda aktualisieren; rho für die
nächste Stufe mit 10 multiplizieren, wenn v>0.25*previous_violation, sonst halten.
previous_violation=max(v,1e-12). Alle acht Stufen bleiben Pflicht, außer
Konstruktionsziel oder Fehler beendet vorher. Kein Budgetnachschlag.

Nach bestandener Startprüfung beendet ein vollständig ausgewerteter Punkt mit
f<=0.008 und allen g>=0 die Konstruktion. Das ist **kein** Konvergenznachweis.
Gesamtauswahl wie zuvor: interne v<=1e-8 zuerst, darunter kleinster Flux,
sonst kleinste Verletzung dann Flux, erste Bindung. Beide Felder unabhängig
abnehmen: alle vier Fluxgitter, alle Geometriegitter, kontinuierliche Schranken
und native Zusatzmetriken. Kein Holdout-Feedback. Kein gleicher Wallzeitvergleich
oder Methodenrang aus diesem explorativen anderen Stufenalgorithmus.

## Prüfungen vor der physikalischen Suche

1. Sieben reine Kernelkontrollen: AL-Wert/Gradient/Multiplikatorvorzeichen,
   unabhängige Residualrichtungsdifferenzen, Schaltstelle, ungültige Parameter.
2. Exakt lösbare beschränkte Quadratik mit Minimum x=(1,0): derselbe achtstufige
   Solver, maximale Parameterabweichung <=1e-5, Verletzung <=1e-8 und stationäre
   Lagrangegradientnorm <=1e-6. Fehlschlag stoppt vor jedem neuen Plasmabundle.
3. Qualifizierter Originalvektor und native z/Dz müssen gebunden sein; die
   ursprüngliche vollständige Seed-46-Richtungsprüfung muss <=1e-6 bestehen.
4. Unabhängiger Nachprüfer berechnet Stufen-Meritwerte, Stufenauswahl,
   Multiplikator-/rho-Folge, Budget, Gesamtwahl und Wiederholung erneut.

Protokoll/Kernel jetzt committen; Laufadapter und analytische Solverkontrolle
ebenfalls testen und committen **vor** der physikalischen Ausführung. Neue Suche
erst nach beiden SLSQP-Armen und deren Abschlussdokumentation. Keine Änderung
an laufenden oder historischen Suchdaten. Ein Erfolg an einem Startpunkt ersetzt
nicht die noch nötigen Mehrstart-/Budgetvergleiche aus Schritt 2.
