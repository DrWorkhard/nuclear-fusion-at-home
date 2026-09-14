# Zwei Wirkungsdomänen: Arbeitsstand und Bedienung

14. September2026. [Registriertes Folgeprotokoll](PLASMA_BALANCED_PROTOCOL.md).
**Phase A abgeschlossen, noch kein zulässiger Entwurf oder Schritt3-Abschluss.** Die erste Form bleibt
[unabhängig abgelehnt](PLASMA_OPTIMIZATION_RESULTS.md). Jetzt beide Domänen und
lokale Wirkungsgrenzen schon bei der Konstruktion berücksichtigen.

## Vor Ausführung geprüfte Implementierung

Getrennte unveränderliche Phasenberichte für Archivauswertung, bedingte
Vorschlagssuche und Kaltendpunkte. Jeder native Solve verwendet unveränderten
alten Worker, Eingabemapper und Ressourcenwächter; zusätzliche breite Diagnostik
und Auswahl werden separat gespeichert. Keine alte numerische Datei geändert.
Der explizit markierte Diagnoseadapter nutzt den vorhandenen Vier-Zustands-
Auswerter, behauptet aber keinen alten Zwei-Poll-Suchlauf. Eigener Gesamtauditor
prüft tatsächliche Quellen, Phasenbedingungen und Auswahl vor physischen Gates.

Das gemeinsame lineare Vorschlagsmodell speichert alle zentralen Differenzen,
142 Nebenbedingungen, Bounds, primalen und dualen Zustand. Der unabhängige
Prüfweg rekonstruiert die Matrix und kontrolliert Zulässigkeit, Dualzeichen,
Stationarität, Komplementarität und Dualitätslücke; keine Gleichsetzung mit
physischer Optimalität. Negative oder unvollständige Daten können keinen
Zulassungspass erzeugen. Eine Archivform verhindert zusätzliche Differenzsolves,
wenn sie bereits die vorab festgelegten Auswahlbedingungen erfüllt.

19 neue Kontrollen beziehungsweise46 zusammen mit dem ersten Plasmalauf bestehen
in0,73s; vollständige Gesamtsuite766 Tests/144 bekannte Warnungen in54,05s.
Ruff besteht. Ein erster neuer Testlauf fand die Python-Tupel-/JSON-Listenform
der LP-Bounds; vor jeder neuen Rechnung vereinheitlicht. Die LP-Threadoption wird
von SciPy mit einem Weiterleitungswarnhinweis an HiGHS gegeben; Warntext wird im
Modellbericht gespeichert, nicht als physische Fehlermeldung oder Warnungsfreiheit
umgedeutet. Keine Installation, kein externer Quelleneingriff.

## Phase A: keine auswählbare Archivform

Bei8693339 alle16 vorhandenen Formen auf sämtlichen35 breiten Zellen gemessen,
ohne einen neuen Gleichgewichtssolve. Keine fehlenden Domänenzellen. Der separate
Audit bestätigt Quellen, alte native Datensätze, alle neuen Aktionen durch
Gaussquadratur, Zellstatistik, Konstruktionsklassifikation und Auswahl: kein Index
zulässig. Einzige Form mit beiden erforderlichen Kostenvorteilen ist Index10;
sie verletzt die lokale Mittelwirkungsgrenze. Kein Ausblenden dieser Grenze,
kein nachträgliches Absenken des Auswahlschirms.

Phase/Audit in `evidence/plasma-balanced-v1/archive.json` und `archive-audit.json`,
Rohtraces unter `artifacts/plasma-balanced-v1/archive`.46 gezielte Kontrollen
bestehen danach erneut in0,66s; Dokument-/Diffprüfung bestanden. Gesamtaussage
bleibt unverändert: Schritt3 offen. Damit ist die vorab festgelegte Bedingung
für Phase B erfüllt: acht kleine neue Differenzsolves, anschließend höchstens
drei reale gemeinsame Vorschläge, ohne weitere Suche in diesem Experiment.

## Phasen ausführen und getrennt bewerten

Der Umgebungspräfix aus dem [ersten Runbook](PLASMA_OPTIMIZATION_RESULTS.md)
gilt unverändert. Neue Pfade verwenden, mindestens3GiB Reserve. Nach jeder
abgeschlossenen Phase Dokumentation/Checks/Commit, erst dann nächste Phase.

```sh
.venv/bin/python scripts/run_balanced_plasma.py archive evidence/plasma-balanced-v1 artifacts/plasma-balanced-v1
.venv/bin/python scripts/audit_balanced_plasma.py archive evidence/plasma-balanced-v1 evidence/plasma-balanced-v1/archive-audit.json
```

Nur wenn `archive.json` keinen ausgewählten Index enthält:

```sh
.venv/bin/python scripts/run_balanced_plasma.py propose evidence/plasma-balanced-v1 artifacts/plasma-balanced-v1
.venv/bin/python scripts/audit_balanced_plasma.py propose evidence/plasma-balanced-v1 evidence/plasma-balanced-v1/propose-audit.json
```

Nur mit tatsächlich ausgewähltem Kandidaten, nicht bei bloßem Modellabstieg:

```sh
.venv/bin/python scripts/run_balanced_plasma.py endpoints evidence/plasma-balanced-v1 artifacts/plasma-balanced-v1
.venv/bin/python scripts/validate_balanced_plasma.py evidence/plasma-balanced-v1 artifacts/plasma-balanced-v1/validation
.venv/bin/python scripts/audit_balanced_plasma.py final evidence/plasma-balanced-v1 evidence/plasma-balanced-v1/final-audit.json
```

Ein Phasenaudit-Pass ist ausdrücklich kein Schritt3-Pass. Nur das positive finale
Ergebnis mit allen unveränderten physischen Gates erlaubt den registrierten
Vakuumabschluss. SQuID-C, globale QI-/Orbitphysik und SoTA bleiben getrennt.

Nächster Schritt: abgeschlossene Phase A samt Audit committen, dann bedingte
Phase B ausführen. Noch keine neuen Gleichgewichtssolves in diesem Folgeversuch.
