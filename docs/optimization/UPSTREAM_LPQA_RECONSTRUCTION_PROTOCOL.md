# Rekonstruktion der fünf fest ausgewählten LPQA-Referenzfelder

Vor neuer physikalischer Ausführung festgelegt, 2026-09-12. Die fünf Einträge
und Feldhashes kommen unverändert aus dem
[abgeschlossenen Inventar](UPSTREAM_LPQA_INVENTORY_RESULTS.md). Kein weiterer
Kandidatentausch anhand der neuen Ergebnisse, keine Optimierung und keine
Strom-/Geometrieanpassung. Erst nach Abschluss und Dokumentation des laufenden
Jacobiskalierungsversuchs einschließlich seiner feinen Holdouts ausführen.

## Unveränderte Eingaben und Rekonstruktionsprüfung

Exakt das aktuelle LPQA-Ziel mit SHA-256
`4c6ba4bc391a69b5b6a5e84ff82df9b0ce92e20c42f2a47f89a9283fd5bc3458`
und unser a0=10,100286074838271. Jeder Quellbericht und jedes Quellfeld wird
hashgeprüft; 16 physikalische Kopien, vier direkte Fourierbasiskurven der Ordnung8.
Basisströme müssen zu den gemeldeten Werten passen (relative Normabweichung
<=1e-12), ohne ihre Summe auf unseren anderen Startstromwert zu normieren.

Nur Quadraturrepräsentation ändern: neues Feld aus identischen vier Fourier-
Koeffizientensätzen/Strömen und Symmetrien nfp2, stellsym=true,200 Punkten je
Kurve aufbauen. Regulierungseigenschaften erhalten. Originaldatei unverändert;
neue abgeleitete Datei mit Quell-/Ableitungshashes speichern. Alle16 Kurven
an257 gleichmäßig verteilten Parametern und alle16 Ströme gegen die Original-
Serialisierung prüfen (maximale normierte Abweichung<=1e-12). Geometrische
Nachparametrisierung, Verschiebung oder geänderte Symmetrie ist nicht erlaubt.

Zusätzliche Feldgegenrechnung:64 feste Punkte des8x8-Halbperioden-Zielgitters,
200 und800 Spulenpunkte. Unabhängige Fourierpositionen/-tangenten und direkte
NumPy-Biot-Savart-Summe gegen native Auswertung; normierte Vektorabweichung
<=1e-12 mit Nenner max(1,||B_native||). Vollständige Punktfelder beider Seiten
speichern. Vorher analytische Kreisfeldkontrolle, Linearität und Vorzeichen prüfen.
Dies prüft Filamentfelder abseits der Leiter, kein endliches Wicklungspaket oder
regularisiertes Eigenfeld. Ein gespeicherter Regularisierungswert ist keine
automatische Volumen-/Kraftfreigabe.

## Unabhängige feste Abnahme aller fünf Felder

Bestehenden Feld-/Geometrie-Holdout unverändert verwenden: vier Fluxgitter
(32,200),(64,200),(128,200),(128,800), Geometrie200/1000/5000/20000 und
Plasma64/128/256/512. Roh-Flux<=1e-8, Länge<=220m, Krümmung<=1/m,
cc>=1,06m,cp>=1,3m und bisherige Verfeinerungsgrenzen. Keine Abschaltschwelle.
Alle Kandidaten und Auflösungen behalten, auch bei regulären Ablehnungen.

Dieser erste Rekonstruktionsschritt ist ausdrücklich eine statische Quellen-/
Filamentfeld- und Gitterabnahme, **keine vollständige Designfreigabe**. Falls ein
Kandidat den gesamten Gittertest besteht, folgen vor einer Baselinebehauptung
kontinuierliche Schranken, native Zusatzbedingungen, vollständige Problem-
Identität und Wiederholbarkeit. Neue Stromsumme, andere historische Rechenbudgets
und mögliche gemeinsame Abstammung bleiben sichtbar; fünf Archivfelder sind
keine fünf unabhängigen methodischen Wiederholungen.

Mindestens2GiB freier Platz mit laufendem Wächter, keine parallele schwere
Suche/Installation. Absturz oder Quell-/Symmetrie-/Feldwächterverletzung sind
Ausführungsfehler, keine normale physikalische Ablehnung; Originale nie ändern.
