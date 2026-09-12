# Neue QI-Diagnose: Vergleich bei gemeinsamem geradem Feldlinienwinkel

Vor neuer Feldauswertung registriert, 2026-09-12. Die abgeschlossene
[16-Zellen-Studie](QI_FRESH_RESOLUTION_RESULTS.md) verglich R/Z, Tangenten und
|B| bei gleichem VMEC-Winkel. Ihre1e-3-Fidelitätsgrenze scheitert14/16-mal.
Diese neue Diagnose prüft einen möglichen Parametrisierungsbeitrag; die
historischen Kriterien/Ergebnisse werden nicht umdefiniert oder überschrieben.

## Koordinaten und eng begrenzte Hypothese

Die Primärdokumentationen von [STELLOPT](https://princetonuniversity.github.io/STELLOPT/VMEC%20PEST1%20Coordinates.html)
und [booz_xform](https://hiddensymmetries.github.io/booz_xform/theory.html)
beschreiben den geraden Feldlinienwinkel u=theta+lambda bei unverändertem
toroidalen Winkel. Abruf2026-09-12; keine Gleichsetzung mit Boozer-Winkeln.
Wir behalten hier ausdrücklich den bisherigen geometrischen phi-Sinn und
die bereits geprüfte signierte Flusskonvention, statt ein anders orientiertes
PEST-Konventionspaket zu übernehmen.

Eigene Kettenregel für festes s, D=1+lambda_theta:

    theta_u = 1/D; theta_phi|u = -lambda_phi/D
    e_u = e_theta/D
    e_phi|u = e_phi - e_theta*lambda_phi/D

Die Positions-/Betragswerte werden erst am so bestimmten theta ausgewertet.
Ein bloßer Umbenennen alter Winkelarrays ist falsch. Eine gleiche radiale
Winkelursprungswahl wird durch die unveränderten gespeicherten symmetrischen
Lambda-Koeffizienten festgelegt, nicht aus einem optimierten Datenabgleich.
Dieser Vergleich ist immer noch kein vollständig koordinateninvarianter
Oberflächenabstand; iota und Volumen werden durch die Transformation nicht geheilt.

## Festgelegte Matrix und Prüfungen

Alle vier historischen Dateien und alle16 neuen Wouts der vollständig
hashgebundenen frischen QI-Studie. Dieselben s=0,25/0,5/0,75; u und geometrisches
phi auf64/128-Gittern über einen Feldzeitraum. Vollständige48 neue Wout/Radius-
Paare und12 historische Referenzen behalten; keine Fallauswahl nach neuem Ergebnis.

Additiver Koeffizientenleser mit denselben vollen/halben Radialgittern und
physikalischen m/n-Moden. Vor neuen Koordinaten alle archivierten128er VMEC-
Punktfelder mit normierter Abweichung<=1e-12 reproduzieren. Unveränderte
alte Reader und Ergebnisdateien. Newton-Inversion maximal50 Schritte,
Schrittkappung0,5rad; residual<=1e-12 und D>1e-8 an allen ausgewerteten Punkten.
Nicht konvergierte/falsch orientierte Punkte stoppen ihre Freigabe und bleiben
negativ; keine Behauptung global bewiesener Bijektivität aus diesen Stichproben.

Getrenntes skalares Bracketing mit expliziter Fourierauswertung prüft alle32x32
gemeinsamen Punkte je Wout/Radius; Klammer u±(sum(abs(lambda_mn))+1),
Brent-Root xtol1e-13. theta-Abweichung<=1e-10, eigene Residuen<=1e-12;
Positionen, |B| und transformierte Tangenten normiert<=1e-10 gegentesten.
Alle64/128-Punktarrays speichern, gemeinsame Punkte<=1e-12 und Differenzen
der jeweiligen alten/neuen Feldvergleichsfehler<=1e-5 verlangen.

Neue Vergleichsgrenzen wie zuvor1e-3 für R/Z, beide transformierten Tangenten,
|B| und Volumen relativ, iota absolut. Vollständige Tabelle in VMEC- und neuen
Koordinaten nebeneinander, ohne die alte Klassifikation zu verändern.
Weniger Fehler stützen einen Parametrisierungsbeitrag, nicht automatisch gleiche
Physik; verbleibende Abweichungen können weitere Gleichgewichts-/Produzenten-
Untersuchung erfordern. Keine neue QI-/Maximum-J-/absolute Driftfreigabe.

## Reihenfolge und Ressourcen

Reine analytische Koordinatenkontrollen vor echter Auswertung: Identität,
bekannte sinusförmige Verschiebung, periodische Winkel, unabhängige skalare Roots,
Kettenregel gegen Cartesian-Differenzen, ungültige/singuläre Daten.
Keine neuen Gleichgewichtsläufe oder Installationen. Ausführung erst nach
geschlossener aktiver SLSQP-Suche samt Abnahmen und der registrierten sechs-Netze-
Studie; keine parallele schwere Rechnung. Neue Rohdaten auf unter1GiB schätzen,
3GiB vor Start und2GiB laufende Reserve. Ergebnisse, Audits und negative Zellen
vollständig dokumentieren/committen, bevor neue Physikhypothesen ausgeführt werden.
