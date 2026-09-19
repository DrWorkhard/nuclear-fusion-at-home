# Feldstarts aus geometrisch angenommenen Konturen: Arbeitsstand

19. September2026. [Protokoll](CLEAR_COIL_FIELD_START_PROTOCOL.md).

Geometriestudie bei323cfdd vollständig geschlossen: alle zwölf Varianten
angenommen, n6/n8-shape-d100mm ausgewählt. Jetzt getrennte numerische
Feldstart-/Auflösungsqualifikation vor jeder weiteren Suche. Noch keine neuen
Target-Feldwerte, keine optimierten Kandidaten und kein Schritt4-Abschluss.

Zwei getrennte lesende Agentenreviews identifizieren dieselben Integrationsfallen:
der alte Konstruktor legt Startkoeffizienten und Flussorientierung bereits an
seinen Kreisen fest; seine Geometriefläche bleibt hart64×32. Auch Gesamtprüfung,
Initialisierungszählung und Flussraster sind nicht durch Umetikettieren übertragbar.
Deshalb additive Klasse mit echtem Geometrieseed vor dem ersten Feldaufruf,
neuem Binder/Workflow/Gesamtaudit und unveränderten alten numerischen Dateien.

Gewählt wird die begrenzte Sechs-Stufen-Prüfung je vier physischer Zellen;
N/V erhalten getrennte zehnteilige Ableitungsqualifikation. Ein Vorschlag für
Innenraster128² bleibt bewusst außerhalb: dafür fehlt hier ein entsprechend
qualifiziertes Targetarchiv. Kein stiller neuer QI-Qualifikationszweig. Beide
Reviewer bestätigen den engeren Startupumfang; spätere Suchpunkte brauchen
ihre eigene feinere unabhängige Abnahme. Strom und archivierter64²-B²-Maßstab
bleiben während sämtlicher Auflösungsprüfungen fest.

Native aktive CP-Strafen erzeugen dichte Paararrays. Schon256×128² benötigt
etwa101MB nur für Differenzkoordinaten einer aktiven Kurve, zuzüglich Distanz,
Gewicht und Ableitungstemporaries; sichere Starts würden diesen Pfad auslassen.
Ein mathematisch identischer KDTree-/punktweise ausgewerteter Adapter begrenzt
den Speicher. Vor Einsatz vollständige aktive24/32-Spulen-Kontrollen bei beiden
registrierten Spulenauflösungen, einschließlich nativer Werte/VJPs, Differenzen,
Peak-Speicher und Zeit. Der zusätzliche algebraische Review bestätigt beide
Kovektoren ohne Faktor1/2 oder Symmetriedivisor. Flächengewicht muss der Betrag
der unnormierten nativen Parameternormalen sein, nicht unitnormal oder auf Summe1
normiertes Gewicht; Nenner je KurveN_curve*N_surface. Dieser rohe Integralterm
hat wie die native Implementierung die SI-Dimensionm^5, bevor die festgehaltenen
Strafgewichte angewandt werden. Synthetische Implementierungsprüfung bleibt nötig.
Reviewpräzisierung vor Code: nur den Suchradius konservativ polstern, danach
den ursprünglichen Hinge exakt anwenden; deterministische Nachbarreihenfolge,
unveränderliche feste Flächendaten und vollständiger Mindestabstand auch bei
Nullstrafe. Keine fehlenden Flächenableitungen als Co-Designgradient ausgeben.

Nächster Schritt nach Protokoll-Commit: additive Implementierung und synthetische
Qualifikation. Noch kein neuer Start numerisch angenommen oder Feldfit gestartet.

## Implementierung vor Targetdaten

Erste15 synthetische Sparse-CP-Kontrollen bestehen in2,09s: aktive native
Werte/VJPs, beide zentralen Schrittweiten, Symmetriekopien, verschiedene
Spulenquadraturgrößen, Cacheinvalidierung bei Basisänderung, feste unnormierte
Flächengewichte, echter Mindestabstand bei Nullstrafe sowie ungültige/degenerierte
und cutoff-nahe Daten. Ruff besteht. Das ersetzt noch nicht die vollständige
128²-Ressourcenmatrix und keinen magnetischen Startupnachweis.

