# Geometrisch angenommene Spulen: Feldstart- und Auflösungsqualifikation

Vor Implementierung und neuen Feldwerten registriert,19. September2026.
[Geometrieabschluss](../geometry/CLEAR_COIL_INITIALIZATION_RESULTS.md) bei323cfdd,
[Gesamtziel Schritt4](COUPLED_DESIGN_OPTIONS.md). Dies ist ausdrücklich **keine
Suche**, keine gemeinsame Plasma-/Spulenoptimierung und kein Schritt4-Abschluss.
Alle bisherigen Fehler, numerischen Kerne und Protokolle bleiben unverändert.

## Frage, Quellen und feste Matrix

Können wir die geometrisch angenommenen Starts mit quellgebundener Flussnormierung,
verlässlichen Werten/Ableitungen und ausreichender lokaler Rasterauflösung in
einen späteren Feldfit übernehmen? Der letzte Pilot scheiterte auch an Singularnähe
und fehlender Verfeinerung; geometrische Sicherheit allein garantiert deren
Behebung nicht. Kein neues Gleichgewicht, Druckmodell, Download oder Installation.

Genau vier physische Zellen: Referenz/Schritt3-Entwurf × n6/M5 beziehungsweise
n8/M7. Unveränderte401er Inputs/Wouts und die exakt bei727dec8 konstruierten,
bei323cfdd abgeschlossenen `n6-shape-d100mm`/`n8-shape-d100mm`-Snapshots.
Binder verlangt beide einzeln angenommenen ausgewählten Sätze, deren genaue
Rohsnapshotreferenzen und vollständige12/168-Geometrieabnahme. Globales
`all_pass` allein genügt nicht. Keine Kreisalternative nach Feldsichtung.

Jede physische Zelle erhält beide MethodenN/V mit je zehn festen Qualifikations-
bundles. Physische Diagnostik nur einmal je Zelle, nachdem identische N/V-
Startfelder, Strom und Normierung geprüft sind; unterschiedliches J/Gradient
ist beabsichtigt. Insgesamt höchstens80 vollständige Werte-/Gradientenversuche.

## Additiver Adapter, Ströme und Zielfunktion

Neue Klasse setzt sämtliche benannten geometrischen Fourierkoeffizienten **vor
dem ersten Spulenfeld-/Potentialaufruf**. Nicht den alten Kreis-Konstruktor
aufrufen und nachträglich nur`x` setzen. Wiederverwendbare eingefrorene
Wert-/Ableitungsformeln dürfen geerbt werden; neue Initialisierung, Raster,
Quellen und Buchhaltung werden gesondert qualifiziert. Keine Globalmonkeypatches.

Grundspulenströme weiterhin fest100kA, stellaratorsymmetrische Kopien mit
korrektem Vorzeichen. Tatsächlicher gemeinsamer Strom ausschließlich über
a=Phi_ziel/Phi_unit aus dem orientierten256-Punkt-Randlinienintegral; genau
ein expliziter initialer A-Aufruf je neuem Modell auf der echten Startgeometrie.
Vorzeichen, Nichtnullgrenze1e-12Wb und Normierungsableitung wie im
[ersten Pilot](COUPLED_COIL_PILOT_PROTOCOL.md), keine Nullfeldlösung.

Gemeinsamer B²-Maßstab pro Target aus dessen bereits unabhängig qualifiziertem
archiviertem64²-Innenfeld auf s=0,25/0,5/0,75. Diesen positiven Zahlenwert
quellgebunden einmal festlegen und in sämtlichen Klassen, Methoden, Probes und
feineren Diagnosen unverändert benutzen. Keine neue Normierung je Innenraster.

Konstruktionsraster:64² Rand pro voller Feldperiode,256 Punkte je Spule,
32² je Innenradius. Separate128²-Volltorusfläche für die Abstandsstrafe.
JN,JV undN/V-Gewicht0,05 unverändert. Geometriegewichte/Grenzen ebenfalls:
L-Strafe0,5*sum(max(L−3,5,0)²), Krümmungsstrafe wie natives Lp(p=2,threshold10/m)
mit Gewicht1e-4, alle physischen CC-/CP-Strafen mit Schirmen0,06/0,08m und
Gewicht1000. Dies sind weiterhin weiche Konstruktionsstrafen, keine Zulassung.

