# Klassische AL mit Jacobispalten-Skalierung

Vor neuer physikalischer Ausführung festgelegt, 2026-09-12, während der
unveränderten AL-Wiederholung. Es wird kein verbessertes Ergebnis vorausgesetzt.

## Hypothese und einzige beabsichtigte Methodenänderung

Die archivierten vollständigen räumlichen Jacobimatrizen zeigen stark
unterschiedliche Spaltennormen: Verhältnis größter/kleinster positiver Norm etwa
401 am Original und149 am alten Kandidaten119. Das ist keine Konditionszahl und
kein Nachweis der Ursache langsamer Konvergenz. Gleiche Koordinatenschritte können
aber sehr unterschiedliche Wirkung haben.

Wir prüfen daher die klassische SciPy-TRF-Einstellung `x_scale="jac"` statt1.
Sie passt die Koordinatenskalen anhand inverser Jacobispaltennormen an; Quelle:
[offizielle SciPy-Dokumentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html).
Keine Änderung an rohem Flux, Residuen, physikalischen Ableitungen,
Stufenauswahl, Multiplikatoren, rho-Regel oder unabhängigen Grenzwerten.

## Unveränderter Versuchsrahmen

Wie im [ursprünglichen AL-Protokoll](NATURAL_AUGLAG_PROTOCOL.md): Originalstart,
207 benannte DOFs, Ordnung8,16 Spulen,137 geometrische Ungleichungen,
`x=x0+0.01*y`, neun feste Startprobes, acht Stufen mit je höchstens128 neuen
Bundles, höchstens1033 pro Wiederholung. Kein Budgetübertrag, kein Warmstart,
kein Holdout-Feedback. Zwei neue sequenzielle Wiederholungen. Originale
physikalische Auswahl und Konstruktionsziel-/Konvergenztrennung bleiben bestehen.

Alle übrigen TRF-Optionen unverändert: `tr_solver=exact`, `loss=linear`,
`ftol=xtol=gtol=1e-10`, `max_nfev=100000`. Ein expliziter getesteter Adapter nimmt
die alten Solveroptionen entgegen, ändert ausschließlich `x_scale` und protokolliert
die effektive Einstellung. Kein globales Monkeypatching oder Ändern alter Kernel.
Der getrennte Runner erhält die historischen Dateien unverändert; sein Diff
gegen den alten Runner muss auf Adapter, Label, Protokoll und Provenienz begrenzt sein.

## Voraussetzungen und unabhängige Abnahme

1. Reine Adapterkontrollen müssen genau eine Optionsänderung, unveränderte
   Funktions-/Jacobianübergabe und Ablehnung unerwarteter Optionen belegen.
   Dieselbe analytisch lösbare beschränkte Quadratik muss die ursprünglichen
   Fehler-/Verletzungs-/Stationaritätsgrenzen bestehen, diesmal mit dem Adapter.
2. Originalstart, Referenzgeometrie, vollständige Start-Ableitungen und native
   Identitätswächter an jedem Bundle bleiben Pflicht. Effektive Optionen und
   neue Adapter-/Runnerquellen werden ausdrücklich in der Studie gebunden.
3. Erst ausführen, wenn die unveränderte AL-Recovery samt unabhängigen Audits
   **und sämtlichen feinen Holdouts** abgeschlossen und dokumentiert ist. Neue
   Kennung `natural-auglag-jac-v1`; mindestens2GiB freier Platz, laufender Wächter,
   keine parallele schwere Such-/Buildarbeit.
4. Unabhängig alle Stufen, Budgets, native Zusatzarbeit, Gesamtwahl, benannte
   Feldidentität und beide vollständigen neuen Wiederholungen prüfen. Im
   Gegensatz zur Recovery wird **kein identischer alter Suchpfad** erwartet:
   die Schrittskalierung ist absichtlich anders. Vergleich gegen unskaliert ist
   nur ein explorativer Ein-Start-Optionsvergleich, keine allgemeine Methodenrangfolge.
5. Beide Felder durch unveränderte vier Fluxgitter, Geometrie-/Plasmagitter,
   kontinuierliche Krümmungs-/Abstandsschranken und native Zusatzmetriken prüfen.
   Fehlende Zulässigkeit bleibt negativ; keine nachträgliche Budgetverlängerung.

Diese Vorabfestlegung betrifft einen gewöhnlichen klassischen Solverparameter,
keine neue Optimierungsmethode. Mehrstartigkeit, Zulässigkeit und belastbare
Ingenieurphysik bleiben Voraussetzungen eines weitergehenden Erfolgs.
