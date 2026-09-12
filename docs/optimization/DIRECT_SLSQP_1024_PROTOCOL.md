# Neuer SLSQP-Konstruktionslauf mit 1024-Bundle-Grenze — 2026-09-12

Vor dem neuen Lauf festgelegt. Der abgeschlossene 256-Bundle-Pilot bleibt
unverändert. Er hat weder Konvergenz noch eine zulässige Baseline gezeigt.
Der parallel vorbereitete GN-Versuch erhält bereits ein Limit von 1024 Bundles;
die klassische Alternative soll ebenfalls unter diesem Limit untersucht werden,
bevor wir aus der neuen Krümmungsdarstellung einen Optimierungsvorteil ableiten.
Diese Auswahl erfolgt explorativ nach älteren Ergebnissen, nicht blind.

## Unveränderte Konstruktion und neue feste Grenze

Alle physikalischen Daten, 207 Parameter/Original-Warmstart, 137 Ungleichungen,
Roh-Flux/1e-6, Koordinaten x=x0+0.01*y und SLSQP-Optionen bleiben wie im
[ursprünglichen Protokoll](DIRECT_SLSQP_PILOT_PROTOCOL.md): analytische Jacobians,
ftol=1e-10, maxiter=100000. Einziger Suchparameterunterschied zu diesem Pilot:
je **1024** statt 256 vollständige Bundles. Keine Fortsetzung gespeicherter
Iterierter oder Übernahme eines günstigeren Starts.

Zwei sequenzielle identische Wiederholungen. Die ersten neun Bundles sind wieder
die unveränderten Seed-46-Startprüfungen mit allen vier Differenzenschrittweiten.
Fehlversuche zählen, exakte letzte Wiederholungen sind Cachetreffer. Reguläre
Solver-Rückkehr oder feste Budgetgrenze beendet den jeweiligen Arm. Keine
nachträgliche Erweiterung anhand der Ergebnisse.

Auswahl unverändert: interne Verletzung<=1e-8 zuerst, darunter minimaler Flux;
ansonsten minimale Verletzung, dann Flux, erste Bindung. Beide ausgewählten
Felder speichern und getrennt gegen unveränderte feine Flux-/Geometrie-/native
Prüfungen bewerten. Ein unabhängiger Ledger-Audit muss das 1024-Limit explizit
prüfen; der alte Prüfer-Standard 256 wird nicht aus dem Bericht abgeleitet.

Zusätzlich müssen die ersten 256 vollständigen Vorschlagshashes und Werte beider
neuen Arme exakt dem alten 256-Bundle-Pilot entsprechen. Falls der Präfix sich
ändert, gilt die behauptete unveränderte Fortentwicklung als nicht bestätigt;
nicht stillschweigend einen anderen Vergleich daraus machen.

## Vergleichsgrenzen

Erst starten, wenn beide GN-Suchläufe beendet sind; keine parallelen nativen
Suchläufe. Der neue SLSQP-Lauf darf keine Rückmeldung aus seinen eigenen oder
GN-Holdouts bekommen. Beide haben dieselbe maximale Bundlezahl, nicht dieselbe
Ableitungsarbeit: GN berechnet zusätzlich eine räumliche Matrix. Wallzeit und
Arbeit getrennt berichten; frühe Solver-Rückkehr ist kein verbrauchtes Vollbudget.
Die laufenden GN-Zwischenwerte begründen keinen formalen Methodenrang.

Auch ein zulässiges Feld an diesem einen Startpunkt schließt Schritt 2 nicht:
Danach mindestens fünf vorab festgelegte Initialisierungen und belastbare
Budget-/Methodenvergleiche gemäß dem übergreifenden Versuchsprotokoll. Kein SoTA-
oder vollständiger Kraftwerksnachweis aus diesem Konstruktionslauf.
