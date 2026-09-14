# Eigene QI-nahe Plasmaoberfläche: Arbeitsstand und Bedienung

Stand: 14. September2026. [Festes Protokoll](PLASMA_OPTIMIZATION_PROTOCOL.md).
**Schritt3 noch offen.** Neue additive Such-/Prüfwerkzeuge sind implementiert;
erster Start vor jeder Rechnung wegen Herkunfts-Metadatenprüfung gestoppt.
Noch kein neuer Gleichgewichts- oder Entwurfsbefund. Die früheren Schritte1/2
und sämtliche alten negativen Forschungsdaten bleiben unverändert.

## Implementierung vor erster Rechnung

Vier explizite Randmoden, zwei deterministische Pollrunden mit Cache-/Arbeits-
zählern, separate Kaltwiederholung und201/401-Endpunkte. Jeder Solver schreibt
Input, Request, Log, Wout, Kraftreste und terminalen Zustand. Zeit-/Platzwächter
beenden nur den selbst gestarteten Prozess. Alte Inputs/Wouts werden nicht überschrieben.

Die Zielgröße ordnet je zwei vollständige Teilchenmulden ihren Feldperioden zu.
Alle angefragten s/q-Zellen werden versucht; fehlende/zensierte Mulden erhalten
Fehlereinträge und können keine scheinbaren Nullkosten erzeugen. Der separate
Auditor rekonstruiert die gesamte Pollfolge, prüft Quellen und Änderungen aller
Eingabefelder, kontrolliert gespeicherte Traces durch skalare Fourier-/Geometrie-
Stichproben und integriert Aktionen mit separater64-Punkt-Gaussquadratur.
Physische Zulassung, Prozessabschluss und Vorteil bleiben eigene Aussagen.

27 gezielte Kontrollen bestehen, einschließlich analytisch bekannter Varianz,
fehlender Mulden/Zellen, NaN, falscher Modenzuordnung, manipulierter Auswahl,
unzureichend aufgelöstem Vorteil und falschen Zulassungsflags. Der erste Testlauf
fand eine fehlende Winkelendpunktprüfung im separaten Integrator (24/25 bestanden);
vor jeder neuen Physikrechnung korrigiert. Ein zusätzlicher skalarer Quellencheck
am erhaltenen Wout besteht und weist manipuliertes B zurück. Kandidateninput
durchläuft die echte VMEC++-Modellkonversion unverändert, ohne Solve.

Gesamtsuite vor der letzten zusätzlichen Quellenkontrolle:745 Tests/144 bekannte
Warnungen in68,54s. Danach26 gezielte Tests in0,27s. Ruff besteht. Bekannte
netCDF-/NumPy-Grenzen werden nicht als behoben ausgegeben. Dokument-/Diffprüfung
und lokaler Implementierungscommit erfolgen vor dem ersten neuen Solve.

## Erhaltener erster Startfehler

Bei c9801ba verlangte die neue Quellenprüfung einen direkten Git-Eintrag des
historischen Rohinputs. Er liegt absichtlich im ignorierten Artefaktbaum; seine
Bytes sind bereits durch den committeten Originalbericht gebunden. Der Start
endete vor Verzeichniserzeugung oder Solve. Terminalbefund ist ausdrücklich als
manuelle Übertragung in `evidence/plasma-design-v1-preflight-error.json` erhalten.
Korrektur: direkter Commitnachweis für Berichte/Code/Protokoll, unverändert strenger
SHA-Nachweis für Rohdaten. Zusätzlicher Test schützt diese Trennung. Kein Input,
keine alte Evidenz, keine physische Schwelle verändert. Nächster frischer Lauf: v2.

## Bedienung auf den vorhandenen gesperrten Umgebungen

Alle drei Phasen nacheinander, keine konkurrierenden schweren Rechnungen. Vorher
Code/Protokoll committen und mindestens3GiB frei halten; währenddessen2GiB.
Neue, noch nicht vorhandene Ergebnisverzeichnisse und Berichtsdateien verwenden.
Für jeden Aufruf gilt dieser Umgebungspräfix:

```sh
export PYTHONPATH=src
export MPLCONFIGDIR=/private/tmp/fusion-mpl-cache
export OMPI_MCA_btl=self
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
.venv/bin/python scripts/run_plasma_search.py evidence/plasma-design-v2 artifacts/plasma-design-v2
.venv/bin/python scripts/validate_plasma_design.py evidence/plasma-design-v2 evidence/plasma-design-v2-holdout.json artifacts/plasma-design-v2-holdout
.venv/bin/python scripts/audit_plasma_design.py evidence/plasma-design-v2/summary.json evidence/plasma-design-v2-holdout.json evidence/plasma-design-v2-audit.json
```

Kein Installationsschritt. Ein negatives Auditorergebnis bleibt erhalten und
schließt Schritt3 nicht; keine nachträgliche Grenzwertänderung. Die gespeicherte
ausgewählte Inputdatei ist der reproduzierbare Entwurf, nicht eine Abbildung oder
ein bloßes Parameterarray. Nächster Schritt: registrierte Suche ausführen, dann
Ergebnisse dokumentieren/committen und ohne Auswahlfeedback unabhängig abnehmen.
