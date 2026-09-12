# Strikte wissenschaftliche Regression — 2026-09-12

## Zweck und vorab festgelegter Umfang

Schließt eine Software-Prüflücke in Schritt 1: fehlende W7-X-Rohdaten konnten
auch bei ausdrücklich gewünschter wissenschaftlicher Integration als Skip
enden. Die optionale Kern-CI darf weiterhin ohne große Rohdaten laufen; der
dedizierte wissenschaftliche Pfad verlangt alle Daten ausdrücklich.

`scripts/run_scientific_integration.py OUTPUT` benutzt nur die aufrufende
Python-Umgebung, installiert nichts und verlangt einen neuen Ausgabeordner.
Er setzt `FUSION_REQUIRE_QI_DATA=1` und `FUSION_REQUIRE_W7X_DATA=1`, führt exakt
die bestehenden sechs Tests aus und prüft anschließend den JUnit-Bericht auf
die sechs eindeutigen Testnamen, null Skips, null Fehler und null Fehlschläge.
Unterprozessstatus, Bericht, Textlog, Codehashes und Revision werden erfasst.

- Zwei Goodman-Metadatenfälle nfp1/nfp2.
- Drei eingefrorene Vakuum-Bouncewirkungsregressionen, unverändert s=0,5,
  fünf Pitchwerte, 16 Feldlinien, relative Toleranz 1e-3.
- Ein W7-X-Regressionstest mit den vorhandenen versionspassenden Ausgaben,
  korrekten Toleranzen und erhaltener erweiterter 60/63-Abweichung; manipulierte
  Hashbindung muss weiterhin abgelehnt werden.

Der Prüfer wird **vor** seiner Ausführung committet. Erwartung: vorhandene
Root-Daten bestehen, isolierter Kern-Checkout ohne W7-X-Daten scheitert sichtbar.
Beide Ausgaben werden erhalten. Keine neue physikalische Zielgröße oder Toleranz.

## Softwarekontrollen und Grenzen

Acht Kontrollen bestehen: fehlende QI-/W7-X-Dateien sind optional ein Skip,
verbindlich ein Fehler; korrekter Sechs-Test-Bericht besteht, Skip, Fehler,
Fehlschlag, fehlender oder doppelter Test werden abgelehnt. Vollsuite 288
bestanden, 11 bekannte Warnungen, Ruff bestanden. Drei Formatlängen korrigiert.

Ein Bestehen heißt ausschließlich: **sechs vorhandene Rohdatenregressionen**
sind wirklich gelaufen. Kein neuer Solverlauf, kein frischer nativer Build,
keine vollständige QI-/Maximum-J-Qualifikation, kein Abschluss von Schritt 1.
Die Testwerte und Annahmekriterien wurden nicht verändert. Der laufende
bundlebudgetierte SLSQP-Suchcode bleibt unberührt.

## Ergebnisse

Ausführung und Gegenkontrolle stehen noch aus.
