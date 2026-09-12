# SLSQP mit zusammengesetztem Startgate: vollständig geprüft, Flux abgelehnt

## Unabhängige feine Abnahme abgeschlossen, 2026-09-12

Alle vier registrierten Abnahmephasen bei b7a9610 vollständig durchgeführt:
Flux-/Geometrie-Holdout, kontinuierliche Krümmung, kontinuierlicher Spulenabstand
und zusätzliche native Bedingungen. Reguläre Exitcodes2/0/0/0; der negative
Fluxbefund hat keine spätere Prüfung unterdrückt. Alle entsprechenden
physikalischen Zahlen beider Wiederholungen stimmen exakt überein.

| Prüfgröße, Reaktorskalierung | Ergebnis | Unveränderte Grenze |
| --- | --- | --- |
| Roh-Quadratic-Flux,128x128/800 Spulenpunkte | 8,191665362116152e-8 | <=1e-8: abgelehnt |
| Mittlerer Feldbetrag | 0,9461249131T | Diagnostik, kein Freigabekriterium |
| Gesamtlänge der vier Grundspulen | 219,9000016604m | <=220m: bestanden |
| Kontinuierliche Krümmungsobergrenze | 0,8007962530/m | <=1/m: bestanden |
| Kontinuierliche Spulenabstandsuntergrenze | 1,0875120845m | >=1,06m: bestanden |
| Spulen-Plasma-Abstand,512er Gitter | 2,9654936517m | >=1,3m: Gitterschirm bestanden |
| Maximale native MSC / Bogenlängenvariation | 6,8100975643 / 7,0023184256 | <=10,1002860748 /102,0157787936: bestanden |

Feldverfeinerung und native Linking-Prüfung bestehen. Alle sieben
Krümmungsauflösungen200 bis12800 sind erhalten. In `curvature.json` ist
`fields[0]` weiterhin die generische alte Quelle `rejected-warmstart`; nur
`direct-r1` und `direct-r2` sind die hier geprüften neuen Kandidaten.

Der feine Flux liegt rund8,53% unter dem vorigen AL-Kandidaten, aber weiterhin
Faktor8,1917 über der physikalischen Grenze. Krümmung und Spulenabstand verbessern
sich ebenfalls, Länge steigt leicht und Plasmaabstand sinkt: **keine vollständige
Pareto-Dominanz**, keine Aussage gleicher Methodenbudgets. Keine zulässige
Baseline, kein Konvergenz- oder SoTA-Nachweis. Diese getrennte Studie ist
geschlossen; ihr Budget wird nicht nachträglich erweitert.

Evidenz: `evidence/slsqp-composite-v1-validation/summary.json` samt allen vier
quellgebundenen Einzelberichten und Logs. Nächster registrierter Teil von Schritt1:
Nichtlokalitätsprüfung aller sechs eingefrorenen Spulennetze. Der nächste
Konstruktionsversuch für Schritt2 benötigt ein eigenes vorab begründetes Protokoll.

## Abgeschlossene Suchrechnung, 2026-09-12

Beide2048-Bundle-Arme bei ede0ba8 vollständig gespeichert: je6047 Anfragen,
3998 Cachetreffer, eine abgewiesene Budgetüberschreitung, null fehlgeschlagene
Auswertungen. Beide vollständigen Punkt-/Wertverläufe, Auswahl, Zähler und
Arbeitsmengen stimmen exakt überein. Separater Audit besteht zehn Profilprüfungen
und je32 Armprüfungen, ohne zusätzliche Physikaufrufe.

Ausgewählt wird jeweils Bundle1573 mit Roh-Flux8,191534720971661e-8 und
interner Maximalverletzung8,28366242267009e-9. Diese liegt innerhalb der vorab
festgelegten1e-8-Auswahltoleranz, ist nicht identisch mit exakt erfüllten
Konstruktionsungleichungen. Vollständiger Start und neun alte Startpunkte stimmen;
das qualifizierte zusammengesetzte Gate besteht, der alte all-row-FD-Test bleibt
negativ. Beide Solver enden am Budget, nicht mit nachgewiesener Konvergenz.

