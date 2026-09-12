# Signierte Flussnormierung für die QI-Driftmessung

Vor neuer Auswertung registriert, 2026-09-12. Begrenzter Teiltest für Schritt1,
keine neue Bounce-/Orbitrechnung oder globale QI-Zulassung.

## Hypothese aus Theorie und gepinntem Quellcode

Für `B=grad(psi) cross grad(alpha)` und
`alpha=theta_vmec+lambda-iota*phi_geometrisch` gilt mit signierter VMEC-Jacobi-
Determinante `g`:

`g*B^phi = psi_a*(1+lambda_theta)` und
`g*B^theta = psi_a*(iota-lambda_phi)`.

SIMSOPT a79006b0, `vmec_diagnostics.py` Zeile1494 verwendet explizit
`psi_a=-wout.phi[-1]/(2*pi)`. Diesen Minuszweig vorab als Hypothese wählen;
Pluszweig und fehlenden2pi-Faktor nur als feste Negativkontrollen, nicht anhand
des Ergebnisses umschalten. Das historische `A_s` und seine Gauge-Resultate
bleiben unverändert, absolute Driftvorzeichen wurden bisher nicht freigegeben.

[Rodríguez/Helander/Goodman, Gleichungen1.1–1.2](https://doi.org/10.1017/S0022377824000345)
definieren die kanonische Drift aus der Bouncewirkung. Unsere Prüfung betrifft
nur ihre VMEC-Koordinatennormierung. Geometrischer Toruswinkel ist nicht ohne
weitere Transformation der Boozer-Winkel; keine Boozer-Spezialformel übernehmen.

## Feste Daten, Auswertung und Grenzen

Die vier unveränderten Wout-Dateien aus `evidence/qi-radial-action-v1/`:
nfp2/nfp3 jeweils vacuum/beta2; Hashes aus diesen Berichten gegenprüfen.
Radien s=0,25/0,5/0,75. Volle poloidale Periode und eine toroidale Feldperiode
mit16x16 und32x32 Punkten, Endpunkte nicht doppelt. Alle24 Gitter behalten.
Lineare Halb-/Vollgitterinterpolation wie im eigenen bisherigen Tracer.

Lambda-Ableitungen analytisch aus den geometrischen Fouriermoden;
`gmnc,bsupumnc,bsupvmnc,bmnc` getrennt aus Nyquistmoden rekonstruieren.
Die zwei obigen Identitäten prüfen und aus tangentialen R/Z-Ableitungen
zwei kartesische Feldvektoren bilden: kontravarianter Wout-Weg und Clebsch-Weg.
Auch Betrag des ersten Vektors gegen `bmnc` prüfen. Normierung jeweils globaler
maximaler Betrag der Referenz, bei theta-Komponente mindestens `abs(psi_a)`.
Jede dieser vier Fehlergrößen muss<=1e-3 sein; kein Toleranzwechsel bei Fehler.
Negative Vorzeichen-/2pi-Kontrollen müssen Fehler>0,1 zeigen. Verschwindende
Flusskonstante, singularer Jacobian oder fehlende/nonfinite Daten stoppen das Gitter.

Vor realen Feldern: analytischer kreisförmiger Torus mit bekanntem signiertem
Jacobian, Vektorfeld, Fluss-/Lambda-Konvention; Vorzeichen-/2pi- und Singulärtests.
Separater Auditor rechnet die beiden Clebsch-Identitäten, kartesische Kombination
und Betragsfehler aus archivierten Punktarrays erneut, nicht aus Pass-Flags.
Alle Quellen, Codehashes, Punkte, Zwischenfelder und Metriken speichern.

Diese Gegenüberstellung verschiedener Darstellungen **derselben** Wout-Datei ist
kein unabhängiges Gleichgewicht. Sie verwendet den Wout-Jacobian, qualifiziert
nicht dessen Übereinstimmung mit der Ableitung der radial interpolierten Geometrie.
Volle Drift benötigt diese zusätzliche Konsistenz, radiale Geometrieableitungen,
Grad-B/Krümmung, Bouncezeit, feste Invarianten und direkten Bahnvergleich.
Die1e-3-Normierungsprüfung ist kein entsprechend genauer Frequenznachweis.
Kleine Diagnose ohne neue Solver/Archive;2GiB Reserve, kein zweiter schwerer Suchlauf.
