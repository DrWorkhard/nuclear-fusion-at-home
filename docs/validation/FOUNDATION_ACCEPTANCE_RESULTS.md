# Basisabnahme und Bedienung

Stand2026-09-13: Implementierung kontrolliert; echte konsolidierte Abnahme noch
ausstehend. Maßgeblich ist das vorab committene
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
  evidence/foundation-acceptance-v1 artifacts/foundation-acceptance-v1
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

## Tatsächliche Ausführung und Abschluss

Noch ausstehend. Erst ein vollständiger bestandener Gesamtaudit erlaubt den
Abschluss beider geschärfter Schritte; danach Dokumentation/Commit und Übergabe.
