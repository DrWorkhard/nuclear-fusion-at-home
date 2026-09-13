# Basisabnahme und Bedienung

Stand2026-09-13: **Schritt1 und Schritt2 im geschärften Umfang abgeschlossen.**
Die vollständige frische Wiederholung `foundation-acceptance-v2` bei1aa28b6
besteht den unabhängigen Gesamtaudit. Der erste Lauf bleibt negativ erhalten.
Maßgeblich ist das vorab committene
[Protokoll](FOUNDATION_ACCEPTANCE_PROTOCOL.md), nicht frühere breitere Etappenziele.

## Was wird abgenommen?

Schritt1: lokale gesperrte Referenz-/LPQA-Filamentbasis einschließlich Daten,
Ableitungen, feiner unabhängiger Bewertung und zutreffender Ablehnung.
Schritt2: tatsächlicher reproduzierbarer Optimierungs-/Speicher-/Bewertungszyklus.
Keine Pflicht zu neuem Bestwert, Zulässigkeit oder SoTA. Keine globale QI-,
Orbit-, Mechanik- oder SQuID-C-Zulassung.

## Ein Befehl für die konsolidierte Abnahme

Aus dem Repository in der vorhandenen qualifizierten Root-Umgebung, ohne Sync
oder Installation. Beide Zielpfade müssen neu sein; bestehende Versuche werden
nicht überschrieben. Für Wiederholung andere Namen wählen.

```bash
PYTHONPATH=src .venv/bin/python scripts/run_foundation_acceptance.py \
  evidence/my-foundation-check artifacts/my-foundation-check
```

Der Runner setzt die gespeicherten Einzelthread-/Importumgebungswerte selbst.
Mindestens3GiB freier Platz, laufend2GiB Reserve. Keine parallele schwere Arbeit.
Reihenfolge: vollständige Regression, Ruff, Dokumentstruktur, sechs Pflichtdaten-
Tests, sichtbare Importwarnungsdiagnose, zweimal24 Bundles, separater Zyklusaudit,
alle vier Kandidatenabnahmen, abschließender quellengebundener Gesamtaudit.
Die16 Startreplays je Arm zählen innerhalb der24, nicht zusätzlich.

`run.json` enthält Befehle, Logs, Rückgabecodes und Quellen. `summary.json` enthält
getrennte `step1_pass`/`step2_pass`, physische Kandidatenurteile und ausdrücklich
nicht freigegebene Fähigkeiten. Ein positiver Shell-Rückgabecode bezeichnet die
Basisabnahme, nicht einen zulässigen Spulenentwurf. Bei Fehlern Ausgaben erhalten;
Diagnose und begründete Korrektur vor einem neuen Versuch dokumentieren.

Bediengrenze des separaten Gesamtauditors: Für eine reine Nachprüfung ohne neue
Rechnungen `scripts/audit_foundation_acceptance.py` mit **absolutem Pfad zu
`run.json`** und einem neuen Ausgabepfad aufrufen. Seine strikte Befehlsbindung
vergleicht absolute Pfade. Der Hauptbefehl oben normalisiert automatisch;
relative Ausgabeordner sind dort korrekt unterstützt.

## Einzelnen Iterationszyklus nutzen

```bash
PYTHONPATH=src MPLCONFIGDIR=/private/tmp/fusion-mpl-cache OMPI_MCA_btl=self \
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python scripts/run_foundation_cycle.py \
  evidence/my-cycle-v1 artifacts/my-cycle-v1
PYTHONPATH=src .venv/bin/python scripts/audit_foundation_cycle.py \
  evidence/my-cycle-v1 evidence/my-cycle-v1-audit.json
```

Danach unter derselben Einzelthread-/Importumgebung wie im ersten Befehl:

```bash
PYTHONPATH=src MPLCONFIGDIR=/private/tmp/fusion-mpl-cache OMPI_MCA_btl=self \
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python scripts/run_coil_holdouts.py \
  evidence/my-cycle-v1 evidence/my-cycle-v1-audit.json evidence/my-cycle-v1-validation
```

Der kurze Demonstrator verwendet bewusst den fest qualifizierten Start. Pro Arm
liegen alle207 benannten Parameterpunkte, Werte, Zähler, Start-Jacobian und
Gram-Matrix sowie `best.npz`/`best_field.json` vor. Für spätere Methoden-/Budget-
oder Startvarianten neuen Versuch registrieren; unveränderte physische
Grenzen und benanntes Parametermapping beibehalten. Ein veränderter Start muss
seine Startqualifikation bestehen. Alte Läufe und Protokolle nicht umschreiben.

## Implementierungskontrolle vor nativer Ausführung

