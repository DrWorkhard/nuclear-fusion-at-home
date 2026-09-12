# Nächste Baseline-Diagnose: exakte Stromoptimierung bei unveränderter Geometrie

Vor neuer physikalischer Auswertung registriert, 2026-09-12. Die beiden
abgeschlossenen AL-/SLSQP-Kandidaten scheitern am Flux, nicht an den geprüften
Geometriebedingungen. Zuerst untersuchen, wie viel Verbesserung bei ihren
**exakt unveränderten** Spulen allein durch optimal verteilte Ströme möglich ist.
Kein verlängerter SLSQP-Lauf, keine neuen Formmoden, keine gelockerten Grenzen.

## Klassische Methode, keine Neuheitsbehauptung

Bei festen Kurven ist Biot-Savart linear in den Strömen; die feste vierte
Stromsumme macht den Feldvektor affin in den drei freien Stromparametern.
Mit den unveränderten räumlichen Normalfeldgewichten gilt daher

    z(c0 + d) = z0 + A*d,
    min_d Phi = 1/2 ||z0 + A*d||²,    A hat drei Spalten.

SVD-Lösung des linearen Teilproblems ist ein klassischer Schritt zur
Variablenprojektion, nicht bereits eine neue Spulenmethode. Primärgrundlage:
[Golub/Pereyra1973](https://doi.org/10.1137/0710036), separierbare lineare und
nichtlineare Parameter; [O'Leary/Rust, NIST](https://www.nist.gov/publications/variable-projection-nonlinear-least-squares-problems)
beschreibt eine spätere Implementierung. Abruf2026-09-12; ursprünglicher
SIAM-Abstract über Suche verfügbar, direkter Vollseitenabruf403. Hier eigene
enge Anwendung nur auf das dreidimensionale lineare Teilproblem. Keine
Behauptung allgemeinen/globalen nichtlinearen Erfolgs oder eines gelesenen Volltexts.

## Zwei unveränderliche Zustände und fester Prüfpfad

1. Erster ausgewählter AL-Arm aus `evidence/upstream-start-study-v1/summary.json`,
   ausgewähltes Feld-SHA6ee2a013254b2f30195291dfd4d13c6a166d06d5286cb966db92a2646db2fb5f.
2. Erster ausgewählter zusammengesetzter SLSQP-Arm aus
   `evidence/slsqp-composite-v1/summary.json`,
   Feld-SHAa9a2448a9204478acd2b89675f625bc2122c4665c311d6623c0642800e661dcf.

Jeweils Originalaudit und alle abgeschlossenen Abnahmen binden. Explizite
benannte Zuordnung aller207 DOFs, exakte204 Geometriekoeffizienten und unveränderte
Stromausdrücke. Feste Grundstromsumme1250075,624635464A, Stromblatt-Skalierung
gemäß Originalgraph (hier1e7), keine aus DOF-Sortierung geratene Stromposition.
Alle16 Kopien/Symmetriezeichen erhalten. Die tatsächlichen physikalischen
Einzelströme, Gesamtstrom und mittlere Feldstärke vor/nachher berichten.

Pro Zustand vollständiges ursprüngliches138-Zeilen-Bundle mit normiertem
Quellwert-Replay<=1e-12. Native B-Felder am unveränderten32x32-/200-Punkte-
Konstruktionsgitter: Quelle, jeweils drei reine Stromverschiebungen±0,001 in
den explizit identifizierten internen Stromparametern, anschließend der einzige
lineare Minimierer. Keine feineren Daten zum Fitten oder zur Kandidatenauswahl.

Aus Plus/Minus die zentralen affinen Feldspalten bilden; alle sechs Probes
gegen dieselbe affine Formel normiert<=1e-12 prüfen. Vorhandenen nativen
Stromgradienten mit A^T*z gegenprüfen (Flux-Skalierung1e-6 korrekt berücksichtigen),
normiert<=1e-10. SVD mit rcond1e-12; Rang muss3 und Konditionszahl<=1e10 sein,
sonst qualifizierter Abbruch ohne behauptetes eindeutiges Optimum.

Unabhängiger reduzierter QR-Rechner muss d bis normiert1e-10 reproduzieren.
Normalgleichungsrest ||A^T*r||/(||A||*max(||r||,1e-30))<=1e-10;
native Feldvorhersage normiert<=1e-12 und Roh-Flux relativ<=1e-9. Alle vier
Einzelströme samt konstantem Summenausdruck und geometrischen Koeffizienten
unabhängig aus Serialisierung rekonstruieren. Vollständiges neues natives
138-Bundle; alle137 geometrischen Werte gegenüber Quelle normiert<=1e-12.
Alle nativen B-/Bundleanfragen einschließlich zusätzlich gelesener Cachewerte
und beide linearen Löser getrennt zählen. Kein fairer Methodenbudgetvergleich.

## Unabhängigkeit, Holdouts und Entscheidung

Reine analytische Kontrollen zuerst: affine Drei-Strom-Aufgabe mit bekannter
Lösung, nichtverschwindender Rest, Rangverlust, ungültige Skalen/NaNs, QR/SVD-
Konsistenz, feste Summe und Fehlersignale. Separater Datei-/Array-Auditor ohne
erneute Optimierung prüft Quellen, alle Probes, Strom-/Geometrieidentität,
SVD/QR-Lösung, Orthogonalität und vollständige Zahlenklassifikation.

Beide festgelegten Strom-Minimierer auf allen unveränderten Feld-Holdouts
32/64/128 bei200 Spulenpunkten und128/800 nachmessen; Quelle/Gitterzahlen sowie
mittlere Feldstärke berichten. Die geometrische Quellqualifikation gilt nur
bei nachgewiesener exakter geometrischer Identität; keine neue allgemeine
Ingenieurzulassung. Roh-Fluxgrenze1e-8 unverändert, keine Schwellen-Nullwerte.

Ein geringer Stromverbesserungsspielraum ist ein wichtiges negatives Ergebnis,
kein Grund zum Verwerfen der Studie. Eine größere Reserve motiviert erst ein
eigenes Protokoll für Geometrieoptimierung mit innerer Stromelimination. Niemals
aus diesen zwei linearen Problemen globale Formoptimalität oder SoTA folgern.
Physikalische Ausführung erst nach geschlossenem feinsten Netzabschluss samt
Audit; reine Algebra/Implementierung davor zulässig.3GiB Start-/2GiB laufende
Reserve, keine Installationen, keine parallele schwere Rechnung. Alle Ergebnisse
und Prüfungen dokumentieren/committen, Originalstudien bleiben unverändert.
