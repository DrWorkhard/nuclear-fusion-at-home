# Gemeinsamer Einstieg für Menschen und AI-Agenten

20. September 2026. Dünne gemeinsame CLI über unveränderten wissenschaftlichen
Programmen. Sie vereinheitlicht Aufruf, Profilentdeckung und Pfadbehandlung,
nicht die Physikmodelle. **Version1 unterstützt genau ein festes Studienprofil,
keine beliebigen neuen Entwurfsdateien.**

## Ohne Rechnung beginnen

Im Forschungscheckout mit der vorhandenen Pythonumgebung:

```bash
PYTHONPATH=src .venv/bin/python -m fusion_baselines --help
PYTHONPATH=src .venv/bin/python -m fusion_baselines profiles
PYTHONPATH=src .venv/bin/python -m fusion_baselines profiles --json
.venv/bin/python fusion.py profiles --json
```

`fusion.py` ist der Einstieg direkt im Projektroot, ohne gesetztes `PYTHONPATH`.
Der historisch installierte Befehl `.venv/bin/fusion-baselines` bleibt dagegen
unverändert für Datenaufnahme/Umgebungsprüfung; er erhält diese neuen Unterbefehle
nicht. Seine Implementierung und die Paketkonfiguration gehören zur eingefrorenen
Basisabnahme. Keine Installation/Synchronisierung erforderlich oder automatisch ausgelöst.
Discovery und Hilfe laden keine NumPy-/SciPy-/netCDF-/nativen Rechenbibliotheken.
Für die Forschung weiterhin zuerst [Projektstand](../STATUS.md),
[Arbeitsplan](../PROJECT_PLAN.md) und [Arbeitsregeln](../../AGENTS.md) lesen.

Maschinenlesbare Entdeckung liefert Schema, Profil-ID, unterstützte Operationen,
Eingaben, Ausgaben, Voraussetzungen, Ressourcen und Bedeutung der Exitcodes.
`supports_candidate_input: false` ist verbindlich, nicht nur eine Beschreibung.
Es gibt kein `--design`, keinen freien Backendpfad und keine stillschweigende
Auswahl eines anderen Modells.

## Profil clear-coil-field-start-v1

Der vorhandene [Feldstartablauf](../optimization/CLEAR_COIL_FIELD_START_PROTOCOL.md)
rechnet dieselben vier festgelegten Zellen: Referenz-/eigener Plasmaentwurf,
jeweils sechs/acht Grundspulen. Er erzeugt tatsächliche Feld-/Ableitungsdaten,
optimiert aber keine neue Spulenform. `audit` rekonstruiert und prüft den
gespeicherten vollständigen Lauf unabhängig. Grenzwerte, Raster, Normierung,
Quellenbinder und Ressourcenwächter bleiben in den bestehenden Backends.

| Operation | Unveränderter Backend | Ausgabe |
| --- | --- | --- |
| evaluate | scripts/run_clear_coil_field_start.py | Neuer Ordner mit run.json, Workerprotokollen und Roharrays |
| audit | scripts/audit_clear_coil_field_start.py | Neue JSON-Datei mit numerischer und physischer Entscheidung |

**Voraussetzungen:** Forschungscheckout einschließlich `scripts/`, bestehende
qualifizierte native Umgebung, gepinnte externe Quellen, Vorgängerevidenz und
alle referenzierten lokalen Rohdaten. Ein installiertes Wheel oder ein Git-Clone
allein enthält die benötigten ignorierten Artefakte nicht. Historische absolute
Pfade/Hashes dürfen zur Portierung nicht einfach umgeschrieben werden; ein neuer
Rechner benötigt separat reproduzierte und qualifizierte Daten.
[Umgebung und Grenzen](ENVIRONMENT.md).

## Geplanten Aufruf zuerst ansehen

```bash
PYTHONPATH=src .venv/bin/python -m fusion_baselines evaluate \
  --profile clear-coil-field-start-v1 \
  --output artifacts/my-field-start \
  --dry-run
```

