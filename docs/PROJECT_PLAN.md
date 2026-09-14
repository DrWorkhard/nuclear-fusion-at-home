# Arbeitsplan und Erfolgskriterien

Stand: 14. September 2026, nach erster eigener Plasma-Suchentscheidung.
[Projektfrage](README.md) · [Ergebnisstand](STATUS.md)

**Abnahme abgeschlossen: Schritt1 PASS, Schritt2 PASS.**
[Abschluss und Bedienung](validation/FOUNDATION_ACCEPTANCE_RESULTS.md), Lauf
`foundation-acceptance-v2` bei1aa28b6: alle zugeordneten Gates bestanden.
Diese Abgrenzung bleibt verbindlich. Der Nutzer hat danach ausdrücklich
Schritt3 beauftragt; die bisherige automatische Stoppregel ist erfüllt.

## Jetzt: Schritt3 — eigene QI-nahe Plasmaoberfläche

Aktiv nach neuem Nutzerauftrag. Vier benannte Fourierkoeffizienten eines offenen
Goodman-nfp2-Vakuumfalls variieren, jedes zugehörige Gleichgewicht neu lösen und
eine auf registrierter Domäne numerisch bestätigte QI-relevante Verbesserung
erzielen. Keine Spulenoptimierung als Ersatz. Das
[vorab festgelegte Protokoll](qi/PLASMA_OPTIMIZATION_PROTOCOL.md) verlangt unabhängige
feinere Domänen-/Kontur-/Feld-/Aktionsprüfungen und reproduzierbaren Entwurf.
Nur Ablauf oder negativer Versuch reicht diesmal nicht; SoTA gehört weiterhin
zu Schritt5. Globale Orbit-/Druck-/Stabilitäts-/Kraftwerksqualifikation bleibt getrennt.
Erster Versuch vollständig abgeschlossen und Entwurf abgelehnt:14,35%
Trainingsgewinn, aber15,53% schlechter auf erweiterter Domäne und20 lokale
Wirkungsverletzungen. Die numerischen/Quellenprüfungen bestehen.
Jetzt gezielten Folgeversuch mit beiden Domänen und lokalen Wirkungswächtern
vor der Konstruktion registrieren; [Befund](qi/PLASMA_OPTIMIZATION_RESULTS.md).
Schritt3 ist noch offen; nach bestandenem Abschluss Übergabe, kein automatischer Schritt4.

## Abgeschlossene Etappe: Basis und prinzipielle Iterationsfähigkeit

Schritt1 und2 sind **Befähigungsziele**, keine Neuheits- oder Leistungsziele.
Der Nutzer hat den bisherigen zu breiten Umfang korrigiert. Eine neue zulässige
Spulenform, ein SoTA-Vorteil oder vollständige SQuID-C-Qualifikation sind keine
Voraussetzung für ihren Abschluss. Physikalische Zulässigkeitsgrenzen bleiben
unverändert; ein funktionierender Ablauf darf einen Entwurf weiterhin ablehnen.

Die abgegrenzte erste Basis ist lokale Festoberflächen-/Filamentspulenarbeit am
bekannten LPQA-Fall, ergänzt um W7-X-Gleichgewichtsregression und grundlegende
Goodman-Daten-/Wirkungsregressionen. Das ist ausdrücklich **keine universelle
Stellarator-, QI- oder Ingenieurqualifikation**.

## Schritt 1: Verlässliche Rechen- und Prüfbasis

Abnahme anhand des [festen Basisprotokolls](validation/FOUNDATION_ACCEPTANCE_PROTOCOL.md):

| Notwendige Fähigkeit | Abnahme |
| --- | --- |
| Reproduzierbare lokale Umgebung und Daten | Gesperrte Quellen/Versionen, erhaltene frische Aufbau-Evidenz, aktuelle Tests ohne fehlende Pflichtdaten |
| Bekannte Gleichgewichte/Daten lesen und vergleichen | Sechs strikte W7-X-/Goodman-Regressionsidentitäten ohne Skip; bestehende W7-X-Physikprüfung und bekannte60/63-Grenze erhalten |
| LPQA-Feld und Filamentgeometrie auswerten | Qualifizierte Werte/Ableitungen/benannte Parameter, unabhängige Feld-/Geometrieabnahme und Verfeinerung |
| Zutreffend akzeptieren oder ablehnen | Prozessstatus, Werkzeugqualifikation und Entwurfszulässigkeit getrennt; Manipulationen/fehlende Daten dürfen keinen Pass erzeugen |
| Nachvollziehbarkeit und praktische Nutzung | Ein dokumentierter Abnahmebefehl, gebundene Rohdaten/Berichte, Gültigkeitsbereich und offene Erweiterungen explizit |

