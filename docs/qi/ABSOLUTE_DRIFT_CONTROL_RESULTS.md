# Absolute Drift am analytischen Spiegel: vollständig qualifizierter Kontrollfall

2026-09-13; [vorab registriertes Protokoll](ABSOLUTE_DRIFT_CONTROL_PROTOCOL.md)
bei2b713c3. Matrix und unabhängiger Audit bei eb64490 vollständig ausgeführt.

## Ergebnis der festen Matrix

Alle81 Zellen und sämtliche27 Verfeinerungslinien bestehen. Kein fehlgeschlagener
Lauf, keine Warnung, keine ausgelassene Auflösung und keine Grenzwertänderung.
Kartesisch12.096 Punkte/603 Rootaufrufe. Separater skalarer Audit:45 vollständige
Läufe/135 adaptive Integrale,309 Root-,2835 Wirkungs-,2835 Transit- und4725
Wirkungsableitungs-Integrandaufrufe. Achsensymmetrie ausdrücklich für die drei
Winkel genutzt, nicht81 unabhängige Magnetfelder gerechnet.

| Prüfung | Größte Abweichung | Feste Grenze |
| --- | --- | --- |
| Direkte Drift gegen integriertes A_psi, relativ | 1,035e-10 | 1e-8 |
| Radiale reduzierte Drift, absolut | 2,525e-18 | 1e-10 |
| Analytische Feldidentitäten, normiert | 3,719e-16 | 1e-12 |
| Alle64→128→256 Verfeinerungen, relativ | 1,424e-10 | 1e-7 |
| Skalar unabhängige Wirkung / Transitlänge, relativ | 3,171e-14 /2,553e-11 | 1e-7 |
| Direkte Drift gegen unabhängiges skalares A_psi, relativ | 1,552e-10 | 1e-7 |
| Zentrale Wirkungsdifferenz, relative psi-Stufe1e-4 /1e-5 | 2,555e-9 /1,471e-8 | jeweils1e-6 |

Maximale adaptive absolute Fehlerschätzung5,668e-11; diese Schätzung allein ist
kein mathematischer Fehlerbeweis. Unabhängige Quadratur und Verfeinerung liefern
zusätzliche numerische Evidenz. Alle SI-/Teilchen-/Summen-/Quellenprüfungen bestehen.

Beispiel, psi0,03/Bstar1,6/alpha0/N256, definiertes positives10keV-Testteilchen:
Einwegwirkung J=2,2463075967e-21kg*m²/s, Transitzeit T=3,7521628182e-6s,
Delta_alpha=0,0016990752614rad, omega_alpha=452,82556854rad/s.
Reduzierte Gradienten-/Krümmungsanteile+0,4603878890 und-0,3528558656 addieren
sich zur positiven Drift. Beide Anteile sind wesentlich; Vakuumvereinfachung
oder ein isoliertes Vorzeichen eines Anteils wäre kein gültiger Vergleich.
Ladungsumkehr kehrt Drift/Frequenz um, doppelte Energie verdoppelt Frequenz,
doppelte Masse lässt sie bei gleicher Energie unverändert. Keine genaue Ionenspezies.

**Schluss:** Allgemeine erste Driftordnung, Einwegwirkung und absolute SI-
Normierung stimmen in diesem lokal drucktragenden analytischen Spiegel überein.
Das ist ein wirklicher begrenzter Qualifikationsschritt, kein Toroid-/QI-/
maximum-J-Zertifikat. Radiale Drift ist durch Achsensymmetrie null; nichtverschwindende
radiale Drift, komplexe Mulden, physikalische Phasen und echte QI-Felder bleiben offen.
Plan-Schritt1 ist nicht abgeschlossen.

Evidenz: `evidence/absolute-drift-control-v1.json`, separater `*-audit.json`,
beide `*-driver/` und alle81 Dateien unter `artifacts/absolute-drift-control-v1/`
(3,0MiB). Ursprungscode, Protokoll, Versionen und Einzelarrays sind hashgebunden.
Abschließende gesamte Regression687 Tests bestanden,144 bekannte Fixture-Warnungen;
Ruff/Dokumentstruktur/Diff bestehen. Keine strenge netCDF-Importfreigabe daraus.

