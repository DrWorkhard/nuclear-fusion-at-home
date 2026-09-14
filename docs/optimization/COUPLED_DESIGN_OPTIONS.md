# Schritt 4: Wege zur gekoppelten Plasma-/Spulenentwicklung

14. September 2026. Neuer ausdrücklicher Nutzerauftrag nach dem
[Schritt3-Abschluss](../qi/PLASMA_BALANCED_RESULTS.md). Zuerst Optionen unabhängig
prüfen, dann begrenzte Versuche iterieren. Keine Neuheitsbehauptung aus bloßer
Methodenwahl. Die angenommene Vakuumform bleibt unverändert verfügbar.

## Arbeitsziel und Abgrenzung

Die fehlende Verbindung ist derzeit: ideale Plasmaoberfläche → reale Spulen →
tatsächlich erzeugtes Feld → dessen Flächen und Physik. Ein kleiner Feldfehler
auf der gewünschten Oberfläche schließt diese Kette nicht allein. Schritt4
nennt außerdem endlichen Druck, Baubarkeit und Robustheit. Diese Ziele bleiben
Teil des Gesamtpakets; ein erfolgreicher Vakuum-Spulenfit wird nicht zu einem
vollständigen Schritt4-Abschluss umdefiniert. SoTA bleibt Schritt5.

## Optionen und vorläufige Rangfolge

| Weg | Nutzen | Wesentliche Voraussetzung / Risiko | Entscheidung |
| --- | --- | --- | --- |
| Gepaarte klassische Filamentrealisierung | Zeigt, ob Referenz und neue QI-nahe Form unter denselben Spulenanforderungen erzeugbar sind | Normalfeldfehler allein kann Feldamplitude, Inseln und QI-Verlust verbergen | Zuerst; notwendige Vergleichsbasis, noch kein Co-Design |
| Alternierende oder gemeinsame kleine Rand-/Spulenschritte | Direkte Verbindung der vier qualifizierten Plasmamoden mit tatsächlich gerechneten Spulen | Lokale Ableitungen garantieren keinen endlichen Fortschritt; kleine Vertrauensradien und reale Probes nötig | Bevorzugter nächster Konstruktionsweg |
| Reduzierte gemeinsame Richtung durch Eliminierung leicht nachführbarer Spulenänderungen | Zeigt, welche Plasmaänderung den schwer erzeugbaren Feldanteil reduziert | Skalierung, Regularisierung und Spektral-Cutoff vorab festlegen | Aussichtsreiche zweite Co-Design-Methode; kein beanspruchtes neues Prinzip |
| REGCOIL-/QSS-Oberflächenstromproxy | Günstiger Realisierbarkeitsschirm während Plasmaoptimierung | Wicklungsfläche, Stromnorm und Diskretisierung können Ranking bestimmen; reale Spulen weiterhin nötig | Reserveweg; Implementierung lokal nicht vorhanden |
| Direkte Spulenoptimierung mit impliziten Boozer-Flächen | Bewertet Flächen im erzeugten Vakuumfeld statt nur auf Wunschoberflächen | Neuer Flächensolve/QI-Anschluss; kleines Residuum ist keine globale Topologiequalifikation | Späterer alternativer Zweig nach qualifiziertem Spulenstart |
| Sofortiger neuer finite-β-Solver, globale Suche oder lernender Ersatzrechner | Größerer Suchraum beziehungsweise günstigere teure Auswertung | Neue Qualifikation und Daten nötig; beschleunigt sonst einen falschen Maßstab | Nicht als Einstieg; später mit messbarem Zusatznutzen |

