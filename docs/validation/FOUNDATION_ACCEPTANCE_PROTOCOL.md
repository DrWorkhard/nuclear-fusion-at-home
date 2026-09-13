# Geschärfte Basisabnahme: Schritt1 und prinzipielle Iterationsfähigkeit

2026-09-13, vor neuer Abnahme registriert. Expliziter Nutzerauftrag: Basis fertigstellen,
grundsätzlich iterieren können; keine starke neue Lösung oder SoTA-Leistung nötig.
Dies ist eine **neue Etappenabgrenzung**, kein nachträglicher Pass alter Entwürfe.
Altbestand bei5971fee bleibt unverändert in Git und den Rohdaten erhalten.

## Unterstützter Umfang

Lokaler gesperrter Python-/SIMSOPT-/StellCoilBench-Pfad, LPQA-Festoberfläche,
vier Fourier-Grundspulen Ordnung8/16 Kopien/207 Freiheitsgrade mit festem Gesamtstrom.
Unveränderte Konstruktions- und unabhängige physikalische Grenzen der bestehenden
Studien. W7-X dient als versionsgebundene Gleichgewichtsregression; Goodman als
bekannte Daten-/eingefrorene Bouncewirkungsregression, nicht als globaler QI-Score.

Ausgeschlossen: neue Plasmaoptimierung, globale QI-/maximum-J-Zulassung, endliche
Teilchenbahnen, vollständige reale Wicklungspakete/Mechanik, Hardwareunabhängigkeit,
Hosted-CI und SQuID-C-Reproduktion. Diese Erweiterungen bleiben offen und dürfen
von einem Basispass nicht automatisch freigegeben werden.

## Schritt1-Gates

1. Aktuelle vollständige lokale Tests, Ruff und Dokumentstruktur bestehen;
   JUnit zählt keine Auslassungen oder Fehler. Pflichtintegration separat exakt
   die sechs vorhandenen W7-X-/Goodman-Testidentitäten ohne Skip.
2. Erhaltener frischer21-Phasen-Aufbau und archivierte Binär-/Eingabe-/Woutdaten
   sind hashgebunden. Vorliegende W7-X-Physikabnahme besteht; erweiterter Vergleich
   bleibt60/63 mit genau pres,presf,chipf. Kein neuer Build oder Solverlauf behauptet.
3. Geschlossene vollständige Feld-/Ableitungsqualifikationen werden gebunden.
   Der kurze reale Zyklus wiederholt16 feste Startbundles und vollständige
   Start-Jacobian-/native-Gramprüfung; dieselben Toleranzen1e-12/1e-10 wie vorher.
4. Alle vier vorhandenen unabhängigen Kandidatenabnahmen laufen für beide neuen
   Smoke-Kandidaten: Feld/Geometrie, kontinuierliche Krümmung, Spulenabstand,
   zusätzliche native Bedingungen. Alle Auflösungen unverändert erhalten,
   auch bei Fluxablehnung. Fehlerfreie Ablehnung ist kein Prüfwerkzeugfehler.
5. Fehlende Quellen, falsche Hashes/Zuordnung, unvollständige Phasen, vertauschte
   numerische Freigaben oder behauptete ausgeschlossene Fähigkeiten werden in
   Negativkontrollen zurückgewiesen. Physische Grenzwerte nicht lockern.

Umgebung: netCDF4-Größenwarnung separat erneut in frischen Prozessen sichtbar
machen. Erwartete bisherige0/0/1-Ausgänge und gleiche Binärquelle müssen belegt
bleiben. Strenger Import bleibt fehlgeschlagen; kein Filter hinzugefügt, kein
ABI-Zertifikat. Daten-I/O wird durch die verpflichtenden realen Regressionen
geprüft. Bekannte Fixture-DeprecationWarnings berichten, nicht als Null ausgeben.
Ein neuer unerklärter Import-/Datenfehler darf diese Ausnahme nicht erben.

## Schritt2-Gates: kleiner realer Smoke-Zyklus

Quelle ist ausschließlich das bereits qualifizierte SLSQP-Stromminimum und seine
Startmatrix aus `current_gn_inputs.qualified_source`. Vorhandene numerische Kerne
und `run_current_gn_arm.run_arm` unverändert wiederverwenden; Budget hier neu
**zweimal24 vollständige Bundleversuche**, jeweils16 Startreplays enthalten.
Keine Verlängerung alter2048-Läufe. Identische bisherigen GN-/Trustoptionen,
0,01-Koordinatenskalierung,207 benannte Parameter,1e-8 Auswahltoleranz.

Nach erfolgreicher Startqualifikation muss der Solver wirklich aufgerufen worden
sein und mindestens einen von x0 verschiedenen Punkt nach dem Startup ausgewertet
haben. Beide tatsächlichen Parameter-/Wertpfade, Auswahl und Arbeit müssen exakt
wiederholen. Mindestens17 und höchstens24 Versuche je Arm; Budgetstopp ausdrücklich
kein Konvergenzerfolg. Vollständige Zähler und Fehler bleiben erhalten.

Separater Auditor verwendet den bestehenden unabhängigen Armprüfer mit explizitem
24er Limit, eigener Quellen-/Parametermapping-/Gram-Gegenrechnung und bindet die
Ausgabefelder. Alle vier nachgelagerten Abnahmen werden quellengebunden geprüft.
Kein Mindestgewinn, keine Zulässigkeit und keine Mehrstart-Leistungsrangfolge
als Etappenkriterium. Feldgrenze1e-8 bleibt im Kandidatenbericht bestehen.

## Abschluss, Erhalt und Nutzung

Ein neuer Gesamtprüfer führt die begrenzten Phasen sequenziell aus, speichert
Befehle/Logs/Rückgabecodes/Quellhashes und besitzt einen eigenständigen
Abschlussaudit. Ein positiver Gesamtstatus verlangt sämtliche Schritt1-/2-Gates;
ausgeschlossene Fähigkeiten und wissenschaftliche Zulässigkeit werden separat
ausgewiesen, niemals aus Prozessstatus abgeleitet.

Mindestens3GiB vor nativer Ausführung,2GiB laufende Reserve, keine parallele
schwere Suche/Installation. Root-Umgebung und externe Checkouts unverändert.
Alle neuen numerischen Runner/Auditoren vor echter Ausführung durch synthetische
Kontrollen prüfen und committen. Ausgabeordner müssen neu sein; bei Fehlschlag
Originaldaten behalten. Altbestandprüfung gegen5971fee erlaubt neue Dateien und
ausdrücklich geänderte Übersichten/Journalregeln, nicht Änderungen alter Evidenz,
numerischer Kerne oder registrierter historischer Protokolle.

Nach erfolgreicher Abnahme: übersichtliche Bedienanleitung, Status/Plan/READMEs
aktualisieren, Ergebnisse lokal committen, **Schritt1/2 nur für diesen Umfang als
abgeschlossen melden und an den Nutzer übergeben**. Keine weitere Forschung
automatisch anhängen. Umfangserweiterung erfordert neue explizite Qualifikation.