## Aufbewahrte reine Kontrollen vor der Auswertung

Der kartesische Rechner bildet Feld, vollen Jacobian, Feldstärkegradient,
Feldlinienkrümmung und beide Clebsch-Gradienten direkt ab. Die allgemeine
erste Driftordnung behält Gradienten- und Krümmungsanteil getrennt. Ein eigener
Einheitenhelfer liefert Einwegwirkung, Transitzeit, Winkel und Frequenz.

Neun Tests bestehen: Clebsch-/Divergenz-/Kraftgleichgewichtsidentitäten,
unabhängige kartesische Differenzen bei beiden festen Schrittweiten,
verschwindende radiale Drift und azimutale Kovarianz, SI-/Ladungs-/Energie-/
Massenskalierung einschließlich Einweg/Vollbounce sowie ungültige Eingaben.
Eine absichtlich verwendete Vakuumvereinfachung liefert hier ein anderes Ergebnis;
dieser stromtragende Kontrollfall verlangt die allgemeine Driftformel.

Keine native Feldrechnung, Gleichgewichtsrechnung oder neue QI-Abnahme.
Ruff, Dokumentstruktur und Diffprüfung bestehen. Die allgemeine Regression bleibt
bis zum nächsten vollständigen Lauf bei dem zuletzt belegten Stand667 Tests;
die neun kleinen Kontrollen sind separat geprüft. Beide READMEs/Status/Plan
geprüft, Gesamturteil unverändert.

## Quadratur-/Auditaufbau vor der Matrix

Der feste81-Zellen-Runner speichert sämtliche kartesischen Felder, Jacobimatrizen,
Clebsch-Gradienten, Driftanteile, Quadraturgewichte und Integranden. Rootaufrufe,
angefragte/fertige Feldpunkte, Warnungen und fehlgeschlagene Zellen werden erhalten;
ein Zellenfehler überspringt nicht die folgenden Auflösungen.

Separater skalarer Weg verwendet eigene Feldliniengeometrie und Root in z statt
der kubischen Root in S, adaptive Einwegintegrale und beide festen Flussdifferenzen.
Die neun Grundfälle werden ausdrücklich per Achsensymmetrie für die drei Winkel
wiederverwendet;45 skalare Root-/Dreifachintegrationsläufe insgesamt, nicht81
unabhängige Geometrien. Jeder angefangene skalare Lauf wird vor seinem Aufruf
ins Ledger aufgenommen; bei Abbruch bleiben Zähler, fertige Integrale und Warnungen.
Ein separater Arrays-/Summen-/Einheiten-/Quellencheck prüft die gespeicherten Werte.

Acht neue Kontrollen bestehen (zusammen mit den neun Grundtests17): unabhängige
skalare Wirkung plus beide FD-Stufen, kleiner Gesamtworkflow mit allen drei
Auflösungen, Vorzeichen/Faktor-zwei/Einheiten-/fehlende-Stufe-Mutationen,
Zellenabbruch ohne Unterdrückung späterer Stufen, ungültige Eingaben, unvollständige
Verfeinerung und abgebrochene skalare/kartesische Arbeit. Testparameter
psi0,02/Bstar1,4 gehören nicht zur registrierten81-Zellen-Matrix. Initiale
Lintbefunde zur Schleifenbindung/Formatierung wurden vor Auswertung korrigiert.
Ruff/Dokumentstruktur/Diff bestehen; gesamte Matrix weiterhin nicht ausgeführt.

Damals folgten Commit, feste Matrix und unabhängiger Audit; diese sind im oberen
Abschnitt inzwischen abgeschlossen. Nächster Schritt: nichtverschwindende radiale
Drift und Koordinatenkovarianz separat kontrollieren, bevor echte QI-Felder
einen absoluten Drift-/Frequenzpass erhalten.
