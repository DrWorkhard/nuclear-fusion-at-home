# Räumliche Tetraederprüfung: Kontrollkern vorbereitet

2026-09-12. Die bisherigen sechs strukturierten Spulennetze bestehen nur
intrinsische Qualitäts-/Topologieprüfungen. Das feinste besitzt327000 Tetraeder;
ein vollständiger ungefilterter Paarvergleich wäre unpraktisch. Neue echte
Netz-/Kollisionsrechnungen wurden in diesem Schritt nicht durchgeführt.

## Zwei getrennte Nachweise

Der additive Kern `tetra_nonoverlap.py` prüft Projektionen konvexer Tetraeder
auf Flächennormalen und Kreuzprodukte ihrer Kanten, ergänzt um Koordinatenachsen.
Eine strikt getrennte Projektion liefert eine Trennrichtung. Grundlage:
[Eberly, Method of Separating Axes, Abschnitte2/4](https://www.geometrictools.com/Documentation/MethodOfSeparatingAxes.pdf).
Der Text ist vom20. Juni2022; die Suchmaschine nennt daneben ein neueres Crawl-
Datum, das nicht als Veröffentlichungsdatum verwendet wird.

Unser Kern gibt nur `separated` oder `unresolved` aus. Er speichert Richtung,
Ursprung, Projektionslücke und Sicherheitspolster. Keine gefundene Trennachse
ist ausdrücklich kein bestätigter Überlappungsbefund. Kontakt bleibt unaufgelöst.

Eine unabhängige lineare Optimierung sucht einen gemeinsamen Punkt mit strikt
positiven baryzentrischen Gewichten in beiden Tetraedern. Erst eine getrennte
4x4-Lösung für beide Gewichtssätze plus Rekonstruktions-/Summenprüfung bestätigt
einen positiven inneren Punkt. Ein fehlgeschlagener LP-Lauf, negatives Optimum
oder bloßer Randkontakt ist ebenfalls kein Freigabenachweis. So werden positive
und negative Behauptungen nicht aus demselben heuristischen Boolean abgeleitet.

Numerik: Trennrechnung nach gemeinsamer Translation, normierte Achsen und
1e-10-relatives Polster plus64epsilon für Subtraktion/Projektion; LP-Witness
verlangt Gewichte>1e-10, Summenfehler<=1e-12 und skalierten Rekonstruktionsfehler
<=1e-12. Entartete/nichtendliche Eingaben werden abgelehnt. Das sind konservative
Gleitkommaschirme, keine gerichtete Intervallarithmetik oder formale Zertifizierung
beliebig schlecht konditionierter Geometrie.

## Tatsächlich geprüfte Kontrollen

Zehn Tests bestehen: klare Trennung, trotz überlappender achsparalleler Boxen
getrennte Tetraeder, echte Überlappung, vollständige Einbettung, gemeinsamer
Rand ohne Innenüberlappung, Starrbewegung/Vertexpermutation, ungültige/
entartete Eingaben.32 feste zufällige Tetraederpaare mit Seed624 vergleichen
Achsenprüfung und LP unabhängig; die Kontrollen enthalten getrennte und sich
überlappende Fälle. Ruff/Dokument-/Diffprüfung bestanden.

Die konservative räumliche Vorauswahl ist inzwischen ebenfalls als additiver
Kontrollkern vorhanden: eine deterministische Boxhierarchie zerlegt alle
ungeordneten Elementpaare in getrennte Teilbäume und kleine Blattpaare.
Trennungen brauchen ein positives gepolstertes Boxintervall; Kontakte werden
behalten. Ein vollständiges Ereignisprotokoll und die Identität
`geprüfte Kandidaten + getrennte Paare = N*(N-1)/2` gehören zur Bilanz.
Unvollständig konsumierte Generatoren melden ausdrücklich keine vollständige
Abdeckung. Das ist noch kein Nachweis für echte Spulennetze.

Neun weitere Tests bestehen. Bei96 festen Zufallstetraedern stimmen die
Kandidaten für vier Blattgrößen exakt mit einer unabhängigen vollständigen
Paarprüfung überein; keine Duplikate, alle Knotenboxen gegen ursprüngliche
Vertices nachgeprüft. Kontakte/doppelte Geometrie werden nicht verworfen,
ungültige Indizes und wiederholte Traversierung abgelehnt. Insgesamt19
Geometriekontrollen bestanden. Nächster Schritt: separate Studie an allen sechs
unveränderten Spulennetzen registrieren und danach ausführen/auditieren.
Dieses [separate Netzprotokoll](MESH_NONLOCAL_PROTOCOL.md) ist nun registriert;
es startet erst nach QI-Studie und SLSQP-Nachoptimierung samt deren Abnahmen.
Nachbarpaare, getrennte Netzregionen, vier Grundspulen und spätere Symmetriekopien
müssen explizite getrennte Gültigkeitsbereiche behalten. Noch kein realer
Spulen-Nichtüberlappungsnachweis, keine qualifizierte Wickelpaketorientierung,
keine Verbesserung der ungültigen absoluten linearen Mechanikprognose.
