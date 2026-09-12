# Feste Geometrie, optimale Ströme: vollständig geprüft, kein nennenswerter Gewinn

2026-09-12. [Protokoll](FIXED_GEOMETRY_CURRENT_PROTOCOL.md) bei ebc7e79 vorab
registriert; Implementierung bei1b78832. Beide tatsächlichen Spulenformen sind
jetzt neu ausgewertet und unabhängig auditiert. Der zusätzliche Stromgewinn ist
äußerst klein; alle festgelegten feinen Feld-Holdouts sind abgeschlossen und
separat nachgerechnet. Beide Formen bleiben magnetisch unzulässig. Die nachstehenden
Vorbereitungsabschnitte dokumentieren den Zustand vor dieser Ausführung.

## Native Ausführung und Datei-Audit

| Feste Form | Grober Flux vorher | Stromminimum | Relative Senkung |
| --- | --- | --- | --- |
| AL | 8,95478252250164e-8 | 8,954781375131198e-8 | 0,0000128129% |
| SLSQP | 8,191534720971661e-8 | 8,191534235747067e-8 | 0,00000592349% |

Jeweils Rang3, Kondition5,586 beziehungsweise5,360. Alle sechs affinen Feldprobes
liegen innerhalb4,441e-16; die native Roh-Fluxvorhersage stimmt relativ bis
7,966e-14. Beide vollständigen ursprünglichen138-Wert-Bundles reproduzieren exakt.
Alle137 geometrischen Werte und die serialisierten geometrischen Koeffizienten
bleiben unverändert. Je57 unabhängige Datei-/Array-Prüfungen bestehen, einschließlich
aller16 physikalischen Kopien und Stromvorzeichen. Der separate QR-Rechner
bestätigt das Minimum; unabhängig rekonstruierter Normalrest höchstens1,046e-14.

Grundströme vorher/nachher, inA:

- AL: [332570,82572;377088,42559;287349,09363;253067,27969] →
  [332571,13639;377087,65817;287349,96423;253066,86585].
- SLSQP: [287532,97340;306020,66037;338118,16657;318403,82430] →
  [287533,03112;306020,24591;338118,40426;318403,94334].

Unveränderte Summe1250075,624635464A. B-Mittel vorher/nachher liegt bei beiden
nahe0,946125T; Änderungen von−4,20nT (AL) beziehungsweise+22,47nT (SLSQP). Exakte Werte und
alle16 Vorzeichenkopien im Bericht. Das ist vorerst eine Aussage auf dem festen
Konstruktionsgitter, keine globale Formoptimalität oder physikalische Zulassung.

Arbeit insgesamt: vier vollständige native Bundles mit vier B-VJPs sowie16
zusätzliche B-Gitteranfragen, also20 B-Anfragen einschließlich Cacheabfragen.
Zwei SVD- und zwei QR-Lösungen; unabhängiger Dateiaudit zusätzlich zwei
Singulärwertprüfungen und zwei QR-Lösungen, null neue native Felder. Rund2,1MiB
Rohdaten. Quellen und aktiver Code unverändert committed; der Berichtsstatus
`dirty=true` entsteht durch die neu erzeugten, noch uncommitteten Laufberichte.

Evidenz: `evidence/fixed-currents-v1.json`, `...-audit.json`, beide zugehörigen
Driver-Verzeichnisse und `artifacts/fixed-currents-v1/`.

## Alle Feld-Holdouts abgeschlossen

Ausführung bei064175e, alle acht Gitter gespeichert; regulärer Exit2 wegen
Fluxablehnung, kein unterbrochener Lauf. Je14 weitere unabhängige Array-/Quellen-/
Klassifikationschecks sowie vier Gesamtchecks bestehen, null neue native Felder
oder Fits im Auditor. Der eigentliche Holdout verwendet acht B-Gitteranfragen
mit insgesamt75.776 Punkten; keine Rückkopplung in den Stromfit.

| Form | Flux32/200 | Flux64/200 | Flux128/200 | Flux128/800 |
| --- | --- | --- | --- | --- |
| AL | 8,95478137513e-8 | 8,95511938556e-8 | 8,95511949056e-8 | 8,95511949056e-8 |
| SLSQP | 8,19153423575e-8 | 8,19166456331e-8 | 8,19166480121e-8 | 8,19166480121e-8 |

Beide Oberflächen-/Spulenverfeinerungsschirme und der32/200-Quellreplay bestehen,
die unveränderte1e-8-Grenze scheitert. Feinster nativer SLSQP-Wert exakt
8,191664801213237e-8 (Faktor8,1917); AL8,955119490561782e-8 (Faktor8,9551).
Die unabhängige Fluxarithmetik weicht erst in den letzten Gleitkommastellen ab.
Gegenüber den jeweiligen abgeschlossenen Quellen sinkt der feinste Fehler nur
um0,0000166076% (AL) beziehungsweise0,00000684724% (SLSQP).
Solche winzigen Unterschiede sind kein praktisch relevanter Entwurfsfortschritt.

Das gut konditionierte dreidimensionale Stromproblem ist damit an beiden festen
Formen numerisch ausgeschöpft. Bloße Stromumverteilung erklärt beziehungsweise
schließt den fehlenden Faktor8–9 nicht. Daraus folgt **keine** globale Untergrenze
für andere Spulenformen oder andere zulässige Suchräume. Die nächsten konstruktiven
Schritte müssen an der Formsuche ansetzen; ihre Wahl braucht ein eigenes Protokoll.
Alle ursprünglichen geometrischen Abnahmen werden ausschließlich über exakte
Identität aller16 serialisierten Spulenkopien übernommen. Elektromagnetische
Kräfte würden sich mit Strömen ändern; keine Mechanik-/Ingenieurfreigabe geerbt.

Evidenz zusätzlich: `evidence/fixed-currents-v1-holdouts.json`,
`...-holdouts-audit.json`, beide Driver-Verzeichnisse und
`artifacts/fixed-currents-v1-holdouts/`. Damit ist dieser begrenzte Versuch
geschlossen, nicht Langfristiger Plan Schritt2.

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
