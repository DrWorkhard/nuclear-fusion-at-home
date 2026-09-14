# Schritt4A-Pilot: gepaarte, flussnormierte Filamentspulen

Vor Implementierung/Ausführung registriert, 14. September 2026.
[Methodenreview und Gesamtumfang](COUPLED_DESIGN_OPTIONS.md). Ein Fit-Pilot,
kein vollständiger physischer Transfer oder Schritt4-Abschluss. Keine neuen
Gleichgewichtssolves, Installationen oder Änderungen vorhandener Quellen.

## Feste Quellen und Vergleichsmatrix

Unveränderte401er Eingaben/Wouts der Goodman-Referenz aus `plasma-design-v2`
und des angenommenen Entwurfs aus `plasma-balanced-v1`. Beide Inputs in Git,
Wouts durch die abgeschlossenen Audits gebunden. Alle Randmoden erhalten:
VMEC-mpol5, ntor10, nfp2, R00=1m, |Randfluss|=π/100Wb, Vakuum. Keine implizite
Übertragung der alten LPQA-Spulen, Grenzwerte oder Reaktorskalierung.

Acht Zellen: zwei Ziele × zwei Spulenklassen × zwei Konstruktionsmethoden.
Klassen: sechs Grundspulen/Fourierordnung5 (=24 physische Spulen) und acht
Grundspulen/Ordnung7 (=32 physische Spulen). Gleiche Anfangskreise je Klasse:
R0=1m, R1=0,35m, gleichmäßig in einer halben Feldperiode, SIMSOPT-Konvention
einschließlich stellaratorsymmetrischer Kopien. Ein gemeinsamer Serien-Strommaßstab;
keine freien unabhängigen Grundspulenströme in diesem Pilot. Nullgeschwindigkeit,
degenerierte Kurven und erkannte exakte Selbstschnitte sind ungültige Filamente.
Diese Architekturwahl
ist eine begrenzte Kostenklasse, keine optimale Spulenanzahl oder Reaktorauslegung.

Explizite Parameterordnung: Grundspulenindex, dann kartesische Achse x/y/z,
jeweils c0,s1,c1,...,sM,cM, alle in Metern. Änderungen pro Koeffizient höchstens
0,12m gegenüber seinem Startwert. Kein runtimeabhängiger Optimizable-Name als
physikalische Identität. Sämtliche tatsächlichen physischen Kopien mit benannter
Basis-/Rotations-/Flip-/Stromzuordnung exportieren und getrennt rekonstruieren.

## Physische Flussnormierung, ohne Nullfeldlösung

Für jede Form zunächst Einheitsmaßstab mit100kA pro Grundspule auswerten.
Φu=∮A_u·dl auf dem ungekürzten Randquerschnitt bei phi=0 (256 theta-Punkte):
periodische Trapezquadratur von A(r(theta))·r_theta mit analytischem Fourier-
Tangentenvektor, keine Polygonsehnenquadratur.
Die Orientierung ergibt sich aus der parametrisierten R/Z-Kontur; das Vorzeichen
des Zielflusses aus dieser Orientierung und dem toroidalen Zielfeld. Der Betrag
bleibt exakt der gespeicherte Randfluss. Keine bloße Gleichsetzung von VMEC-
Flussvorzeichen und beliebiger Integrationsrichtung. Konkret: positive orientierte
R-Z-Fläche hat Normale−e_phi. Die toroidalen Zielkomponenten bei phi=0 auf allen
drei inneren Zielradien müssen ein gemeinsames von null verschiedenes Vorzeichen
haben. Zielflussvorzeichen=−sign(R-Z-Fläche)·sign(Bphi).

Flächengegenprüfung: Zentrum ist das R/Z-Mittel des1024-Punkt-Randquerschnitts;
r(rho,theta)=Zentrum+rho·(Rand(theta)−Zentrum), rho∈[0,1]. Signierte Flächennormale
aus r_rho×r_theta (nicht ihr Betrag), radiale Gaussquadratur und periodisches theta.
Konstantes nichtnull Jacobian-Vorzeichen für rho>0 und R>0 fordern; sonst kein
stillschweigender Ersatz durch eine andere Fläche. Analytischen toroidalen
Kreisfall einschließlich Vorzeichen vor tatsächlicher Target-Qualifikation testen.

Der gemeinsame Maßstab a=Φziel/Φu setzt B=aBu und I=a·100kA. Nichtfinite Daten,
|Φu|≤1e-12Wb oder ein Orientierungswechsel zum Start sind Fehler, keine Nullkosten.
Die Ableitung muss die Normierung enthalten:
dB=a·dBu−(a/Φu)·Bu·dΦu. Ungeclippte native B-/A-VJPs, nicht der vorhandene
SquaredFlux-Nullgradient. Die Flussidentität wird unabhängig durch direkten
Vektorpotential-Summenwert und eine Flächenintegration des tatsächlichen B geprüft.

