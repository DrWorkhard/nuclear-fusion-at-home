# Vorhandene LPQA-Referenzen: 5301 Berichte, noch keine zusätzliche Freigabe

Stand 2026-09-12, Auswertung bei `7fbd4c7` nach
[Vorabfestlegung](UPSTREAM_LPQA_INVENTORY_PROTOCOL.md). Kein Feld geladen oder
neu berechnet, kein Archiv entpackt und keine externen Dateien verändert.

Alle5301 im StellCoilBench-Pin verfolgten LPQA-`results.json` sind erfasst und
bytegenau gegen ihre Git-Objekte geprüft:31 flache und5270 neuere verschachtelte
Berichte, kein Parserfehler.27 erfüllen den vorab festgelegten **gemeldeten**
Vier-Spulen-/Ordnung8-/Geometrie-/Feldstärkenschirm. Die fünf kleinsten gemeldeten
mittleren Normalfeldfehler werden als unqualifizierte Rekonstruktions-Warteliste
festgehalten, nicht als fünf unabhängige Starts oder als zulässige Entwürfe.

| Kennung, jeweils `auto/…` | Gemeldeter mittlerer relativer Normalfeldfehler |
| --- | --- |
| 2026-02-17_083339_92598 | 4,242713230861179e-4 |
| 2026-02-17_083339_39220 | 4,2593663798057876e-4 |
| 2026-02-16_075401_68534 | 4,2664833942566744e-4 |
| 2026-02-15_210059_46837 | 4,268129572649108e-4 |
| 2026-02-16_054521_52359 | 4,2703179318683606e-4 |

Alle fünf melden `final_squared_flux=0` bei Abschaltschwelle1e-6, also100-mal
unserem festen Roh-Fluxlimit.2954 der5301 Gesamtberichte melden null. Diese
Nullwerte sind kein Beleg einer erfüllten1e-8-Abnahme. Der aktuelle lokale
SIMSOPT-Pin unterdrückt Werte unterhalb seiner Schwelle; die fünf historischen
Produzenten nennen jedoch eine andere SIMSOPT-Revision (`50ec27637`) und
unterschiedliche StellCoilBench-Revisionen. Deren genaue alte Semantik und
Metriken werden nicht durch die aktuelle Quellinspektion rückwirkend zertifiziert.

Auch die Vergleichbarkeit bleibt offen: Die fünf melden |B| etwa1,0963T und
Basisstromsumme1249999,2463040038A; unsere lokale Summe ist1250075,624635464A.
Diese Feldmeldungen sind nicht mit unserem Oberflächenmittel gleichzusetzen:
die [spätere Rekonstruktion](UPSTREAM_LPQA_RECONSTRUCTION_RESULTS.md) misst dort
stattdessen etwa0,94606T. Unterschiedliche Messdefinitionen bleiben getrennt.
Unterschiedliche Starts, Produzenten und Rechenbudgets verhindern eine direkte
Methodenrangfolge. Stromwerte werden nicht still angepasst und geschwellte
Zielfunktionswerte nicht als Rohwerte übernommen.

## Gegenprüfung

`evidence/upstream-lpqa-inventory-v1.json` enthält alle Quellhashes, extrahierten
Werte, Ausschlussgründe und fünf geprüfte Endfeldhashes. Ein separater Auditor
berechnet Pfadvollständigkeit, Quellenbytes, gemeldete Werte, alle numerischen
Schirme, Zähler und lexikalisch stabile Auswahl erneut, ohne den Parser zu
importieren. Alle neun Prüfungen bestehen:
`evidence/upstream-lpqa-inventory-v1-audit.json`. Er prüft nicht die physikalische
Wahrheit dieser gemeldeten Metriken.17 Parserkontrollen bestehen; eine vor der
Audit-Ausführung gefundene Schleifenbindungswarnung wurde behoben, anschließend
Ruff bestanden. Keine fehlgeschlagene physikalische Ausführung.

Nächster Schritt: unveränderte gespeicherte Felder mit autoritativem LPQA-Ziel
rekonstruieren, Symmetrien/Ströme/Parameterisierung prüfen, Roh-Flux und Geometrie
mit unseren festgelegten Gittern auswerten. Dies erhält ein eigenes Protokoll
und beginnt erst nach Abschluss der laufenden kontrollierten Suche. Das Inventar
allein schließt weder die zulässige Baseline noch langfristigen Schritt2.
Die inzwischen abgeschlossene Rekonstruktion bestätigt alle fünf Quellen/
Felder, lehnt jedoch jeden Roh-Flux nahe1e-6 gegenüber1e-8 ab.

## Getrennt vorbereitete Rekonstruktion

Das [neue Protokoll](UPSTREAM_LPQA_RECONSTRUCTION_PROTOCOL.md) ist inzwischen
vorab committed. Der statische Runner verlangt den abgeschlossenen committeten
Jacobi-Versuch einschließlich seiner Holdouts, unveränderte Inventar-/Feldhashes,
Spulenzahl/Ordnung/Symmetrien und berichtete Ströme. Originale bleiben unverändert;
ein neuer200-Punkte-Quadraturklon erhält Geometrie, Ströme und Regularisierungen.
Fehlerpunkte werden mit ihren tatsächlichen Feldarrays gespeichert.

Die unabhängige direkte Filamentfeldsumme besteht acht reine Kontrollen:
analytisches Kreisfeld samt Vorzeichen, Stromlinearität, Überlagerung, Translation
sowie Zurückweisung singulärer oder ungültiger Eingaben. Das ist noch keine
Ausführung der fünf Referenzfälle. Der Ressourcenwächter protokolliert den
expliziten statischen Befehl und seine Ausgabe; kein Hintergrundstart vor
abgeschlossener vorheriger Suche/Abnahme.

Zusätzlicher reiner Quellenprüfer liest die vier Fourier-Koeffizientensätze,
Regularisierungen und alle16 physikalischen Ströme direkt aus dem serialisierten
Objektgraphen, ohne nativen Deserialisierer. Zehn Kontrollen decken skalierte/
summierte Ströme, veraltete Konstruktorargumente, Zyklen, Nichtendlichkeit und
falsche Basisgeometrie ab. Der Runner prüft seine geladenen Daten dagegen.
Ein separater Endauditor ist vorbereitet: unveränderte Quellparameter, erneute
komponentenweise Biot-Savart-Summen aus den gespeicherten Arrays sowie
Abnahmearithmetik/Gittervollständigkeit. Zwei zusätzliche Kreisfeld-/Fehlerkontrollen
bestehen; keine erneute feine Geometrieprüfung durch diesen reinen Audit behauptet.