Das schreibt keine Dateien und startet keinen Unterprozess. Das JSON zeigt
den genauen Backendbefehl, Checkout, normalisierte Pfade und Änderungen der
Unterprozessumgebung. Es prüft nur Checkout-/Dateipfade, **nicht** vollständige
Quellenverfügbarkeit, Physik, Bibliothekskompatibilität oder freien Speicher.
Diese eigentliche Zulassung erledigt erst das Backend beim echten Aufruf.

Relative Eingabe-/Ausgabepfade beziehen sich auf das aktuelle Aufrufverzeichnis,
nicht auf einen später gewechselten Checkout. Außerhalb des Checkouts kann man
`--project-root /absoluter/pfad/fusion` angeben. Der Unterprozess läuft mit dem
aufrufenden Pythoninterpreter, Checkout als Arbeitsverzeichnis und dessen `src/`
als explizitem `PYTHONPATH`; keine Shellauswertung. Die drei numerischen
Threadgrenzen werden nur für diesen Unterprozess auf1 gesetzt.

## Vorhandenen Lauf nachprüfen — empfohlener erster echter Aufruf

```bash
PYTHONPATH=src .venv/bin/python -m fusion_baselines audit \
  --profile clear-coil-field-start-v1 \
  --run artifacts/clear-coil-field-start-v1/run.json \
  --output artifacts/my-field-start-audit.json
```

Der Lauf muss samt allen referenzierten Dateien lokal vorhanden sein. Auch
`audit` unterstützt `--dry-run`. Neue Ausgabe verwenden; existierende Dateien,
Ordner und symbolische Links werden nicht überschrieben. Ein Audit ist eine
echte unabhängige Nachrechnung gespeicherter Daten, kein neuer nativer Feldlauf
und kein Optimierungslauf.

## Registrierte Studie erneut ausführen

Bewusst ohne parallele schwere Jobs und mit ausreichenden Ressourcen:

```bash
PYTHONPATH=src .venv/bin/python -m fusion_baselines evaluate \
  --profile clear-coil-field-start-v1 \
  --output artifacts/my-field-start

PYTHONPATH=src .venv/bin/python -m fusion_baselines audit \
  --profile clear-coil-field-start-v1 \
  --run artifacts/my-field-start/run.json \
  --output artifacts/my-field-start-audit-after-evaluation.json
```

Vier serielle Worker, jeweils maximal1800s inklusive Import/Quellenbinder;
mindestens3GiB Reserve vor jeder Zelle und2GiB währenddessen. Jede vollständige
Zelle zählt262 native Requests. Kein automatischer Audit, Retry, Suchlauf,
Gleichgewichtssolve oder Budgetoverride. Fehler-/Teilresultate bleiben erhalten;
ein Neustart verlangt einen neuen Ausgabepfad. Nicht bloß für einen CLI-Smoke-Test
eine gesamte neue Studie rechnen.

## Ergebnisse richtig lesen

Die CLI gibt die regulären Backend-Exitcodes unverändert weiter:

| Aufruf | Exit0 bedeutet | Andere Ausgänge |
| --- | --- | --- |
| profiles / --dry-run | Entdeckung beziehungsweise Aufrufplanung erfolgreich | Keine Rechen-/Physikentscheidung |
| evaluate | Producer vollständig; unabhängige Abnahme steht aus |1 bei Fehler/unvollständiger Produktion |
| audit | Numerischer startup_pass |2 bei numerischer Ablehnung oder Auditfehler; JSON-status unterscheiden |

Dispatcher-/Checkout-/Dateifehler geben1 zurück, argparse-Nutzungsfehler2.
SignalabbruchN wird als128+N ausgegeben, Unterbrechung als130. Der bestehende
Auditwriter verwendet einen festen `.tmp`-Geschwisterpfad; auch dieser muss neu
sein, damit erhaltene Zwischenstände oder Links nicht überschrieben werden.
Ausgaben/Fehlermeldungen der Backends bleiben sichtbar. **Exit0, `all_pass` oder
`startup_pass` sind hier keine physische Entwurfszulassung.** Insbesondere der
bereits abgeschlossene Feldstart besteht numerisch, während
`physical_seed_pass=false` und `step4_pass=false` bleiben.

