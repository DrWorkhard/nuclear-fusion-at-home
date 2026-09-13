# Geometrische Krümmung: quellgebundener Ablauf vorbereitet

2026-09-13, [Protokoll](GEOMETRIC_CURVATURE_PROTOCOL.md) bei64972fa registriert.
Noch keine neue Feld-/Matrixrechnung an den tatsächlichen Spulen durchgeführt.

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