## Zwei vorab festgelegte Konstruktionsmethoden

Randgitter:32×32 über eine volle Feldperiode,128 Punkte je Spulenperiode.
Innere Zielfelder: exakt die vorhandene qualifizierte Fourierrekonstruktion bei
s=0,25/0,5/0,75, jeweils16×16. Positionen und Vektoren aus derselben VMEC-
Winkelauswertung, keine Mischung mit PEST-Punkten. Keine ungeprüfte
Halbgitterextrapolation zum Rand.
Fester B²-Maßstab = Mittel von |Bziel|² über die inneren Punkte, unabhängig von
Spulenparametern. Randgewichte sind positive Flächenelemente, auf Summe1 normiert.

- **N:** JN=0,5·Summe w(B·n)²/B²maßstab plus Geometriestrafen.
- **V:** JN+0,05·JV plus dieselben Geometriestrafen;
  JV=0,5·Mittel|B−Bziel|²/B²maßstab auf allen inneren Punkten.

Das zweite Ziel ist eine zu prüfende Hilfsstrategie, keine neue QI-Messung oder
behauptete neue Methode. Beide Methoden speichern JN, JV, tatsächliche Feldnorm
und rohe Fehler. Werte verschiedener Gesamtzielfunktionen nicht direkt als
Methodensieg vergleichen. Keine Änderungen von Gewichten nach Ergebnissichtung.

Geometriestrafen aus vorhandenen nativen Primitiven: Summe der
`QuadraticPenalty(CurveLength(curve),3.5,"max")` über Grundspulen mit Gewicht1;
`CurveCurveDistance`-Schirm0,06m
mit Gewicht1000 über alle physischen Spulen (`num_basecurves=4*nbase`);
`CurveSurfaceDistance`-Schirm0,08m mit Gewicht1000 über alle physischen Spulen
und ein separates64×32-Volltorus-Plasmagitter; Summe
`LpCurveCurvature(p=2,threshold=10/m)` über Grundspulen mit Gewicht1e-4.
Die Volltorus-Geometrie verhindert künstlich fehlende Nachbarn in der zweiten
Feldperiode; das Randfeldziel bleibt32×32 pro voller Feldperiode.
Diese weichen Strafen
sind keine Zulassung. Kein zusätzlicher verdeckter Start- oder Selektionsbonus.

## Qualifikation vor Optimierung

Alle acht Startzustände: benannte Input-/Flächen-/Symmetrieidentität, unabhängige
Fourierkoordinaten/-ableitungen und direkte Biot–Savart/A-Rechnung. Auf64 vorab
gleichmäßig ausgewählten Feldpunkten relativer Maximalfehler≤5e-10 (Nenner jeweils
maximale absolute Komponente, positiver endlicher Maßstab). Φziel-Vorzeichen
muss zum inneren toroidalen Feld passen. Flächenfluss gegen Linienintegral≤1e-6
relativ, mit16/32 radialen Gauss-Punkten und256/512/1024 theta-Punkten überprüft.
Auch Linienintegral und Winkelverfeinerung müssen innerhalb1e-6 übereinstimmen.

Zwei deterministische normierte Richtungen sin(k+1) und cos(k+1), zentrale
Schritte1e-5m und5e-6m. J-Ableitung mit relativer Abweichung≤2e-4 oder absolut≤1e-8.
Je Start höchstens zehn vollständige Werte/Gradienten inklusive Wiederholung;
alle Punkte/Fehler speichern. Wiederholter Startwert/-gradient exakt.
Scheitert ein Start, keine Optimierung dieser Zelle. Kein Reparieren durch
lockere Grenzen; Implementierungsfehler vor einem neuen frischen Lauf beheben.

## Begrenzte Suchläufe und Auswahl

Je Zelle L-BFGS-B mit analytischem Gradient, den festen Boxgrenzen, maxiter128,
maxls20, ftol1e-12, gtol1e-9. Zusätzlicher strikter Zähler: höchstens128
Wert-/Gradientenversuche, höchstens600s Suchlauf; keine Cachegutschrift. Jeder
Aufruf zählt, auch wiederholte Punkte, verworfene Liniensuchpunkte und Fehler.
Die erste Suchauswertung ist erneut der ungestörte Start und wird mitgezählt;
die höchstens zehn vorherigen Qualifikationsbundles sind separat bilanziert.
Die Suchzeit beginnt unmittelbar vor dem ersten Suchbundle. Ein Elternprozess
begrenzt sie mit0,5s-Prüftakt; ein dann laufendes Bundle wird abgebrochen und
als unvollständiger Versuch erhalten (maximal5s Terminierungsfrist). Letzter
vollständiger Checkpoint bleibt unverändert, keine Auswahl ungespeicherter Arbeit.
Genau eine Runde, keine automatische
Budgetverlängerung. Acht Zellen seriell, ein Thread, keine schweren Paralleljobs.

