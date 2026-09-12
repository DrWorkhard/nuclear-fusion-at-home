# Geometrischer Abstieg: alle sechs echten Schritte negativ, unabhängig bestätigt

2026-09-12, [Protokoll](GEOMETRIC_DESCENT_PROTOCOL.md) bei a56c9e1 registriert.
Die sechs LPs und sämtliche nativen Richtungs-/Schrittprüfungen sind inzwischen
ausgeführt und unabhängig auditiert. Alle sechs echten Schritte verschlechtern
den Flux und verletzen die Konstruktionsbedingungen. Die späteren
Vorbereitungsabschnitte halten den vorherigen Implementierungsstand fest.

## Sechs lineare Teilprobleme abgeschlossen

Ausführung bei849809f: alle sechs HiGHS-DS-LPs erfolgreich, sechs unabhängige
skalare Primal-Dual-Zertifikate bestanden. Der separate Dateiaudit bestätigt
Quellen, explizite204-Spalten-Zuordnung, Modelle, Schritte, Kosten und Zertifikate,
ohne neue LP- oder native Rechnung. Höchster normierter Primalrest1,377e-14,
Stationaritätsrest2,776e-17, normierte Dualitätslücke2,221e-16.
Je18 Einzelchecks pro Modell plus zwei Fall-/vier Gesamtchecks bestätigen die
vollständige Ablage. Als nichtverschwindende Ungleichungs-Marginalwerte treten
beim AL-Fall das Paar(8,12), ab Radius1e-5 zusätzlich die Länge auf; beim
SLSQP-Fall bei allen Radien Länge sowie Paare(0,1) und(8,12). Alle Zahlen im
Solverprotokoll. Das sind aktive Zeilen des skalierten LPs, keine neuen
physikalischen Grenzen oder belastbaren technischen Kostenprioritäten.

| Quelle | Radius | Vorhergesagte Roh-Fluxänderung |
| --- | --- | --- |
| AL | 1e-6 | −1,48199958e-11 |
| AL | 1e-5 | −3,31317841e-11 |
| AL | 1e-4 | −1,69744571e-10 |
| SLSQP | 1e-6 | −1,80236672e-12 |
| SLSQP | 1e-5 | −1,81506554e-11 |
| SLSQP | 1e-4 | −1,81633542e-10 |

Die Modelle enthalten somit Abstiegsrichtungen. Das zeigt weder einen echten
Fluxgewinn noch erhaltene Geometrie bei endlicher Schrittweite und ist kein
Nachweis globaler oder nichtlinearer Optimalität. Die sechs LPs brauchen jeweils
1–6 Simplexiterationen; tatsächliche Auswertungsarbeit bleibt null neue native
Bundles. Native Ableitungs- und Schrittqualifikation folgt mit unverändertem
registriertem Höchstbudget32, allen Radien und beiden Differenzenschritten.

Evidenz: `evidence/geometric-models-v1.json`, `...-audit.json`, beide Driver-
Verzeichnisse und `artifacts/geometric-models-v1/`. Quellen/alte Ergebnisse bleiben
unverändert; weitere Formsuche wird nicht aus einer bloßen LP-Verbesserung freigegeben.

## Native Prüfung vollständig abgeschlossen

Ausführung bei7ba5523: alle32 vollständigen nativen Bundles abgeschlossen,
Quellwerte und ganze Jacobimatrizen innerhalb1e-12 reproduziert. Alle sechs
Richtungen bestehen **beide** festen Nicht-Paar-FD-Schirme (Maximum4,901e-7
gegen1e-6), beide komplexen Paarprüfungen (Maximum1,146e-12 gegen1e-9) und die
Schrittstabilität. Damit wurden alle sechs vorgesehenen Kontrollschritte
ausgewertet und serialisiert, keine nachträgliche Radiusauswahl.