Pro Arm9.830.400.000 Spulenpaar- und6.710.886.400 Plasmapaar-Stichproben.
Zusammen mit1033 AL-Bundles beträgt die nominelle Konstruktionsobergrenze
3081 pro Hybridpfad; gesonderte Startup-/Ableitungsqualifikationen und deren
unabhängige Gegenrechnungen bleiben zusätzlich bilanziert. Kein fairer isolierter
Methodenvergleich, keine Zulassung durch den positiven Studienaudit.

Evidenz: `evidence/slsqp-composite-v1/summary.json`, beide Armberichte,
`evidence/slsqp-composite-v1-driver/` und
`evidence/slsqp-composite-v1-audit.json`. Die damals noch offene feine Abnahme
ist im obigen Abschnitt separat abgeschlossen.

## Aufbewahrter Zwischenstand vor Abschluss

Ausführung bei ede0ba8. Erster Arm vollständig mit2048 Bundles/6047 Anfragen/
3998 Cachetreffern und einem Budgetcap gespeichert, null fehlgeschlagene
Auswertungen. Anfangswerte und komplette qualifizierte Jacobimatrix reproduzieren
exakt; der alte all-row-FD-Test bleibt negativ, das zusammengesetzte Gate besteht.
Auswahl: Bundle1573, grober Roh-Flux8,191534720971661e-8,
maximale interne Verletzung8,2836624e-9 (innerhalb der unveränderten1e-8-Auswahl-
toleranz). Immer noch über der physikalischen Fluxgrenze1e-8.

Zweite Wiederholung läuft. Noch kein vollständiger Wiederholungsvergleich,
unabhängiger Studienaudit oder feiner Holdout; **kein neuer zulässiger Entwurf**.
Laufende Berichte `evidence/slsqp-composite-v1/` bleiben bis zum Abschluss unstaged.
Die folgende Vorbereitung beschreibt den festgelegten Prüfpfad, keinen Gesamtpass.

## Aufbewahrte Vorbereitung

2026-09-12, [Protokoll](SLSQP_COMPOSITE_PROTOCOL.md) bei0966da6 vorab
registriert. Neuer Arm ist additiv, alte SLSQP-/Native-/Budgetkerne unverändert.
AST-Gegenprüfung bestätigt identische Optimiereraufrufe und Callback-Funktionen;
geändert sind nur explizite qualifizierte Startrichtung, Speicherung/Replays und
zusammengesetztes Gate vor dem ersten Solveraufruf.

Der neue Runner verlangt die vollständige committed Startqualifikation samt
unabhängigem Audit. Jede Wiederholung speichert ihr erstes natives138x207-Bundle
und muss es gegen die qualifizierte Matrix reproduzieren, danach alle neun
ursprünglichen Startpunkte/Werte. Originales all-row-FD-Ergebnis bleibt getrennt;
keine numerischen Werte oder Ableitungen werden durch Referenzen ersetzt.

Sechs neue Kontrollen prüfen insbesondere falsche Nicht-Paar-Ableitungen,
falsche vollständige Startmatrix, Punkt-/Quellhashes, Permutation und nichtendliche
Arrays. Ein isolierter Mock bestätigt genau neun Bundles vor Solverfreigabe;
bei falscher Startmatrix genau ein Bundle und null FD-/Solveraufrufe. Das ist
ein Softwarekontrollfall, keine tatsächliche physikalische Qualifikation.

Separater Auditor prüft alle Replays/Gateflags, vollständige Ledger und
benannte ausgewählte Felder; vorgesehene feine Holdouts weiterhin unverändert.
Noch keine neue Suchrechnung. Nächster Schritt: geschützte sequenzielle Ausführung
beider2048-Bundle-Arme, unabhängiger Audit, alle vier Abnahmephasen.