Neue Runner verwenden die vorhandenen numerischen Kerne unverändert. Der
Zyklusauditor berechnet Mapping und Gram-Matrix separat und verwendet den
bestehenden Armprüfer mit explizitem24er Limit. Der Gesamtauditor kontrolliert
Quellen/Phasen/Umfang und berechnet physische Freigaben aus gespeicherten Zahlen
neu; er ist kein zusätzlicher unabhängiger Magnetfeldsolver.

18 neue Kontrollen bestehen; zusammen mit den vier bestehenden GN-Workflowtests
22 bestanden in4,29s. Ruff, Dokumentstruktur und Diffprüfung bestanden.
Noch keine neue native Studie. Die Kontrollen prüfen synthetische echte Solveriteration mit zwei24er Pfaden,
Zuordnungsfehler, falsche Flux-/native-/Krümmungs-/Abstandsfreigaben, fehlende
Auflösungen/Quellen, falsche Hashes, NaN, unbelegte Ingenieur-/QI-Freigaben,
JUnit-Skips/Duplikate, zusätzliche Importfehler und gespeicherte Prozessfehler.
Zusätzlich wird die historische Kandidatenbewertung ohne neue Feldaufrufe
nachgerechnet; sie bleibt korrekt negativ.

## Altbestand und Grenzen

Lokaler Tag `foundation-pre-scope-2026-09-13` zeigt auf5971fee. Die automatische
Bestandsprüfung erlaubt neue Dateien und definierte Übersichts-/Journalkorrekturen,
nicht Änderungen alter numerischer Kerne, Protokolle oder Evidenz. Externe
Quellen und bestehende lokale STELLOPT-Anpassungen werden vor/nachher verglichen.

W7-X bleibt im erweiterten Vergleich60/63; erhaltene frische21-Phasen-Evidenz ist
kein neuer Aufbau in dieser Abnahme. Bekannte netCDF-Größenwarnung wird sichtbar
wiederholt, strenger Import bleibt negativ. Pflichtdatenregression ersetzt kein
ABI-Zertifikat. Vorherige QI-/Orbit-/Mechanik- und Optimierungsstudien bleiben als
spätere Forschung erhalten, einschließlich aller negativen Ergebnisse.

## Tatsächliche Ausführung: erster Lauf und Korrektur

`foundation-acceptance-v1` bei028c4cc:718 Tests mit144 bekannten Warnungen in51,48s,
sechs Pflichtdatenidentitäten ohne Skip, Ruff/Dokumentprüfung und alte Import-
Warnungsidentität bestanden. Beide24-Bundle-Pfade exakt,22 gemeinsame und52 Checks
je Arm bestanden. Je49 Anforderungen/24 Cachetreffer/eine verweigerte25.Abfrage,
keine fehlgeschlagenen Auswertungen; acht Solveriterationsberichte je Arm.
Alle vier feinen Kandidatenprüfungen abgeschlossen. Beide Kandidaten korrekt an
feinem Roh-Flux8,191663957639298e-8 gegenüber1e-8 abgelehnt; Geometrie/nativ bestehen.

Der Gesamtaudit scheiterte fail-closed an einem Fehler der neuen Verwaltung:
Archivverweis enthält zusätzlich `bytes`, der Vergleichsverweis nur Pfad/Hash.
Beide verweisen auf exakt denselben Inhalt. Korrektur prüft Pfad/Hash und, wenn
vorhanden, die tatsächliche Dateigröße statt vollständiger Wörterbuchgleichheit.
Neue Negativkontrollen erhalten falsche Größe/Pfad/Hash als Fehler. Zusätzliche
Gesamtauditkontrolle verwendet eine ausdrücklich synthetisch neu gebundene
Manifestkopie und erhaltene Daten; kein neuer Physiklauf und keine Änderung
des ursprünglichen negativen Audits. Alle übrigen Kandidaten-/Warnungs-/externen
Bestandsprüfungen bestehen auch bei separater Nachrechnung.
Alle20 Basis-Workflowkontrollen bestehen nach Korrektur in5,15s; Ruff,
Dokumentstruktur und Diffprüfung ebenfalls. Übersichten bleiben korrekt auf
ausstehender konsolidierter Abnahme, nicht auf erfolgreichem Entwurf.

Originalberichte/Rohdaten bleiben unverändert gespeichert; ausführender Code ist
bei028c4cc abrufbar. **v1 bleibt abgelehnt**, keine nachträglich geänderte Freigabe.
Nach Korrektur und Commit wurde `foundation-acceptance-v2` mit demselben Protokoll,
unveränderten Budgets/Physikgrenzen und vollständig neuer sequenzieller Ausführung
durchgeführt; diese Wiederholung ist nachfolgend abgenommen.

## Abnahme v2: beide Schritte bestanden