| Quelle | Radius | Tatsächliche Fluxänderung | Roh-Flux danach | Größte Konstruktionsverletzung |
| --- | --- | --- | --- | --- |
| AL | 1e-6 | +1,73345106e-11 | 8,95651483e-8 | 3,16758844e-7 |
| AL | 1e-5 | +1,50335624e-8 | 1,04581376e-7 | 5,51372207e-7 |
| AL | 1e-4 | +1,54237630e-6 | 1,63192412e-6 | 5,34632131e-5 |
| SLSQP | 1e-6 | +1,22253122e-10 | 8,20375955e-8 | 4,91899455e-8 |
| SLSQP | 1e-5 | +1,24001897e-8 | 9,43155321e-8 | 4,88091171e-6 |
| SLSQP | 1e-4 | +1,24622821e-6 | 1,32814355e-6 | 4,29005165e-4 |

Die letzte Spalte ist der größte negative normierte direkte g-Wert. Alle
überschreiten die unveränderte Auswahlgrenze1e-8. Das ist eine Verletzung der
strengeren Konstruktionsbedingungen, nicht die Behauptung einer ausgeführten
feinen Geometrieabnahme oder sechs neuer physikalisch vollständig qualifizierter
Entwürfe. Ströme und Summenkonvention bleiben bei sämtlichen Schritten unverändert.

Der unabhängige Audit besteht alle250 Einzelchecks (je32 auf Fallebene plus
dreimal31 Richtungschecks). Aus JSON rekonstruierte16-Kopien-Geometrie,
reelle Fouriersummen und gewichtete Paar-Kettenregel bestätigen die Ableitungen
bis1,145e-12. Alle Vorhersage-/Istwerte, negativen Geometrie-/Fluxklassifikationen,
FD-Probes und nativen Arbeitszähler stimmen. Kein zusätzlicher LP-, nativer
oder komplexer Aufruf im Audit, zwei eigene reelle120-Paar-Läufe mit je drei
Richtungen. Die Auditfreigabe bestätigt die negative Diagnose, keinen Entwurf.

Arbeitsbilanz der nativen Phase:32 komplette Bundles/32 B-Anfragen/32 B-VJPs,
zusätzlich32 einzelne native Kurvenpositionsanfragen, zwei unabhängige reelle
und zwölf komplexe120-Paar-Wertläufe. Jede Anfrage einschließlich Cachelesezugriff
gezählt; etwa4,1MiB neue Rohdaten. Keine Unterbrechung oder Umgebungsänderung.

**Folgerung:** Das lineare Modell ist für diese festgelegten endlichen Schritte
ungeeignet, obwohl die lokalen Ableitungen stimmen. Ein lokales oder globales
Optimum ist damit weder bewiesen noch widerlegt. Die starke nichtlineare
Krümmung ist eine plausible Ursache, die getrennt mit dem bereits geprüften
quadratischen Fluxmodell an genau diesen Quellen und Probes untersucht werden
sollte. Auch der Nutzen gekoppelter Stromanpassung bei Formänderungen folgt
nicht aus dem zuvor winzigen statischen Stromgewinn. Keine Grenzlockerung oder
nachträgliche Auswahl kleinerer Probes in diesem geschlossenen Versuch.

Evidenz zusätzlich: `evidence/geometric-probes-v1.json`, `...-audit.json`, beide
Driver-Verzeichnisse und `artifacts/geometric-probes-v1/`. Dieser begrenzte Versuch
ist geschlossen, Schritt1/2 bleiben offen. Nächster Schritt ist eine separat
registrierte Krümmungs-/Konditionierungsdiagnose vor einem weiteren Suchlauf.

Der Modellbauer erhält alle Ungleichungen und benutzt unverändertb=g/r, ohne
Addition einer Zulässigkeitstoleranz. Ein verschwindender Gradient wird separat
gemeldet. Der HiGHS-Adapter hat ausschließlich die registrierten Optionen und
bewahrt auch erfolglose Solver-Rückgaben ohne erfundenen Lösungspunkt.

Der getrennte Zertifikatsprüfer benutzt skalare Summen, keinen LP-Löser: primale
Zulässigkeit, Marginal-Vorzeichen, Stationarität, Komplementarität und duale
Kostenlücke. Acht analytische/negative Kontrollen bestehen, einschließlich eines
bekannten Optimums mit gleichzeitig aktiver Ungleichung und Boxgrenze, absichtlich
falscher Dualzeichen/Primalpunkte/Zielfunktion/NaNs, Nullgradient und tatsächlich
unlösbarem LP. Ruff und Dokument-/Diffprüfung bestehen. Dies ist eine Prüfung
des linearen Werkzeuges, keine neue physikalische Optimalitätsaussage.

