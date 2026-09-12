# Feste Geometrie, optimale Ströme: lineare Kontrollkerne vorbereitet

2026-09-12. [Protokoll](FIXED_GEOMETRY_CURRENT_PROTOCOL.md) bei ebc7e79 vorab
registriert. Noch keine der beiden tatsächlichen Spulenformen neu ausgewertet,
kein gemessener zusätzlicher Fluxgewinn.

Additiver Drei-Spalten-SVD-Rechner mit den festen Rang-/Konditions-/Normalrest-
Schirmen; getrennte QR-Zerlegung mit expliziter dreistufiger Rücksubstitution
und skalaren Summen. Keine Verwendung desselben LS-Lösers für beide Antworten.
Rangverlust oder Konditionszahl>1e10 geben ausdrücklich keinen qualifizierten
Minimierer zurück. Konstante Stromsumme und explizite interne Skalierung werden
separat geprüft; keine neue Vorzeichenbeschränkung gegenüber dem Originalproblem.

Acht analytische Kontrollen bestehen: bekannte dreidimensionale Lösung mit
nichtverschwindendem Rest, nichtorthogonale überbestimmte Aufgabe, exakt
darstellbarer Nullrest, Rangverlust/zu große Kondition, NaNs/Formfehler und
konstante physikalische Stromsumme. Ruff beanstandete anfangs eine lange Zeile;
Zeilenumbruch vor Ausführung korrigiert, keine numerische Änderung.

Die strenge Normalrestnorm des Protokolls ist unverändert; aus einem
Numerikfehlschlag nahe Maschinenpräzision darf kein toleranzgeheilter Pass
werden. Nächster Schritt: echte quellgebundene Probes/Dateiaudit und alle
unveränderten Feld-Holdouts nach abgeschlossenem feinsten Netz-Audit.

## Explizite symbolische Stromzuordnung

Zusätzlicher Leser löst den gesamten serialisierten Stromausdruck als16x3-
Matrix plus konstanten Vektor auf. Er verlangt exakt drei getrennte freie
Stromblätter mit Skalierung1e7, feste vierte Summe und alle16 Symmetriezeichen;
die globalen Spalten kommen ausschließlich aus expliziten Namen. Zwei synthetische
Tests bestätigen die unabhängige physikalische Rekonstruktion, eine umgekehrte
Namensreihenfolge und die Ablehnung veränderter Skalierung/Symmetriekopien.

Ein erster Kontrollaufbau kombinierte versehentlich die alte Ordnung4-Fixture
mit Namen eines anderen Ordnung8-Laufs und wurde erwartungsgemäß abgelehnt.
Die Kontrolle benutzt jetzt einen in sich konsistenten synthetischen207-DOF-
Graphen; keine Produktionsdaten/-Namen wurden passend gemacht. Insgesamt zehn
reine LS-/Stromgraphkontrollen bestanden, native Probes weiterhin noch nicht ausgeführt.

## Vollständiger Ablauf und unabhängige Kontrollen vorbereitet

Die beiden eingefrorenen Quellstudien müssen sämtliche vier ursprünglichen
Holdoutphasen abgeschlossen haben. Der neue Treiber bilanziert je erfolgreichem
Zustand zwei vollständige native138-Bundles und acht zusätzliche B-Gitteranfragen,
einschließlich Cacheabfragen. Alle angefragten Strompunkte/Felder werden gespeichert;
bei Fehlern bleiben auch der unvollständige Punkt und die tatsächliche Arbeit erhalten.

Der separate Auditor rekonstruiert Gewichte, Stromspalten und QR-Lösung aus
den gespeicherten kartesischen Feldern, ohne neue native Rechnung. Er prüft
sämtliche16 transformierten Spulenkoeffizientensätze, Regularisierungen, Ströme,
Quellzuordnung, Rechnungsbilanz und Zahlenklassifikation. Ein separater
Feld-Holdouttreiber behält alle acht festgelegten Gitter, auch bei Fluxablehnung;
dessen weiterer Array-Audit rechnet die Flux-/Feldstärkenwerte und Klassifikationen
nach, ist aber keine zweite unabhängige Biot-Savart-Implementierung.

Die synthetische Gesamtprobe entdeckte vor echter Ausführung einen NumPy-bool-
Serialisierungsfehler im Berichtsschreiber. Explizite skalare Umwandlung korrigiert
ihn; kein physikalisches Ergebnis überschrieben. Auch ursprüngliche Ruff-Zeilenlängen
und eine ungebundene Schleifenclosure wurden vor Ausführung korrigiert.
Kontrollen schließen manipulierte Geometriepunkte, Probes, NaNs, zu niedrige
Arbeitszähler, falsche Fluxfreigabe und ausgelassene Holdoutgitter ein.
Noch kein neues physikalisches Ergebnis; nächste Phase ist die vorab registrierte
quellgebundene Ausführung nach Commit der Implementierung und Prüfungen.
Alle sieben neuen Probe-/Treiber-/Holdout-/Fehlerkontrollen und die gesamte
Regression mit634 Tests bestehen;144 bekannte Fixture-DeprecationWarnings.
Ruff, Dokumentstruktur und Diffprüfung bestehen. Native Imports werden erst
bei der wirklichen Ausführung geladen; synthetische Kontrollen benötigen keine
SIMSOPT-Installation. Die separate strenge Importwarnungsprüfung bleibt offen.
