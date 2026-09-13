# Geometrische Krümmung: alle sechs Vorhersagen unabhängig bestätigt

2026-09-13, [Protokoll](GEOMETRIC_CURVATURE_PROTOCOL.md) bei64972fa registriert.
Reale Ausführung bei405c675 vollständig abgeschlossen; separater Audit besteht.
Die folgenden Vorbereitungsschritte bleiben als Chronologie erhalten; der
aktuelle wissenschaftliche Befund steht im abschließenden Ergebnisabschnitt.

Additive Spektraldiagnose mit expliziten drei Stromspalten, vollständigem und
geometrischem Feld-Jacobian sowie rein linearisiertem Stromraumprojektor.
Alle Singulärwerte und numerischen Ränge bleiben erhalten; keine Richtungen
werden entfernt. Rangverlust/zu große Kondition des Stromblocks verhindern
die Stromprojektion, löschen aber nicht die bereits berechneten anderen Spektren.

Fünf analytische/negative Kontrollen bestehen: bekannte Projektionsanteile1/2
und4/5, genau verschwindender Tangentenvektor ohne erfundene Quote, explizite
Spaltenpermutation, Rangverlust, NaNs/ungültige Formen und überlaufende skalare
Projektionsstatistiken. Der Überlaufkontrollfall veranlasste eine zusätzliche
Finite-Prüfung auch der skalaren Ergebnisse vor echter Datenverwendung.
Ruff, Dokumentstruktur und Diffprüfung bestehen. Noch kein Konditionierungs-
oder Entwurfsbefund an den realen Daten.

Nächster Schritt: quellgebundene32-Ereignis-Feldwiedergabe, zwei vollständige
gebündelte/native Matrizengegenprüfungen und unabhängiger Vorhersage-/Spektralaudit.

2026-09-13: Drei zusätzliche reine Kontrollen prüfen die transparente Zählung
der nativen Feld-/VJP-/Spulenableitungsanfragen. Ein absichtlicher Fehler am
zweiten Einzelpunkt erhält die erste fertige Matrixzeile, zählt begonnene und
fertige Arbeit getrennt und stellt die ursprünglichen Beobachtungspunkte wieder
her. Die numerischen Matrixkerne bleiben unverändert. Alle drei Tests, Ruff,
Dokument- und Diffprüfung bestehen; weiterhin keine neue reale Feldrechnung.

## Gesamtablauf vor physikalischer Ausführung

Der neue Treiber bindet die geschlossenen Modell-/Probestudien samt vorherigen
Strom-/Holdout-Abnahmen. Eine reine Quelldatenvorprüfung bestätigt genau zwei
16x207-Punktmatrizen und zwei3x207-Schrittmatrizen. Alte Laufzeitnamen werden
über die physikalischen Besitzer explizit zurück- und neu zugeordnet.

Das Modell verwendet unverändert den archivierten LP-Schritt `d`; jeder bereits
gespeicherte tatsächliche Testpunkt muss exakt dem Gleitkommaausdruck `x+d`
entsprechen. Die durch Subtraktion gewonnenen gerundeten Verschiebungen werden
zusätzlich gespeichert, nicht heimlich anstelle der registrierten Schritte benutzt.

Vier neue Gesamtablaufkontrollen bestehen: beide1024x207-Matrizen/alle32 Felder
im analytischen Spielzeugmodell; korrekt negative Modellnützlichkeit bei weiter
gültiger Implementierung; Abbruch an der dritten Einzelpunkt-VJP mit erhaltenem
Feld, gebündelter Matrix und zwei fertigen Zeilen; umgekehrte Namensreihenfolge
und manipulierte Eingaben. Zusätzliche Mutationen an Punkten, Schritten,
Richtungen, Gradient, Stromspalten und Strommatrix werden unabhängig abgelehnt.
Die Tests führen keine reale Spulenphysik aus.

Der erste synthetische Ablauf fand einen NumPy-bool-/JSON-Serialisierungsfehler;
die skalaren Fluxfehler werden nun vor der Klassifikation explizit in Python-float
umgewandelt. Ein nicht passender Patch wurde ohne Dateiänderung abgelehnt und
gegen die inspizierten formatierten Zeilen erneut angewendet. Keine physikalischen
Daten oder Ergebnisse wurden dafür geändert.

Der separate Auditor benutzt die native Einzelpunkt-Matrix, eigene skalare
Summen für Vorhersagen/FD/Projektionen und separat berechnete Spektren. Er prüft
auch Rohfelder, vollständige Ereignisse, QR-Faktorisierung, Zähler und gespeicherte
wiederhergestellte Beobachtungspunkte. Ein negativer Nützlichkeitsbefund kann als
korrektes negatives Ergebnis auditiert werden; keine Entwurfszulassung entsteht.

Vollständige Regression vor physikalischem Einsatz:663 Tests bestanden,
144 unveränderte Fixture-Warnungen. Ruff/Dokumentstruktur/Diff bestehen.
Die separate strenge Importwarnungsprüfung ist damit nicht geschlossen.

## Abgeschlossenes reales Ergebnis, 2026-09-13 — F-078

