# Geometrischer Abstieg: sechs lineare Modelle auditiert, echte Schritte offen

2026-09-12, [Protokoll](GEOMETRIC_DESCENT_PROTOCOL.md) bei a56c9e1 registriert.
Die sechs LPs aus tatsächlichen Spulendaten sind inzwischen ausgeführt und
unabhängig auditiert. Noch keine neue native Formauswertung. Die späteren
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