Vor deren erster Ausführung präzisiert: acht frische Prozesse, native und Sparse
getrennt für beide Klassen/Spulenauflösungen. Je13 festgelegte Zustände inklusive
voller Gradienten an fünf Kontrollzuständen, acht zentraler Wertprobes und
Cache-/Wiederherstellungskontrollen. Kanonischer B²-Zahlenweg explizit auf
rekonstruiertes(bt*et+bp*ep) der gebundenen64²-Archive festgelegt; keine strikte
Gleichheit unterschiedlicher Summationswege voraussetzen. Diese Präzisierungen
liegen vor der Ressourcenmatrix und vor neuen Projekt-Feldwerten.

Die übrigen Bausteine sind separat implementiert: frischer benannter Feldadapter
(40 erste Kontrollen), unabhängige Archiv-/Geometrie-/Zielfunktions-/FD- und
Auflösungsrechnung (64 Kontrollen) sowie Ressourcen-Elternwächter und genaue
Arbeitsbuchhaltung (43 leichte Kontrollen). Die erste gesamte Regression besteht
mit1334 Tests,334 unveränderten Warnungen in163,11s. Sie ersetzt ausdrücklich
nicht die acht separaten großformatigen Ressourcenläufe. Deren Aufrufe werden
nicht versteckt als gewöhnliche Unit-Tests oder übersprungene Pflichtprüfungen
behandelt.

Ein zusätzlicher unabhängiger lesender Review findet einen echten
Provenienz-Alias: der geerbte magnetische Snapshot teilt seine `sources` mit dem
internen Target. Die additive Klasse isoliert diese Rückgabe nun; ein eigener
Mutationstest belegt unveränderte Modell-/Seedquellen ohne zusätzliche native
Aufrufe. Alle41 Adaptertests bestehen nach der Korrektur in8,99s. Alte numerische
Klassen bleiben unverändert. Der erste1334-Testbericht bleibt als Zwischenstand
erhalten. Die abschließende gesamte Regression nach der Korrektur besteht:
**1335 Tests,334 Warnungen, keine Fehler oder Skips,164,25s.** Gegenüber dem
Geometrieabschluss sind163 Bausteinkontrollen hinzugekommen (15/41/64/43).
Ruff im gesamten Repository, Dokumentstruktur und Diffprüfung bestehen.
Quellenhashes und beide JUnit-Berichte stehen im
[Qualifikationsbeleg](../../evidence/clear-coil-field-start-v1-primitives.json).

Nächster separater Ausführungsschritt nach diesem Code-/Dokumentationscommit:

```bash
PYTHONPATH=src MPLCONFIGDIR=/private/tmp/fusion-mpl-cache OMPI_MCA_btl=self \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python scripts/qualify_sparse_coil_surface.py \
  --raw /ABSOLUTER/FRISCHER/RESSOURCENORDNER
```

Diese Matrix ist noch ausstehend; weder die Testzahl noch die lesenden Reviews
ersetzen sie. Keine neuen Projekt-Feldwerte oder VMEC-Aufrufe in dieser Phase.

Der Gesamtworkflow ist noch **nicht** implementiert oder qualifiziert. Sein
separater Entwurf zählt zehn Modelle je physischer Zelle: zwei Qualifikationen,
sechs Diagnosen, zwei Flussmodelle. Vollständig ergibt das262 native Requests
je Zelle (202 Werte einschließlich zehn Initialisierungs-A,60 VJPs),1048 für
die ganze Matrix. Jedes rohe Ergebnis und jeder begonnene Aufruf wird gebunden;
Diagnosen und Flussblöcke verwenden unverändert den ersten N-Seed-Snapshot.
Radial-, Winkel- und Spulenverfeinerung sind direkte Paarprüfungen, nicht nur
Vergleiche aller Ergebnisse mit einem einzigen feinsten Wert. Diese Präzisierung
ist eine Implementierungsanforderung vor ersten Projekt-Feldwerten, kein Pass.
