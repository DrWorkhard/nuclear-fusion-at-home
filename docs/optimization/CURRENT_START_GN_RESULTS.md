# GN vom aktuellen Stromminimum: vollständig geprüft, weiterhin unzulässig

2026-09-13; [Protokoll](CURRENT_START_GN_PROTOCOL.md) bei c54b991 registriert.
Suchcode bei db2e825 vor realer Ausführung committet. Beide Arme, separater
Studienaudit und alle vier unabhängigen Abnahmephasen abgeschlossen.

## Ergebnis und Grenzen

| Größe | Neuer fein geprüfter Wert | Grenze |
| --- | --- | --- |
| Roh-Flux,128x128/800 | 8,129882387125932e-8 | <=1e-8: abgelehnt |
| Mittlerer Feldbetrag | 0,9461249072T | Diagnostik |
| Gesamtlänge vier Grundspulen | 219,8994003241m | <=220m: bestanden |
| Kontinuierliche Krümmungsobergrenze | 0,8193222990/m | <=1/m: bestanden |
| Kontinuierliche Spulenabstandsuntergrenze | 1,0892164827m | >=1,06m: bestanden |
| Spulen-Plasma-Abstand,512er Gitter | 2,9557058577m | >=1,3m: Gitterschirm bestanden |
| Maximale native MSC / Bogenlängenvariation | 6,9222046603 /9,0702484454 | <=10,1002860748 /102,0157787936: bestanden |

Der feinste Flux verbessert sich gegenüber dem festgelegten Stromminimum um
0,7542107201%, bleibt aber Faktor8,1299 über der Grenze. Länge und Spulenabstand
verbessern sich, Krümmung und Plasmaabstand verschlechtern sich: keine vollständige
Pareto-Dominanz. Kein fairer isolierter Methodenvergleich, keine Konvergenz,
keine zulässige Baseline und kein SoTA-Nachweis. Der Versuch wird nicht verlängert.

Je2048 vollständige Bundles einschließlich16 Startwiedergaben,7159 Anfragen,
5110 Cachetreffer, eine abgewiesene Budgetüberschreitung, keine fehlgeschlagene
Auswertung. Auswahl jeweils Bundle2043 mit grobem Roh-Flux8,129773168035203e-8
und exakt null positiver Konstruktionsverletzung. Die gesamten Punkt-/Wertpfade,
Arbeit, GN-Identitäten, Iterationen und Startprüfungen stimmen exakt überein.
Beide Solver enden am Budget, nicht mit Konvergenzerfolg.

Separate Prüfung besteht20 Profilchecks und je49 Armchecks. Alle16 Ausgangswerte
und der vollständige Start-Jacobian reproduzieren exakt; nativer Gramfehler
2,4624e-12 liegt unter1e-10. Pro Arm2048 gebündelte Matrizen,2048 zusätzliche
native Kovektor-Felder und je32768 gezählte Einzelspulenintegrale sowie jede
geometrische/Strom-Ableitungskategorie. Direkte Paararbeit wie registriert:
9.830.400.000 Spulenpaar- und6.710.886.400 Plasmapaar-Stichproben. Einschließlich
1033 AL- und2048 SLSQP-Bundles nominal5129 Konstruktionsbundles pro Hybridpfad;
separate Strom-/Ableitungs-/Krümmungsqualifikation und Audits kommen hinzu.

Alle vier Holdoutphasen regulär abgeschlossen, Exitcodes2/0/0/0. Alle acht
Fluxgitter, sieben Krümmungsstufen pro Feld, sämtliche Abstands- und nativen
Stufen bleiben erhalten. In der generischen Krümmungsdatei ist das erste Feld
die alte `rejected-warmstart`-Kontrolle; nur die folgenden zwei sind neue Kandidaten.
Linking-Werte null. Beide Wiederholungen ergeben exakt dieselben physikalischen
Holdoutdaten. Separater schreibgeschützter Abschlusscheck bestätigt Quell-/
Code-/Feldhashes, vollständige Auflösungen, groben Replay und Grenzklassifikation
aus den gespeicherten Zahlen, ohne neue native Aufrufe. Das ist keine zweite
unabhängige Biot-Savart-Auswertung aller Holdoutfelder.

Evidenz: `evidence/current-start-gn-v1/`, `evidence/current-start-gn-v1-audit.json`,
beide `*-driver/`, `evidence/current-start-gn-v1-validation/` sowie
`artifacts/current-start-gn-v1/` (1,5MiB Rohdaten; Suchberichte42MiB).
Feld-SHA256:770986775bfb573873e4268160ff05cc98d0ea1a0b69cd7d3f11e9112ad4ff6d.

Nächste Optimierungsentscheidung benötigt ein eigenes Protokoll: Die bisherige
lokale Folge verringert den Fehler langsam, belegt aber weder ein lokales noch
globales Optimum. Keine weitere reine Budgeterhöhung ohne neue Begründung.
Zunächst den bereits registrierten analytischen Drift-Kontrollweg von Schritt1 schließen.

## Aufbewahrter Aufbau vor Ausführung

Quellprüfung bindet das bereits ausgewählte SLSQP-Stromminimum, seine16 alten
Prüfzustände, vollständigen direkten Start-Jacobian und unabhängig qualifizierte
native1024x207-Feldmatrix. Physikalische Namen werden explizit abgebildet;
alle16 Kopien der neu serialisierten Ausgangsform müssen identisch sein.

Zwei2048-Bundle-Arme, jeweils16 vollständig bezahlte Startwiedergaben, natives
H_GN-Startgate, unveränderte direkte Bedingungen und GN-/Trust-Optionen. Jeder
tatsächliche Versuch speichert den vollständigen207-Parameterpunkt, auch beim
Fehler. Native direkte Arbeit, gebündelte geometrische/Stromableitungen und
zusätzliche Kovektor-B-Anfragen werden einzeln gezählt. Bei Fehler letztes
fertiges direktes Bundle und vorhandene Feld-/Matrixdaten erhalten.

## Kontrollen vor echter Physik

Vier Tests bestehen: analytisches beschränktes Quadratproblem plus kompletter
Zweiarmablauf mit korrekt klassifiziertem Zielstopp; exakt bezahlte Budgetgrenze
mit unabhängiger Auswahl-/Arbeitsprüfung; absichtlicher Startgatefehler; Abbruch
in der dritten gebündelten Matrixrechnung. Mutationen an Parametern, Zählern,
Startprüfung, Identitäten und Solveroptionen werden vom separaten Auditor abgelehnt.
Diese Spielzeugdaten ersetzen keine native Startqualifikation oder reale Abnahme.

Reine Quelldatenvorprüfung bestätigt die echte feste Quelle und Matrixdimensionen,
ohne neue Magnetfelder auszuwerten. Gesamte Regression667 Tests bestanden,
144 bekannte unveränderte Fixture-Warnungen. Ruff/Dokumentstruktur/Diff bestehen.
Beide READMEs, Status und Plan damals geprüft; reale Ausführung und Abnahmen
sind inzwischen im oberen Abschnitt abgeschlossen.