Alle32 archivierten Zustände wiedergegeben, beide vollständigen1024x207-Matrizen
gegen native Einzelpunkt-VJPs geprüft. Maximaler normierter Matrixfehler
9,437e-16, native-Kovektor-Gradientfehler1,576e-13, Strommatrixfehler1,932e-14.
Alle zwölf Residuen-FD-Prüfungen an beiden festgelegten Schrittweiten bestehen;
maximal5,351e-9 gegenüber1e-6 Grenze. Beobachtungspunkte exakt wiederhergestellt.

Das quadratische Modell sagt **alle sechs Verschlechterungen richtig voraus**.
Die Fehlerreduktion gegenüber linear beträgt mindestens99,59975%. Werte unten
sind Änderungen des **rohen Flux**, nicht der durch1e-6 skalierten Solvergröße.

| Quelle / Radius | Tatsächliche Änderung | Quadratisch vorhergesagt | Quadratischer / linearer Vorhersagefehler |
| --- | --- | --- | --- |
| AL /1e-6 | +1,7334511e-11 | +1,7334114e-11 | 1,23318e-5 |
| AL /1e-5 | +1,5033562e-8 | +1,5033552e-8 | 6,74478e-7 |
| AL /1e-4 | +1,5423763e-6 | +1,5421860e-6 | 1,23354e-4 |
| SLSQP /1e-6 | +1,2225312e-10 | +1,2224814e-10 | 4,01692e-5 |
| SLSQP /1e-5 | +1,2400190e-8 | +1,2395226e-8 | 3,99719e-4 |
| SLSQP /1e-4 | +1,2462282e-6 | +1,2412395e-6 | 4,00248e-3 |

Alle Norm-/Matrix- und Restidentitäten bestehen. Die erste Ableitung war nicht
das entscheidende Problem dieser sechs endlichen Schritte; die positive
Feldmodellkrümmung erklärt deren gegensätzliche tatsächliche Änderung sehr gut.
Das ist eine lokale Modellqualifikation, keine Konvergenz-/Optimalitätsaussage.

### Spektren und gekoppelte Ströme

Beide Rechner finden bei rcond1e-12 Rang203/207 im vollständigen Feld-Jacobian,
200/204 im Geometrieblock und200/204 nach Stromprojektion. Der Stromblock hat
Rang3 und Kondition5,586 beziehungsweise5,360. Die vollständigen extremalen
Singulärwertquotienten liegen dagegen um4–5e16 und reagieren sichtbar auf
Rundung: Für SLSQP etwa4,098e16 im gebündelten,5,358e16 im nativen Rechner.
Alle Singulärwerte erhalten, normalisierte Spektrenabweichung höchstens3,585e-16.
Keine belastbare Genauigkeit dieser extremen Konditionszahlen behauptet und
keine schwachen Richtungen entfernt; ihre geometrische Ursache bleibt zu prüfen.

Der Anteil des linearen geometrischen Tangentenfeldes im Stromraum beträgt
bei AL15,51%/34,48%/33,23%, bei SLSQP3,289%/3,279%/3,278%. Damit ist Kopplung
vorhanden, obwohl statisches Stromtuning zuvor fast nichts brachte. Die Anteile
sind keine tatsächlich erzielten Fluxgewinne und kein Beweis für den Nutzen
eines bestimmten Eliminations- oder Konditionierungsverfahrens.

### Evidenz, vollständige Arbeit und nächste Entscheidung

- Studie: `evidence/geometric-curvature-v1.json`; unabhängiger Audit:
  `evidence/geometric-curvature-v1-audit.json`; beide Guarded-Driver-Verzeichnisse.
- Rohdaten: `artifacts/geometric-curvature-v1/`,8,0MiB;32 kartesische Felder,
  Residuen, Eingaben und je zwei vollständig unabhängig berechnete Matrizen.
  Spektren/Projektionsdaten vollständig im Studien-/Audit-JSON erhalten.
- Arbeit:32 volle B-Gitter,2048 lokale B- und2048 lokale VJP-Anfragen,
  zwei gebündelte Assemblierungen/32 Spulenkontraktionen/64 geometrische
  Ableitungsanfragen/32 Strom-VJPs. Jeweils alles abgeschlossen, keine Fehler.
  Sechs Aufrufe des unveränderten quadratischen Kerns einschließlich Gramformen;
  Konditionierungsphase acht SVDs/zwei QR/sechs Projektionen. Null neue komplette
 138-Zeilen-Bundles, LPs oder Holdouts.
- Separater Audit:99 Fallchecks plus40 Spektral-/Projektions-Unterchecks je
  Quelle, drei Gesamtchecks, alles bestanden. Eigene acht SVDs/zwei QR/sechs
  Projektionen, keine neuen nativen Anfragen/LPs. Das sind hierarchische
  Rechen-/Provenienzprüfungen, nicht281 statistisch unabhängige Experimente.
- Vier Ablaufkontrollen nach der echten Rechnung erneut bestanden; Ruff,
  Dokument- und Diffprüfung bestehen. Vollsuite zuvor663/144 bekannte Warnungen.

Nächster begründeter Schritt ist ein **separat registrierter** klassischer
GN-/Trust-Region-Suchlauf vom bereits festgelegten besten SLSQP-Stromminimum,
unter unveränderter Physik und eigener Startqualifikation/Wiederholung/Abnahme.
Die historische GN-Suche vom anderen Ausgangszustand bleibt unverändert.
Noch keine neue zulässige Konstruktion: Plan-Schritte1/2 bleiben offen.
