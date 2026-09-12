# Clebsch-Spektraldiagnose: einfache Feldmoden-Trunkierung reicht nicht

2026-09-12: [Protokoll](QI_CLEBSCH_SPECTRAL_PROTOCOL.md) vor neuer Rechnung
registriert. Endliche, getrennte Wout-Fourierausgaben und Lambda-Halbgitter-
Glättung sind im aktuellen gepinnten Quellcode sichtbar. Eine spektrale Ursache
der beobachteten Restfehler ist damit allein noch nicht nachgewiesen.

Projektionswerkzeuge, fester64/128-Auswerter und unabhängiger trigonometrischer
Auditor sind vorbereitet. Sieben Moden-/Konjugations-/Parseval-Kontrollen und
eine direkte DFT-Gegenprüfung bestehen. Der reine Auditor benötigt nur NumPy;
ein unnötiger netCDF-Import wurde entfernt. Alle acht Tests bestehen auch unter
strenger RuntimeWarning-Prüfung. Die separat [dokumentierte native Importwarnung](../validation/NETCDF_IMPORT_WARNING.md)
bleibt bestehen; die ursprüngliche Umgebung wurde nicht geändert.
Die reale Spektralrechnung ist inzwischen vollständig und unabhängig auditiert.

## Vollständige Rechnung und Gegenprüfung

Ausführung bei7832e95. Alle24 Gruppen mit je zwei Halbflächen, insgesamt48
Endpunktgitter, bei64/128 Punkten abgeschlossen. Berichte
`evidence/qi-clebsch-spectrum-v1.json`, `evidence/qi-clebsch-spectrum-v1-audit.json`,
Wächterbericht im `-driver`-Verzeichnis; Rohdaten in
`artifacts/qi-clebsch-spectrum-v1/`. Min freier Platz6042742784Bytes.
Workerexit2 bezeichnet das negative Hypothesenergebnis, nicht einen Abbruch.

Alle bisherigen16/32-Teilgittersamples reproduzieren hier sogar exakt. Der
Parsevalfehler ist maximal3,955e-16. Die64/128-Projektionen stimmen am gemeinsamen
Gitter bis maximal4,732e-11 überein: Winkelauflösung ist für diesen Projektions-
vergleich ausreichend unter der festgelegten1e-5-Verfeinerungsgrenze.

| Fall | Max. poloidaler Projektionsfehler | Max. toroidaler Projektionsfehler |
| --- | --- | --- |
| nfp2 Vakuum | 4,4120737e-4 | 1,9837296e-4 |
| nfp2 beta2 | 3,8055040e-4 | 1,7759602e-4 |
| nfp3 Vakuum | 4,4626677e-4 | 3,1639182e-4 |
| nfp3 beta2 | 1,6039635e-3 | 4,0412732e-4 |

Keine der48 Halbflächen-/Gitterprüfungen besteht die1e-5-Projektionsgrenze,
weder poloidal noch toroidal. Unterschiedliche Nenner gegenüber dem früheren
Clebsch-Test beachten: hier relative Feldkomponente, dort Flussidentität.
Der separate Auditor bestätigt die Projektionen und Bandenergien mit96 direkten
DFT-Summen und48 expliziten trigonometrischen Rücksummen, ohne neue Feldrechnung.
Er bestätigt insbesondere das negative Projektionsresultat und die Verfeinerung.

**Das bloße Abschneiden höherer Moden der aus gespeichertem g/Lambda abgeleiteten
Feldkomponente erklärt die Wout-Komponenten nicht auf1e-5.** Daraus folgt nicht,
dass sämtliche spektralen Effekte ausgeschlossen wären: g selbst ist endlich
repräsentiert, Lambda wurde bei Ausgabe auf Halbflächen geglättet, und der alte
Produzent ist nicht vollständig rekonstruiert. Auch innerhalb der gespeicherten
Moden bleiben Restanteile. Keine Datenreparatur oder neue kanonische Referenz.

Nächster sinnvoller Schritt: exakte Autoren-Eingaben/Produzentenzuordnung und
Ausgabekonventionen prüfen; anschließend eine getrennte frische QI-Gleichgewichts-
und Auflösungsstudie vorab festlegen. Direkte physikalische Drift darf die
begrenzte innere Konsistenz der momentanen Wout-Darstellungen nicht übergehen.
Globaler QI-Maßstab und absolute Frequenzen bleiben offen.
