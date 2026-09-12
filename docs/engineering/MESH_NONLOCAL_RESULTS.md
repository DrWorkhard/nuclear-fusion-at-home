# Nichtlokale Netzüberschneidung: fünf vollständige Pässe, feinster Test unvollständig

**Späterer gesonderter Abschluss:** Das einzige unvollständige Netz besteht
inzwischen die [separate vollständige Wiederholung](MESH_FINE_COMPLETION_RESULTS.md)
einschließlich exaktem2M-Präfix und erneutem unabhängigem Audit. Dieser historische
sechs-Netze-Bericht und sein ursprünglicher Paarcap bleiben unverändert.

## Tatsächliche räumliche Prüfung und unabhängiger Audit abgeschlossen

2026-09-12, Retry-Ausführung bei f5ccea2 nach Quellauflösung gemäß ae8d05a.
Alle sechs ursprünglichen Netze unverändert geprüft; keine geänderten numerischen
Kerne, physikalischen Grenzen oder Caps. Alle sechs Worker terminal, Studie
wegen der fehlenden Gesamtfreigabe mit regulärem Exit2 abgeschlossen.

| h auf Geräteskala/m | Tetraeder | Tatsächliche nichtlokale SAT-Paarprüfungen | Ergebnis |
| --- | --- | --- | --- |
| 0,05 | 2622 | 2608 | vollständig bestanden |
| 0,04 | 13104 | 50381 | vollständig bestanden |
| 0,03 | 17472 | 67008 | vollständig bestanden |
| 0,02 | 58860 | 327459 | vollständig bestanden |
| 0,015 | 139680 | 911188 | vollständig bestanden |
| 0,010 | 327000 | 2000000 | festgelegter Paarcap, unvollständig |

In allen tatsächlich geprüften nichtlokalen Paaren gibt es einen positiven
Trennnachweis; keine LP-Aufrufe, bestätigten Innenüberschneidungen, unaufgelösten
Paarfälle oder Rechenfehler. Dies schließt beim letzten Netz unbekannte
Überschneidungen im **noch ungeprüften Bereich** ausdrücklich nicht aus.

Separater Audit besteht für alle sechs gespeicherten Zertifikate, einschließlich
der korrekten unvollständigen Klassifikation. Er rekonstruiert sämtliche
gespeicherten Box-/Indexpartitionen aus Originalvertices und prüft alle
3.358.644 gespeicherten Einzelpaar-Trennnachweise durch separate Projektion,
ohne neue Trennachsensuche oder LP. Der feinste Scan hat52.642.012.461 der
53.464.336.500 ungeordneten Paarmöglichkeiten im Boxbaum abgearbeitet;
822.324.039 bleiben in nicht traversierten Paarbereichen. Zusätzlich61 bereits
gelieferte Blattkandidaten sind noch nicht verarbeitet. Die Paarzählung ist
disjunkt, aber nicht mit der Zahl tatsächlich nötiger SAT-Aufrufe gleichzusetzen.

126MiB neue Rohzertifikate; etwa274s für den feinsten Scan inklusive Speicherung,
kein Zeitcap/Plattenabbruch. Dort7.923.543 verarbeitete gemeinsame-Vertex-Paare
ausdrücklich ausgenommen. Für keinen Fall gelten die Schirme für alle
Nachbarpaare, vollständige Symmetriebaugruppen, echte Wicklungspakete oder
mechanische Gültigkeit. Ursprünglicher magnetisch unzulässiger Netzquellentwurf,
nicht die zuletzt nachoptimierten Filamente. G5 und Schritt1 bleiben offen.

Evidenz: `evidence/mesh-nonlocal-v2/summary.json`, sechs Worker/Logs,
`evidence/mesh-nonlocal-v2-audit.json`, beide Schutztreiber, Rohdaten
`artifacts/mesh-nonlocal-v2/`. Alle unabhängigen Quellen-/Zähler-/Negativtests
bestanden. Diese fest budgetierte Studie ist geschlossen; eine vollständige
Prüfung des letzten Netzes braucht ein getrenntes Protokoll, keine Umdeutung
oder nachträgliche Verlängerung dieses Caps. Nächster bereits registrierter
Physikteiltest: QI-Vergleich im gemeinsamen geraden Feldlinienwinkel.

## Erster echter Start vor Netzrechnung gestoppt

Bei891e8a5 sind SLSQP und alle Abnahmen geschlossen. Der Startversuch scheitert
aber im historischen Quellhash-Check, bevor ein Netz gelesen oder ein Worker
gestartet wird. Nur der Dokumentationspfad des alten intrinsischen Skripts
hat sich geändert; exakte ursprüngliche Bytes sind an dessen gespeicherter
Git-Revision vorhanden. Alle elf ursprünglichen Quellenverweise unabhängig
aufgelöst, Netze und numerischer Kern unverändert. Der negative Treiberbericht
bleibt erhalten; [getrennt festgelegter Retry](MESH_NONLOCAL_RETRY_PROTOCOL.md)
soll die historische Provenienz explizit auflösen, ohne Physikchecks zu umgehen.

