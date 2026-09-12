# SLSQP mit zusammengesetztem Startgate: Suche unabhängig bestätigt

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
`evidence/slsqp-composite-v1-audit.json`. Feine Abnahme noch offen: als Nächstes
alle vier unveränderten Holdoutphasen für beide Kandidaten, auch bei negativem Flux.

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
