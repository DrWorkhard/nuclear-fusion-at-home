# SLSQP mit zusammengesetztem Startgate: vorbereitete Ausführung

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
