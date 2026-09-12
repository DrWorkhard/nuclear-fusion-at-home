# Bestandsaufnahme vorhandener LPQA-Spulen: zuerst Provenienz und Vergleichbarkeit

Vor der Auswertung festgelegt, 2026-09-12. Dies ist ein Metadatenaudit des bereits
lokal vorhandenen, unveränderten StellCoilBench-Pins `c7949edc4ea6378fc3be633304c69c288c3b79b5`,
kein zusätzlicher physikalischer Suchlauf und keine Änderung des laufenden
Jacobiskalierungsversuchs. Keine Downloads oder Archivextraktion.

## Zweck und Auswertung

Die bisherigen Versuche starten alle am selben zurückgewiesenen lokalen Feld.
Für eine starke Baseline müssen wir auch vorhandene Vergleichsentwürfe prüfen.
Inventarisiere sämtliche im Pin verfolgten `results.json` unter genau
`submissions/LandremanPaul2021_QA/`. Jeden Pfad/Hash, Schema, Produzentenrevision,
relevante gemeldete Endmetriken und vorhandene lokale Felddateien festhalten.
Keine Vermischung mit QH- oder anderen Oberflächen; fehlende Werte bleiben unbekannt.
Bei Fortsetzungsläufen nur explizite Endmetriken verwenden, nicht still eine frühe
Stufe als Endzustand ausgeben. Inkonsistente Angaben gesondert markieren.

`final_squared_flux` ist **nicht automatisch ungeschwellter Roh-Flux**: Der
lokale SIMSOPT-Pin gibt unterhalb seiner eingestellten Schwelle null zurück.
Gerade Nullmeldungen erlauben deshalb keine Rangfolge oder Zulässigkeitsbehauptung.
Auch aktuelle Auswertequellen beweisen nicht automatisch die genaue Semantik
historischer Produzentenrevisionen. Physikalische Rekonstruktion bleibt Pflicht.

Für eine ausschließlich explorative Rekonstruktions-Warteliste:

1. Explizite vier Basisströme und Endordnung8; gespeicherte Endfelddatei vorhanden.
2. Gemeldeter Zielwert1T; finale Feldstärke im Intervall[0,9;1,1]T.
3. Explizites a0, gemeldete Länge*a0<=220m, Krümmung/a0<=1/m,
   cc*a0>=1,06m und cp*a0>=1,3m. Kein Ersatz unserer feinen Abnahme.
4. Sortiere passende Datensätze nach nichtnegativem endlichem
   `avg_BdotN_over_B`, dann lexikalischem Pfad; höchstens fünf erste Einträge
   festhalten. Unbekannte Pflichtwerte erfüllen keinen Schirm.

Alle Ausschlussgründe und keine/mehrere passende Kandidaten sind reguläre
Ergebnisse. Die Warteliste ist keine zulässige Baseline und keine Methodenrangfolge.
Abweichende Geometrieparametrisierung, Stromsumme, Randbedingungen oder Budgets
verhindern einen ungeprüften fairen Vergleich; Zahlen dienen nur der Orientierung.

## Gegenprüfung und nächster Schritt

Parser an flachen/neuen Schemata, fehlenden Werten, Null-Flux mit großer Schwelle,
Fortsetzungs-Endzustand und falschen Parameterzahlen testen. Bestandspfadliste
und sämtliche Berichtsbytes mit Git-Pin prüfen; Eingabefehler gesondert erhalten.
Vollständige Inventarzähler und Auswahl unabhängig aus gespeichertem Inventar
nachrechnen. Kein neuer Feldaufruf für diesen Schritt. Erst anschließend ein
eigenes Rekonstruktions-/Holdout-Protokoll festlegen; kein verstecktes Einsetzen
eines fremden Felds in den laufenden Originalstart-Vergleich.