Auswahl pro Zelle: kleinster endlicher eigener Gesamtzielwert ausschließlich
im Suchledger (einschließlich seines ungestörten Starts), Gleichstand frühester
Aufruf. Differenzprobes der Qualifikation sind keine Auswahlkandidaten.
Der gemeinsame physische
Strom wird aus diesem Ledgerpunkt und dessen256-Punkt-Normierung eingefroren;
keine erneute Normierung an feineren Gittern, die eine schlechte Diskretisierung
verstecken könnte. Start bleibt zulässiger
Rückfall für den Prozess, nicht eine verbesserte Form. Vollständiges Ledger und
gesonderte Solver-/Budget-/Fehlerstatus speichern. Ausgewählte Parameter einfrieren;
erneute Konstruktion in frischem Objekt muss Werte/Felder/Geometrie exakt wiedergeben.
Dies ist Kandidaten-Replay, keine behauptete Wiederholung des gesamten Suchpfads.

## Separate feinere Prüfung und Aussagegrenze

Alle acht ausgewählten Zustände prüfen, auch schlechte. Feldgitter/Spulenpunkte:
(64×64,256), (128×128,256), (128×128,512) und letztere Auflösung um eine halbe
Zelle in beiden Oberflächenwinkeln verschoben. Innerer Vektorvergleich bei32×32
und64×64 auf denselben drei Radien. Aktions-/QI-Input bleibt unverändert; keine
falsche Auswertung der gewünschten VMEC-Flächen als tatsächlich realisierte Flächen.

Separat berichten: flächengewichteter RMS und Maximum |Bn|/|B|, roher JN, innerer
dimensionslosen Vektor-RMS=sqrt(2JV), Strom, Fluss, Längen/Krümmung und alle
physischen Coil-/Plasmaabstände. Der B²-Maßstab bleibt der Konstruktionswert;
feinere Zielgitter dienen nicht zur heimlichen Neunormierung.
Direkte unabhängige B/A-Gegenrechnung wiederum64 feste Punkte je Raster;
Flächenfluss16/32-Gauss×256/512/1024-theta gegen die jeweiligen Linienintegrale.
Winkelverfeinerung und unabhängige Stokes-Gegenrechnung jeweils≤1e-6 relativ,
bei demselben eingefrorenen Strom. Kein Punkt auf einer Spule.
Für flächengewichteten RMS(|Bn|/|B|) gilt Verfeinerung≤1% relativ zum gröberen
Wert oder1e-7 absolut für die Paare64→128 bei256 Spulenpunkten,256→512
Spulenpunkte bei128×128 und unverschoben→verschoben bei128×128/512.
Für dimensionslosen inneren Vektor-RMS dieselben Grenzen für32→64 bei256
Spulenpunkten und256→512 bei64×64. Alle drei Innenradien bleiben enthalten.
Verschobene Gitter sind keine punktweise Gleichheitsprüfung verschiedener Orte.

Ein **Eintrittsschirm für spätere Transferphysik**, kein physischer Schritt4-Pass:
RMS≤1e-4, Maximum≤1e-3, innerer Vektor-RMS≤1e-2, Flussfehler≤1e-6, |I|≤500kA,
alle Längen≤3,5m, Krümmung≤12/m, Coilabstand≥0,06m, Plasmaabstand≥0,08m.
Geometrie auf1024 Kurvenpunkten und256×256 Volltorus-Oberfläche; konservative
Fourier-/Lipschitzpolster für Zwischenpunkte berichten. Kann eine Schranke nicht
bewiesen werden, bleibt das Gate offen. Nichtlokale Selbstnähe gesondert melden;
vollständige Wicklungspakete/Baugruppen sind hier ausdrücklich nicht qualifiziert.
Diese SI-Grenzen sind neu gesetzte Pilotbedingungen, keine universellen Standards.

Alle Grenzen und alle Raster müssen bestehen, sonst kein Eintrittsschirm-Pass.
Unabhängiger Auditor prüft gebundene Quellen, Auswahl, Parameter, Normierung,
Felddarstellung, tatsächliche Arbeit und Schirme. `transfer_pass` und `step4_pass`
bleiben in diesem Pilot immer false. Keine universelle Rangfolge aus einem Start.
Negative Fits verurteilen nur diese Architektur/Budget/Methode, nicht das Plasma
oder die prinzipielle Realisierbarkeit. Selbst ein Eintrittspass benötigt danach
eigene reale Feldlinien-/Flächen-/Wirkungs- und Druck-/Robustheitsstudien.

## Evidenz und Ressourcen

Protokoll committen, additive Implementierung synthetisch testen/committen, erst
dann reale Qualifikation/Suche. Geschätzte neue Artefakte unter1GiB; Platzprüfung
≥3GiB vor Beginn, ≥2GiB währenddessen. Kein Solve, großer Download oder Build.
Phasenweise dokumentieren/prüfen/committen; Fehlschläge unverändert behalten.
Über Folgestudien erst nach abgeschlossener separater Bewertung entscheiden.