Primäre Evidenz: [sequenzieller Ausführungsbericht](../../evidence/foundation-acceptance-v2/run.json),
[Gesamtaudit](../../evidence/foundation-acceptance-v2/summary.json),
[Iterationsaudit](../../evidence/foundation-acceptance-v2/cycle-audit.json),
[alle vier Kandidatenprüfungen](../../evidence/foundation-acceptance-v2/holdouts/summary.json).

| Nachweis | Tatsächliches Ergebnis |
| --- | --- |
| Vollständige Regression | 720 bestanden in53,33s,0 Skips/Fehler;144 bekannte Fixture-Warnungen |
| Strikte wissenschaftliche Integration | Genau sechs vorhandene W7-X-/Goodman-Identitäten bestanden,0 Skips |
| Code und Dokumentstruktur | Ruff und Dokumentprüfung bestanden |
| Erhaltene native Referenz | 21 Aufbauphasen,11 archivierte Dateien und geschützte W7-X-Physik bestätigt; erweiterter Vergleich unverändert60/63 |
| Aktuelle Start-/Ableitungsprüfung | 16 feste Bundles pro Arm, vollständiger Jacobian und separat berechnete native Gram-Matrix bestehen unveränderte Grenzen |
| Tatsächliche Iteration | Je24 Bundles inklusive16 Startreplays,49 Anforderungen/24 Cachetreffer/eine Cap-Verweigerung,0 Auswertungsfehler; acht Solveriterationsberichte |
| Reproduzierbarkeit | Beide vollständigen Parameter-/Wertpfade, Auswahl und Arbeit exakt gleich;22 gemeinsame und52 Armchecks je Wiederholung bestanden |
| Unabhängige Kandidatenprüfungen | Alle vier Phasen/beide Kandidaten/alle Auflösungen; je61 zusätzliche Quellen-/Klassifikations-/Rechenchecks bestanden |
| Umgebungsgrenze | Genau gleiche sichtbare netCDF-Prozessergebnisse0/0/1 und Binärquelle; weiterhin kein strenger Import-/ABI-Pass |
| Erhalt | 1266 historische getrackte Dateien gegen5971fee geprüft; nur erlaubte Übersichten/Journalregeln geändert, externe Quellen unverändert |

Der Gesamtaudit bestätigt alle acht Schritt1-Gates und alle drei Schritt2-Gates.
Die fehlgeschlagene erste Gesamtfreigabe ist **nicht** durch Änderung ihrer
Berichte geheilt worden. Deren damaliger Code bleibt in Git abrufbar.

Beide neuen Kandidaten haben feinen Roh-Flux8,191663957639298e-8 bei Grenze1e-8:
**physisch abgelehnt**, obwohl Geometrie- und zusätzliche native Schirme bestehen.
Das ausgewählte Feld stammt aus Startreplay12, nicht aus einem behaupteten neuen
Solvergewinn. Der Solver hat dennoch nachweislich weitere von x0 verschiedene
Punkte berechnet. Beide Läufe stoppen am Budget, nicht durch bewiesene Konvergenz.
Auswahl-x-SHA256: `1d3dc2db5feb9ca93c64dc11832f41731ba667fcfa0654f35f7b077eef9f3c09`.
Der frühere feinere Forschungsbestwert8,129882e-8 bleibt unverändert erhalten.

Damit sind eine begrenzt verlässliche Arbeitsbasis und tatsächliche
Iterationsfähigkeit belegt, **kein neuer Entwurfserfolg**. Globale QI-Bewertung,
endliche Teilchenbahnen, vollständige Ingenieurmodelle, unabhängige Hardware,
Hosted-CI, ABI-Zertifizierung, SoTA und SQuID-C bleiben ausdrücklich nicht freigegeben.
Plan/Übersichten sind entsprechend aktualisiert. Abschluss dokumentieren und
lokal committen, dann Übergabe; keine weitere Forschung automatisch anhängen.

Abschlusskontrolle nach Übersichtsänderungen: Ruff, Dokumentstruktur und Diff
bestanden. Ein zusätzlicher manueller Audit mit relativem Runpfad wurde wegen
der genannten CLI-Pfadgrenze abgelehnt und
[unverändert erhalten](../../evidence/foundation-acceptance-v2-confirmation.json).
Mit absolutem Runpfad bestätigt derselbe Auditor
[beide Abschlüsse erneut](../../evidence/foundation-acceptance-v2-confirmation-absolute.json),
ohne neue Feldaufrufe oder Änderung eines ursprünglichen Berichts. Diese
Bediengrenze ist kein numerischer Unterschied; der dokumentierte Hauptbefehl
hatte bereits die vollständige Abnahme erfolgreich ausgeführt.
Die20 Basis-Workflowkontrollen bestehen nach den Abschlussänderungen erneut
in4,58s; Dokument- und Diffprüfung ebenfalls.
