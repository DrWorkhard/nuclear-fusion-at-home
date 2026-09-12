# Diagnose der spektralen Wout-Feldrepräsentation

Vor neuer Rechnung registriert, 2026-09-12. Die Produktzerlegung hat radiale
Interpolation als alleinige Ursache ausgeschlossen. Jetzt unveränderte vier
Fälle und die beiden Halbflächen neben s0,25/0,5/0,75 bei64x64 und128x128 prüfen.
Keine neuen Gleichgewichte, keine Reparatur oder Neuabnahme der alten Felder.

Quellinspektion: gepinntes VMEC8.52 `wrout.f` Zeilen684–720 transformiert und
glättet Lambda auf Halbflächen; Zeilen829–859 projizieren g und Feldkomponenten
separat auf endliche Nyquistmoden. Das ist keine nachgewiesene exakte Herkunft
aller alten Goodman-Produzenten. Die Dateien enthalten maximal m8 (nfp2) oder
m12 (nfp3), jeweils |n/nfp|12 in den Nyquistmoden. Geometrie/Lambda reichen nur
bis m4 bzw.m8 und |n/nfp|10. Diskrete Quellenbefunde, noch keine Fehlererklärung.

## Vorab festgelegter Test

Alle24 eindeutigen Halbflächenpunkte aus der vergangenen Diagnose, je zwei
neue Winkelgitter,48 Endpunktgitter insgesamt. Beide gespeicherten Feldkomponenten
und g, Lambda-Ableitungen, iota mit dem unveränderten Matrix-Fourierweg auswerten.
Die beiden bisherigen16/32-Gitter als Teilgitter bis normiert1e-12 reproduzieren.

Rekonstruieren `C_theta=psi_a*(iota-lambda_phi)/g` und
`C_phi=psi_a*(1+lambda_theta)/g`. Diese rationale Clebsch-Darstellung ist eine
**Diagnose**, nicht die ungeprüfte neue Referenz. Ihre DFT exakt auf die wirklich
gespeicherten Nyquistmoden beschränken, einschließlich konjugierter Gegenmoden;
keine bloße rechteckige Maske bei fehlenden Moden. Mit originalem `B^theta/B^phi`
vergleichen. Relative Maximumsnorm zur jeweiligen originalen Komponente muss
<=1e-5 sein, ebenso64/128-Verfeinerungsdifferenz der Projektion am gemeinsamen
Gitter. Überschreitung behalten, nicht nachträglich eine andere Norm/Grenze wählen.

Zusätzlich das ursprüngliche Residuum `g*B^i-psi_a*h_i` spektral in gespeicherte
und außerhalb liegende Moden zerlegen; L2-Energien berichten, Parsevalfehler<=1e-12.
64 Punkte übertreffen die Nyquistanforderung für die endlichen Produktpolynome;
dies per maximaler Eingangsmode prüfen. Rationales C benötigt trotzdem den
gesonderten Verfeinerungstest. Keine additive Interpretation von Maximumsnormen.

Vorher analytische Moden-/Konjugations-/Parseval-/Auslassungskontrollen. Separater
Auditor führt die Projektion über explizite Kosinus-/Sinussummen auf Basis der
gespeicherten Fourierkoeffizienten erneut aus und prüft Band-/Fehlerstatistiken.
Alle Rohwerte, Spektren, Projektionen, Fehler, Quell-/Codehashes und Fehlschläge
speichern. Ein passender Projektionstest stützt endliche Ausgabe-Trunkierung als
Erklärung, qualifiziert aber weder das untrunkierte Feld noch absolute Drift.
Mindestens2GiB Reserve; keine parallele schwere Suche oder Installation.