Nächster Schritt: verbindliche Zwei-Quellen-/DOF-Zuordnung, sechs gespeicherte LPs,
native Richtungs-/Schrittproben und deren separater Quellen-/Kettenregel-Audit.

## Quellgebundener Modelllauf vorbereitet

Der additive Treiber bindet genau die beiden abgeschlossenen Stromminimierer
und sämtliche zugehörigen Qualifikations-/Holdoutaudits. Aus dem vollständigen
serialisierten Stromgraphen werden drei Stromspalten identifiziert, alle204
anderen Spalten bilden den unveränderten geometrischen Suchraum. Benannte
Quellvektoren und exakt stromunabhängige137 Geometriezeilen werden geprüft.

Sechs feste LPs speichern vollständige Eingaben, Solverausgaben/Marginalwerte,
geometrische Schritte und lineare Vorhersagen. Separater Dateiaudit rekonstruiert
die Matrix und prüft alle Primal-Dual-Nachweise ohne weitere LP-Lösung. Drei
synthetische Ablaufkontrollen bestehen: kompletter Sechserlauf/Audit, manipulierter
Dualwert/Radiusreihenfolge/Quellvektor/Stromableitung sowie erhaltener Eingabesatz
bei absichtlich unterbrochenem Solver. Insgesamt elf neue Modellkontrollen bestanden.
Noch keine echte Modell- oder Feldrechnung; nach Commit zunächst alle sechs
Modelle und ihren Audit schließen, danach die bereits festgelegten nativen
Ableitungs- und Kontrollschritte. Keine Anpassung der Radien aus LP-Ergebnissen.
Gesamte Regression645 Tests bestanden,144 bekannte Fixture-DeprecationWarnings;
Ruff/Dokumentstruktur/Diffprüfung bestanden. Strenge Importqualifikation weiterhin offen.

## Native Richtungs-/Schrittphase vorbereitet

Additiver Treiber übernimmt exakt die sechs abgeschlossenen LP-Punkte. Er
reproduziert die Quellen samt ganzer138x207-Jacobimatrix, prüft pro Richtung
beide festen zentralen Differenzen und beide komplexen Paarableitungen und
erlaubt erst danach den einen echten Kontrollschritt. Alle Bundles, auch die
vollständigen Jacobimatrizen, angefragte Fehlerpunkte, Positionsdaten und jeder
komplexe Zwischenwert werden erhalten. Keine weitere LP- oder Stromoptimierung.

Der separate Auditor liest Fourierkoeffizienten/Symmetrien aus JSON und prüft
alle Paarableitungen mit reellen Fouriersummen/gewichteter Kettenregel. Er
verifiziert auch sämtliche16 Kopien und Regularisierungen jedes neuen Feldes,
die feste Stromverteilung, FD-Punkte und Vorhersage-/Ist-Klassifikation.

Sechs neue Kontrollen bestehen: beide FD-Schrittweiten zwingend, komplexer
Gegenfall/NaN, Verbesserung ohne geometrische Freigabe, kompletter synthetischer
32-Bundle-Ablauf mit echter Fourier-/komplexer-/reeller Gegenrechnung, negative
Ableitungsklasse mit weiterlaufenden übrigen Richtungen und erhaltene native
Unterbrechung. Ein erster Patch passte nach automatischer Formatierung nicht
mehr auf den Quelltext und wurde ohne Änderung abgelehnt; anschließend gezielt
auf die gelesene Fassung angewandt. Keine echten Spulenprobes bisher.

Gesamte Regression651 Tests bestanden,144 bekannte Fixture-Warnungen; Ruff,
Dokumentstruktur und Diffprüfung bestanden. Nach Implementierungscommit folgen
die vorab registrierten echten Probes und ihr unabhängiger Audit.