Die bekannte netCDF-Größenwarnung wird sichtbar nachgeprüft und als verbleibende
Umgebungsgrenze dokumentiert. Kein neuer Filter, kein behaupteter ABI-Nachweis.
Warnungsfreie strenge Imports sind nicht mit funktionierender gesperrter
Datenregression gleichzusetzen. Unbekannte neue Fehler führen zur Ablehnung.

## Schritt 2: Reproduzierbarer Iterationszyklus

Abschluss heißt: Referenz laden → Parameter variieren/klassisch optimieren →
Kandidat speichern → unabhängig bewerten → Ergebnis und nächste Entscheidung
nachvollziehen. Ein kleiner realer Zweiarm-Smoke-Lauf demonstriert diesen Weg;
vollständige frühere Suchläufe liefern zusätzlich erhaltene Langlauf-Evidenz.

Keine Pflicht zu neuem Bestwert, erfüllter Fluxgrenze, Konvergenz oder fünf Starts.
**Eine abgelehnte Form bleibt abgelehnt; der funktionsfähige Iterationszyklus kann
trotzdem bestehen.** Solver, Parameter, Budget und Rohdaten bleiben zugänglich,
sodass später gezielt weitere Experimente registriert werden können.

## Abgearbeitete Reihenfolge und Stoppregel

1. Plan-/Umfangskorrektur registriert und Altbestand durch lokalen Tag gesichert.
2. Qualifikationen zusammengeführt;20 neue Schutz-/Workflowkontrollen bestanden.
3. Aktuelle Regressionen, realen Zweiarmzyklus und alle unabhängigen Abnahmen
   ausgeführt. Ersten Verwaltungsfehler erhalten/korrigiert, frische Wiederholung bestanden.
4. Beide geschärften Schritte anhand bestandener Gates geschlossen; Abschluss
   dokumentiert. **An den Nutzer übergeben, keine weitere Forschung automatisch starten.**

Die damalige Begrenzung weiterer Forschung galt bis zur neuen ausdrücklichen
Beauftragung von Schritt3. Tests allein ersetzen weiterhin keine
physikalische Teilqualifikation; vorhandene negative Evidenz wird nicht umetikettiert.

## Erhaltene spätere Forschung

| Thema | Einordnung nach Abschluss der Basis |
| --- | --- |
| Zulässige starke klassische Lösung, Mehrstarts, faire Methodenvergleiche | Spätere Leistungsbaseline; aktueller feinster Flux8,129882e-8 bleibt über1e-8 |
| Eigene QI-Plasmaoberflächen | Langfristiger Schritt3; neue Gleichgewichts-/QI-Abnahme vor Optimierung nötig |
| Gemeinsame Plasma-/Spulenoptimierung | Langfristiger Schritt4; getrennte Daten-/Physikvoraussetzungen |
| Globale QI-/maximum-J-Messung, endliche Teilchenbahnen | Offene Qualifikationen, nicht für den begrenzten LPQA-Filamentzyklus freigegeben |
| Endliche Wicklungspakete, vollständige Netze, Materialien/Lagerung/Mechanik | Vor Ingenieuraussagen zu qualifizieren; alte lineare Verformungszahlen nicht zulässig |
| SoTA-/Paretofortschritt, SQuID-C-Reproduktion | Langfristiger Schritt5 beziehungsweise gesonderte Zielbaseline; keine heutige Behauptung |

Protokolle, Daten, Fehlschläge und Ableitungs-/Driftdiagnosen bleiben in den
[Detailbereichen](README.md#detailbereiche) und im [Journal](logbook/README.md)
erhalten. Der Zustand vor dieser Umfangskorrektur ist Git-Commit5971fee; die
Abnahme dokumentiert seinen Erhalt. Historische Abschlussformulierungen beziehen
sich auf den damaligen breiteren Plan und werden nicht rückwirkend geändert.

## Verbindliche Arbeitsweise

Neue numerische Versuche vorab registrieren und committen. Nach jedem Arbeitsschritt
Detailbericht/Prüfprotokoll ergänzen, betroffene Übersichten aktualisieren, passende
Tests/Dokument-/Diffprüfung durchführen und lokal committen. Keine Pushes,
Autorenkontakte, externen Quelländerungen oder Eingriffe in die qualifizierte
Umgebung. Ressourcenreserve und Schutz vorhandener Daten bleiben verbindlich.
[Dauerhafte Regeln](../AGENTS.md) · [Entscheidung D-012](logbook/DECISIONS.md)