Gemeinsame feste-Rand-/Spulenoptimierung ist etabliert, einschließlich getrennter
Ableitungen und anschließender Prüfung im realisierten Feld.
[Jorge et al. (2023)](https://arxiv.org/abs/2302.10622).
Die Unterscheidung leicht und schwer erzeugbarer Feldanteile hat ebenfalls eine
literarische Grundlage; einfache Randglätte ist kein gleichwertiger Ersatz.
[Landreman und Boozer (2016)](https://arxiv.org/abs/1601.05741).

REGCOIL regularisiert das inverse Oberflächenstromproblem;
[Landreman (2017)](https://arxiv.org/abs/1609.04378). Der aktuelle QSS-Preprint
verwendet einen solchen Feldfehlerschirm bereits während der Randoptimierung,
auch für QI. Kritisch für eine Übernahme: λ=0 während der Optimierung, Randphysik
statt gesamter Volumendomäne, QI-Trade-off-Fall ohne erfüllte Symmetrie-Zielschwelle.
Wir übernehmen deshalb weder einen Neuheitsanspruch noch seine Schwellen als
universelle Standards. [Yu et al. (August 2026)](https://arxiv.org/html/2608.03122v1).

## Drei unabhängig beauftragte Agentenreviews

Die Agenten erhielten verschiedene lesende Prüfaufträge und erarbeiteten ihre
Erstempfehlungen unabhängig. Danach wurde ein konkreter Pilotvorschlag zur Kritik
geteilt. Es sind Reviews innerhalb derselben Agentenumgebung, keine unabhängige
Institution, externe Begutachtung oder zweite experimentelle Bestätigung.

| Reviewer / Auftrag | Wichtigste Einwände | Konsequenz |
| --- | --- | --- |
| `step4_physics_review`: physische Kette und Abnahme | VMEC setzt verschachtelte Flächen voraus; bei Druck muss das Plasmafeld berücksichtigt werden; feste absolute Bouncefelder benötigen unveränderte Flussnormalisierung | Tatsächliche Feldlinien und Wirkungsübertragung bleiben eigene Pflichtgates; Vakuum zuerst, Druck nicht streichen |
| `step4_methods_review`: Literatur und Methodenvergleich | Spulenproxy ist kein Abschluss; identische Budgets/Architekturen nötig; Quotient gestörter/nomineller Fehler kann schlechtere Ausgangsformen bevorzugen | Zwei Zielgleichgewichte, explizite Kostenklassen, absolute Robustheitsgrenzen; kleine tatsächliche gemeinsame Schritte statt bloßer Modellprognosen |
| `step4_code_review`: lokale APIs und Integrationsrisiken | Alter Export ist LPQA-spezifisch; native Fluxableitung besitzt Nullplateau; GP-Kernel wirkt im Kurvenparameter, nicht allgemein in Bogenlänge | Neue additive Adapter und ungeclippte Ableitung; benannte Geometrie; später neue korrekt definierte Störverteilung |

Bestätigter lokaler Bestand: SIMSOPT und direktes Biot–Savart/Tracing importierbar;
VMEC++0.7.3 in separater Umgebung. Kein direkt nutzbares REGCOIL, virtual_casing,
DESC oder altes root-VMEC-Modul. Vorhandene Beispiele allein sind keine
Qualifikation. Unter82 sichtbaren lokalen Daten-Dateien keine Spulendateinamen;
keine Aussage über weltweite Verfügbarkeit. Keine Installation nötig für den Einstieg.

Der alte freie-Rand-Pfad beschränkt vier Grundspulen/16 physische Spulen,
mpol/ntor auf6, nzeta24 und ns31 und setzt Vakuumprofile. Unsere angenommene Form
hat VMEC-mpol5 (= maximal m4), ntor10 und ns401. Ein alter Export würde also
Randmoden verlieren und die Flussnormalisierung verändern. Alte Ergebnisse und
Code bleiben erhalten; neue Adapter dürfen diese Annahmen nicht übernehmen.
Ebenso ist die feste-Rand-Metadatenprüfung (Randinput=Randoutput) kein gültiges
Gate für eine tatsächlich bewegte freie Grenze.

## Geplante Teilpakete und ehrliche Abschlussgrenzen

1. **4A — Realisierung und Transfer:** Gepaarte Spulenfits für alte Referenz und
   neue Form; unabhängige Feld-/Geometrie-/Flussprüfung. Danach tatsächliche
   Flächen/Topologie und Erhalt der QI-relevanten Wirkung prüfen. Ein erster
   Fit-/Softwarepilot allein schließt nicht einmal den gesamten Transfer ab.
2. **4B — Gemeinsame Iteration:** Coil-only-Kontrolle gegen alternierende und
   reduzierte gemeinsame Vorschläge, gleiche Starts und ausgewiesene Budgets.
   Mindestens ein echter physischer Vorteil nach unabhängiger Abnahme, nicht
   lediglich ein kleineres lineares Modell oder neue lauffähige Schnittstelle.
3. **4C — Druck und Einschluss:** Konsistentes Außen-/Plasmafeld, vorab definierte
   Druck-/Stromzustände, freie Antwort und Auflösung. Endliche Teilchenbahnen
   gesondert qualifizieren; eingefrorene Driftidentitäten reichen nicht aus.
4. **4D — Baubarkeit und Robustheit:** Endliche Geometrie, nachvollziehbare
   Wicklungspaket-/Lastannahmen und tatsächliche Störungen aller physischen
   Kopien; unabhängige Prüfziehungen und absolute physische Grenzen.

Quantitative Gates je Teilstudie werden vor neuen Rechnungen registriert.
Die von Reviewern vorgeschlagenen1e-4 RMS/1e-3 Maximal-Normalfeldfehler oder50%
Erhalt des Schritt3-Gewinns sind begründete Projektvorschläge, keine Standards
und noch kein ausgeführter Nachweis. Ein voller Schritt4-Pass verlangt die
vorab definierten Teilpakete, nicht das nachträgliche Streichen offener Physik.

## Erster ausführbarer Vergleich

Verglichen werden reine Randfeldanpassung und ein zusätzlicher innerer
Feldvektor-Term auf s=0,25/0,5/0,75. Letzterer könnte tangentiale Abweichungen
früh sichtbar machen; er ist im Vakuum sinnvoll, darf bei Druck nicht unverändert
als Spulen-Zielfeld verwendet werden. Zwei Spulenkomplexitätsklassen und beide
Plasmaformen verhindern einen einseitigen Vergleich. Jeder Versuch bekommt
dieselbe physische Flussnormierung, benannte Freiheitsgrade, feste Budgets und
separate feinere Prüfung. Vor Optimierung sind insbesondere Fluss-Ableitung,
Fourierabbildung und unabhängiges Biot–Savart zu qualifizieren.

Keine alten Protokolle, Kerne, Quellen oder Fehlschläge überschreiben. Kein
Push, Autorenkontakt oder Ressourcenaufbau ohne belegten Bedarf. Aktueller
Platz vor Einstieg rund9,1GiB; mindestens3GiB vor/2GiB während Rechnungen erhalten.