## Weitere Profile und neue Entwürfe

Die Pythonmethoden `evaluate(x)`/`snapshot(x)` bleiben für die Konstruktion
erhalten; der neue CLI-Befehl `evaluate` ist kein identischer universeller
Einzelpunktaufruf. Ein beliebiger neuer Snapshot benötigt künftig ein eigenes
versioniertes Eingabe-/Prüfprofil mit Quellenbindung und qualifiziertem Ablauf.
Die inzwischen [abgeschlossene52-Zustands-Perturbationsstudie](../geometry/COIL_PERTURBATION_RESULTS.md)
hat eigene spezialisierte Start-/Auditprogramme; sie wird durch Version1 dieser
CLI weder gestartet noch als universelles Einzelentwurfsprofil angeboten.

Erweiterungen an der expliziten Registry vornehmen, bestehende Backends/Protokolle
unverändert lassen, Annahmeumfang und Exitsemantik dokumentieren und Dispatch-/
Negativtests ergänzen. Keine dynamischen Pythonimporte oder ausführbaren Befehle
aus einer vom Entwurf mitgelieferten JSON-Datei übernehmen. Keine alten
LPQA-/Plasma-/Ingenieurprüfungen als austauschbare Profile umetikettieren.

## Implementierungsprüfung

64 unabhängige Dispatch-/Negativtests bestehen: leichte Discovery ohne native
Imports, Pfad-/Umgebungs-/Exitcodekontrollen, Rootlauncher ohne PYTHONPATH und
expliziter Byteerhalt der alten CLI/Paketkonfiguration. Erste Gesamtregression:
1897 bestanden,3 Erhaltungsprüfungen gescheitert,334 bekannte Warnungen,195,14s.
Ursache war der zunächst versuchte direkte Ausbau der eingefrorenen alten CLI.
Ihre Bytes sind wieder exakt hergestellt; neue Parser/Startpunkte sind rein
additiv. Keine alte Prüfbedingung geändert. Fehlgeschlagenes JUnit unter
`artifacts/project-entrypoints-v1-qualification/regression.xml` bleibt erhalten.
Die vollständige korrigierte Regression besteht **1904 Tests**,334 bekannte
Warnungen,0 Fehler/Skips in208,42s. JUnit unter
`artifacts/project-entrypoints-v2-qualification/regression.xml`, Hash
`a9b85b88aa95f0141e9632d3652572931d7a92774c10e994b0564e656d1f91d1`.
[Quellgebundene Softwarequalifikation](../../evidence/project-entrypoints-v1-qualification.json)
hält beide Versuche fest. Repository-Ruff, Dokumentstruktur/Diff und zusätzliche
neun Dokumenttests bestanden. Abschließender lesender Review findet keine
weiteren Blocker; keine externe wissenschaftliche Begutachtung.
Nach Implementierungscommit `caa1333` wurde der vorhandene Feldstart über den
Rootlauncher tatsächlich neu auditiert. Exit0,2434 gebundene Referenzen;
**sämtliche Ergebnisfelder exakt wie im ursprünglichen Audit**, ausgenommen
die erwartbar neue Git-Metadatenzeile `auditor_repository`.
Alle vier numerischen Pässe und physischen Ablehnungen bleiben erhalten.
[Replaybeleg](../../evidence/project-entrypoints-v1-replay.json), Ausgabe unter
`artifacts/project-entrypoints-v1-replay/audit.json`, SHA256
`8e0af0395d3ddc7e561c786ea99984ac6f79a185894ae2a942f389bb398c7936`.
Keine neue native Feldstudie, Optimierung oder Gleichgewichtsrechnung;
unabhängige Rekonstruktion vorhandener Rohdaten. CLI-Aufgabe damit abgeschlossen,
Danach wurde die kumulative Geometriestudie fortgesetzt und separat geschlossen;
deren Qualifikation erweitert den hier dokumentierten CLI-Umfang nicht automatisch.