Der bei ae8d05a registrierte Retry-Pfad ist jetzt implementiert: explizite
historische Codeauflösung in Studie, Worker und Auditor, ausschließlich an der
ursprünglichen Revision und mit exakt passendem SHA. Reale sechs Netze/Manifeste
bestehen die unveränderte Vorprüfung; die historische Skriptquelle wird als
`historical_git`, der numerische Kern als `current` ausgewiesen. Kein neuer
Kollisionsaufruf bei diesem Vorabtest. Acht Quellen-/Resolverkontrollen bestehen,
einschließlich beschädigter physikalischer Dateien ohne historischen Fallback.
Numerische räumliche Kerne und Caps unverändert. Neue Ausführung unter v2 folgt.

## Aufbewahrte Implementierungsvorbereitung

2026-09-12. [Protokoll](MESH_NONLOCAL_PROTOCOL.md) bei2a9e5b6 vorab registriert.
Noch keine der sechs realen Spulenvernetzungen neu untersucht. Die Ausführung
bleibt hinter der laufenden zusammengesetzten SLSQP-Suche und deren Abnahmen.

Der neue Scanner speichert jede tatsächlich geprüfte nichtlokale Paar-ID samt
Trennachse beziehungsweise LP-Innenpunkt zeilenweise komprimiert; komplette
Boxhierarchie und Paarereignisse separat. Geteilte Vertexindizes zählen als
ausgenommene Nachbarpaare. Verarbeiteter Kandidaten-Präfix und vom Boxrechner
bereits gelieferte Kandidaten sind verschiedene Zähler, besonders bei Abbruch
innerhalb eines Blatts. Weder Cap noch Fehler gelten als vollständige Prüfung.

Ein separater Streaming-Auditor rekonstruiert die gesamte Paarpartition und
prüft jede gespeicherte Zeile gegen die Originalvertices. Er liest keine
Produzenten-Kandidatenliste und ruft weder deren Traversierung noch Trennachsen-
Suche/LP auf. Unaufgelöste/positive Innenpunktfälle bleiben explizit negativ;
die vollständige Prüfung eines negativen Ergebnisses ist kein Zulässigkeitspass.

Fünf Workflow-Kontrollen bestehen: getrennte Boxen, echter Innenpunkt, bloßer
Kontakt, ausgenommene gemeinsame Vertices, partieller Paar-/Zeitcap,
eingespritzter Rechenfehler und Ablehnung veränderter Zähler/falscher Freigabe.
Alle Kontrollen benutzen kleine synthetische Daten. Zusammen mit den bisherigen
Kernen/Auditoren39 gezielte Tests; Ruff/Dokument-/Diffprüfung bestanden.
Die echte sechs-Netze-Orchestrierung und ihre Dateiprovenienz sind als Nächstes
zu ergänzen; es gibt weiterhin keine Spulenvolumen- oder Mechanikfreigabe.

## Sechs-Netze-Ausführung und Datei-Audit implementiert

Die echten Dateitreiber sind jetzt vorbereitet. Sie verlangen alle sechs
Originalhashes, beide ursprünglichen Manifeste und die bestandene intrinsische
Prüfung; nur lineare Tetraeder mit allen vier unveränderten Spulentags. Keine
Koordinaten-/Netzänderung. Jede Zelle erhält ihren eigenen Workerbericht,
1200s-Prozesscap und Rohpfad; Timeouts/Fehler bleiben als solche in der vollständigen
sechs-Zeilen-Bilanz. Bei3GiB vor Start/2GiB laufender Reserve bleiben folgende
negative Zellen erhalten, statt aus der Matrix zu verschwinden.

Der Start wird zusätzlich durch den vorherigen committed SLSQP-Studien-/Audit-
und Vier-Phasen-Abschluss geschützt. Der Dateiauditor bindet die Quellnetze,
Workerberichte und komprimierten Zertifikate und prüft jeden verfügbaren Scan
mit den separaten Partition-/Witness-Kernen. Nicht verfügbare Timeout-Ergebnisse
werden nicht als unabhängig geprüft ausgegeben. Gültige partielle Zertifikate
sind weiterhin kein vollständiger Geometrienachweis.

Vier neue Dateiquellen-/Vorgänger-/Meshio-Kontrollen bestehen; Gesamtregression
589 Tests mit69 bekannten NumPy/netCDF-DeprecationWarnings bestanden,
Ruff/Dokument-/Diffprüfung bestanden. Kein echtes altes Spulennetz wurde in
diesem Implementierungsschritt auf Kollision untersucht. Nächster Schritt bleibt
die tatsächliche registrierte Ausführung nach den SLSQP-Abnahmen.