128²-CP-Daten dürfen keine ungebundenen dichten Paararrays erzeugen. Additiver
speicherbegrenzter Adapter berechnet exakt dieselbe diskrete Doppelintegral-
Zielfunktion: je Kurve sum(v_i*area_j*max(d0−r_ij,0)²)/(N_curve*N_surface).
Vollständige KDTree-Ballnachbarn,eps0,workers1, punktweise Verarbeitung; kein
Nachbarcap, keine Rasterauslassung. Analytische Orts- und Tangentenableitung
durch native Kurven-VJPs; feste Oberfläche erhält keine freien DOFs.
Baumsuchradius nur als Broadphase um128*eps*max(1,Koordinatenmaßstab,d0)
nach außen polstern, danach eigene Distanz und unveränderten ursprünglichen
d0-Hinge verwenden; Nachbarindizes deterministisch sortieren. Flächenpunkte und
Parameternormalen unveränderlich kopieren. Keine Oberflächenableitung oder
Co-Designgradientenqualifikation aus dieser festen-Fläche-Schnittstelle ableiten.
Geschwindigkeitsnullen, r_ij=0 oder nichtfinite Größen scheitern explizit.
Auch der tatsächliche Gittermindestabstand wird vollständig berechnet.
Cache bei jeder abhängigen Kurvenänderung invalidieren.

## Synthetische Qualifikation vor Projekt-Feldwerten

Neue benannte Seedabbildung, sämtliche24/32 Kopien, Stromvorzeichen, gecachter
Wertzugriff, Initialisierungszählung und eingefrorene B²-/Stromparameter prüfen.
Keine Quelle darf einen Geometriesnapshot in einen erfundenen magnetischen
Snapshot umetikettieren. Quellen-/Koeffizienten-/Klassenmutationen müssen scheitern.

Sparse CP gegen ursprüngliche native Wert-/Ableitungsformel prüfen: tatsächliche
128²-Surface und ncoil256/512, jeweils volle n6/n8-Symmetrie. Aktivierte CP- und
CC-Fälle, nicht nur sichere Nullstrafen; direkte Analytik und zentrale Differenzen.
Wert-/VJP-Gegenrechnung relativ≤5e-10 oder absolut≤1e-12; FD-Schirme wie unten.
Je maximal120s, eigener frischer Prozess, Peak-RSS≤1,5GiB als Qualifikationsschirm.
Bei Fehler kein echter Lauf; keinen durch Skip oder kleinere Testdaten ersetzen.
RAM-Schirm ist gemessener Peak nach Ausführung, kein behauptetes hartes Betriebssystemlimit.
Keine parallelen schweren Tests/Rechnungen.

## Startup und unveränderte Ableitungsschirme

Pro Methode genau seed, acht zentrale Probes und seed-repeat. Richtungen
sin(k+1),cos(k+1), jeweils euklidisch normiert; h=1e-5 und5e-6m, beide Vorzeichen.
J-Richtungsableitung: relativer Fehler≤2e-4 oder absolut≤1e-8; alle vier Checks
müssen bestehen. Beide Schrittweiten bleiben auch bei Aktivierungswechsel einer
weichen Strafe erhalten. Startwert und voller Gradient exakt wiederholen.
Jede Probe unabhängig aus gespeicherten Feld-/Geometriedaten nachrechnen.

Direkte B/A-Gegenrechnung auf64 gleichmäßig ausgewählten Punkten aus jedem
aufgezeichneten Rand-/Innen-/Loopraster: maximaler Komponentenfehler≤5e-10
relativ zur maximalen absoluten unabhängigen Komponente, kein Nullnenner.
Benannte Kurven, Tangenten, Zielpunkte und Flächengewichte unabhängig prüfen.
Innere Targets aus den gebundenen64²-Archiven exakt subsamplen;32/64-Gitter
sind hier bereits qualifiziert. Neue128²-Zielrekonstruktion ist nicht Teil dieser Studie.

## Sechs feste Diagnosestufen je physischer Zelle

Nach Konstruktion Strom aus dem ersten N-Seedbundle bei256 Spulen-/Loop-Punkten
einfrieren; N/V müssen denselben Wert liefern. Ursprünglicher magnetischer
Snapshot bleibt Quelle aller Diagnosen, keine feinen neu normierten Snapshots.
Alle Stufen auch bei bereits erkennbar schlechtem Feld speichern:

| Stufe | Rand | Spulenpunkte | Innen je Radius | Randversatz |
| --- | ---: | ---: | ---: | --- |
| 0 |64²|256|32²|0|
| 1 |128²|256|32²|0|
| 2 |128²|512|32²|0|
| 3 |128²|512|32²|halbe Zelle in beiden Winkeln|
| 4 |64²|256|64²|0|
| 5 |64²|512|64²|0|

Randnormal-RMS: Paare0→1,1→2,2→3; Innenvektor-RMS:0→4,4→5.
Wie zuvor jeweils≤1% relativ zum gröberen Wert oder≤1e-7 absolut. Keine
automatische Wahl des günstigsten Rasters und keine Behauptung, diese lokale
Prüfung belege Konvergenz beliebiger künftiger Suchpunkte. Alle24 Zustände mit
rohen Feldern/Potentialen, Strom, Maßstab und unabhängigen Gegenrechnungen halten.

Zusätzlich pro physischer Zelle bei256 und512 Spulenpunkten unveränderter
Strom: drei Linienraster theta256/512/1024 und sämtliche sechs Flächenraster
nrho16/32 × theta256/512/1024. Je Block18 gezählte B/A-Wertaufrufe, keine
Gradienten; insgesamt acht Blöcke/72 Flussraster. Signierte Fanfläche,64-Punkt-
direkte Gegenrechnung, Stokes-, Winkel-/Radial- und Zielflussfehler jeweils≤1e-6
relativ. Auch der256→512-Spulenvergleich der jeweiligen Flüsse muss≤1e-6 sein.

Unveränderte Seed-Geometrie wird exakt auf die vorherige positive kontinuierliche
Geometrieabnahme zurückgeführt; keine nachträgliche Verfeinerung ihrer Auswahl.
FD-Probes sind keine Kandidaten. Freie spätere Spulenformen erben keinen
Konvexitäts-, Selbstschnitt- oder Abstandsbeweis.

## Status, Ressourcen und Abschluss

`startup_pass` verlangt Quellen-/Arithmetik-/Geometrieidentität, beide N/V-
Ableitungsqualifikationen, deren physische Identität, alle direkten Feldprüfungen,
alle Fluss- und alle fünf Verfeinerungsgates. Numerischer Werkzeugpass darf trotz
großen physischen Feldfehlers bestehen. Separat `physical_seed_pass`: zusätzlich
alle unveränderten Eintrittsschirme RMS≤1e-4,Max≤1e-3,Innenvektor-RMS≤0,01,
|I|≤500kA und die vorhandenen Geometrie-/Flussschirme auf allen Pflichtgittern.
`search_allowed`, `transfer_pass`, `step4_pass` in dieser Studie stets false.
Eine negative Zelle bleibt negativ; keine automatische Reparatur oder Suche.

Vier physische Zellen seriell, ein Thread. Pro Zelle maximal20 Vollbundles,
sechs wertbasierte Diagnosen und zwei Flussblöcke; keine Cachegutschriften.
Zwei Qualifikationsmodelle, sechs Diagnosemodelle, zwei Flussmodelle: genau
zehn deklarierte Initialisierungs-A-Aufrufe bei vollständiger Zelle,40 insgesamt.
Modellerzeugung zählt separat, auch wenn späterer Konstruktor-/Feldaufruf scheitert.
Native Werte/VJPs und Zusatz-B/A-Arbeit separat bilanzieren; keine als kostenlos
versteckten Konstruktoraufrufe oder Wert-Replays.

Elternwächter1800s pro physischer Zelle ab Workerstart,0,5s Takt/5s
Terminierungsfrist; rechtzeitige Endmarke und exakter Prozesscode0 erforderlich.
Jeder Versuch vor Start persistieren; bei Fehler/IO/Budget letzten erfolgreichen
Checkpoint unverändert halten und unvollständige Arbeit separat kennzeichnen.
Neue Artefakte geschätzt≤1GiB; Platte vor jeder Zelle≥3GiB, laufend≥2GiB.
Keine schweren Paralleljobs oder Änderungen externer Quellen/Umgebungen.

Protokoll zunächst lokal committen, Implementierung synthetisch qualifizieren
und committen, erst dann echte Zellen rechnen. Alle vier unabhängig abnehmen,
Ergebnisse/Fehlschläge dokumentieren und committen. Erst anschließend über ein
neues Suchprotokoll entscheiden. Keine Lockerung früherer negativer Gates.
