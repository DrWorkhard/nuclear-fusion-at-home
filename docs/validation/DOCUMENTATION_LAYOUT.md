# Dokumentationsstruktur und Migration — 2026-09-11

## Regel und Zweck

Auf Nutzerwunsch enthält `docs/` nur drei wissenschaftliche Überblicksdokumente:
Projektfrage, aktueller Ergebnisstand und Arbeitsplan. Details liegen in sieben
zweckgebundenen Unterordnern. Jeder hat eine `README.md` mit Inhaltseinordnung
aller Dokumente; eine tiefere Hierarchie ist ausgeschlossen. Regeln für weitere
Sitzungen stehen in [AGENTS.md](../../AGENTS.md).

Die [Migrationsliste](../../manifests/documentation-layout-v1.json) erfasst alle
53 verschobenen Dateien mit ursprünglichem Pfad, Zielpfad und SHA-256 der
Originalbytes aus Commit `65b046b`. Es wurde kein historisches Ergebnis gelöscht.
Aktuelle Übersichten und Logs dürfen weiterentwickelt werden; das Manifest
bezieht sich ausdrücklich auf die historische Fassung, nicht ewig auf HEAD.

## Provenienz bleibt historisch

Archivierte `evidence/`-JSONs und deren Pfade/Hashes werden nicht umgeschrieben.
Ein alter Pfad ist über die Migrationsliste oder den im Experiment gespeicherten
Git-Commit auflösbar. Für exakte Reproduktion gilt weiterhin der Originalcommit.
Die ursprünglichen Protokollbytes bleiben über Git abrufbar; Verschieben oder
Reparieren eines Navigationslinks ist keine neue wissenschaftliche Präregistrierung.

Aktive Skripte verweisen auf die neuen Protokollpfade. Damit ändern sich ihre
Quelltext-Hashes, aber keine numerischen Formeln. Alte Evidenz darf deshalb nicht
fälschlich gegen heutige Script-Hashes als identisch erklärt werden. Laufprogramme,
die absichtlich die alte Implementierung verlangen, sind am archivierten Commit
auszuführen oder in einem neuen Qualifikationsschritt zu aktualisieren.

## Automatische Kontrollen

`python scripts/check_docs.py` prüft die zulässigen Root-Dateien, maximale Tiefe,
Bereichsübersichten, vollständige Dokumentverlinkung und existierende lokale
Markdown-Dateiziele. Zusätzlich prüft es direkte `docs/...md`-Pfadliterale in
aktiven Python-Skripten. Link-Fragmente und externe Webseiten werden dabei nicht
inhaltlich validiert. Adversariale Tests decken fehlende Übersichten, zu tiefe
Ordner, unindexierte Dateien, kaputte Links und veraltete Skriptpfade ab.

Diese Strukturprüfung ist eine Navigations- und Reproduzierbarkeitskontrolle,
keine erneute wissenschaftliche Prüfung sämtlicher historischer Ergebnisse.

Zusätzlich prüft `PYTHONPATH=src python scripts/audit_documentation_migration.py
evidence/documentation-migration-v1.json` alle ursprünglichen Dokumenthashes
gegen Git und die AST-Gleichheit aller 18 wissenschaftlichen Skripte nach bloßer
Ersetzung der Dokumentpfade. Das Ausgabeverzeichnis darf nicht überschrieben werden.
