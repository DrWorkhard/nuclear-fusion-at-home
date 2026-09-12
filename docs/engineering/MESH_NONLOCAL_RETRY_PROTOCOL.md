# Netzprüfung: Wiederholung nach historischem Quellpfad-Fehlstart

Vor jeder echten Kollisionsrechnung registriert, 2026-09-12. Der Erststart
bei891e8a5 scheitert vor Anlage der Studie und vor einem Netz-Worker. Er bleibt
unverändert unter `evidence/mesh-nonlocal-v1-driver/` erhalten.

Der alte intrinsische Bericht bindet `scripts/check_mesh_integrity.py` mit
SHA c9b6c5c98c80db0bd91780d409b6cf2532f4339400d9039a3ab9ba6e88ee4a8f
an Revision9ee17964f4a4946432437d690fb1a8f18c1d6096. Die heutige Datei hat
einen anderen Hash: bei2f07f95 wurde ausschließlich ihr Dokumentationspfad von
`docs/MESH_INTEGRITY_PROTOCOL.md` zu `docs/engineering/MESH_INTEGRITY_PROTOCOL.md`
geändert. Der numerische Kern und alle sechs Netze sind bytegleich gebunden.
Separater Referenzaudit bestätigt alle elf Verweise: neun aktuell, einer exakt
historisch in Git, ein identisch verschobenes Protokoll. Kein Physikergebnis.

Für die Wiederholung bleibt das [ursprüngliche Protokoll](MESH_NONLOCAL_PROTOCOL.md)
unverändert. Ausschließlich historische Quellcodeverweise dürfen durch den
bereits getesteten Resolver aus der im ursprünglichen Bericht gespeicherten
Git-Revision mit exakt passendem SHA nachgewiesen werden. Jede Auflösung wird
im neuen Studien-/Worker-/Auditbericht explizit ausgewiesen. Keine Wahl anderer
Revisionen, kein Ignorieren nicht auflösbarer Hashes, kein Umschreiben alter
Berichte oder Ausführen alter Skripte.

Netze, Manifeste, aktueller Studiencode und alle neuen Ergebnisverweise müssen
weiterhin gegen ihre tatsächlichen gegenwärtigen Datei-Bytes stimmen; für
physikalische Dateien gibt es keinen Git-Fallback. Alle sechs Auflösungen,
Grenzen,1200s/2M-Paarcaps,2GiB Reserve und unabhängigen räumlichen Auditoren
bleiben identisch. Neue unveränderliche Pfade `mesh-nonlocal-v2` für Studie,
Rohdaten, Schutztreiber und Audit. Vor Ausführung Negativkontrollen für
unauflösbare historische Quellen und veränderte physikalische Netze ergänzen.
