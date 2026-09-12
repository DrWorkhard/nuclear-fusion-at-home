# Nichtlokale Netzüberschneidung: Streaming-Prüfpfad vorbereitet

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
