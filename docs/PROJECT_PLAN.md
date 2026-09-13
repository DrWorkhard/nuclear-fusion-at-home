# Arbeitsplan und Erfolgskriterien

Stand: 13. September 2026, nach ausdrücklicher Schärfung durch den Nutzer.
[Projektfrage](README.md) · [Ergebnisstand](STATUS.md)

## Jetzt: Basis abschließen, prinzipiell iterieren können

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

## Aktuelle Reihenfolge und Stoppregel

1. Plan-/Umfangskorrektur und unveränderten Altbestand sichern.
2. Bestehende Qualifikationen zusammenführen, Schutz gegen falsche Freigaben testen.
3. Aktuelle Regressionen, kurzen realen Zweiarmzyklus und alle unabhängigen
   Abnahmen ausführen; Ergebnisse separat auditieren und dokumentieren.
4. Beide geschärften Schritte nur bei bestandenen zugeordneten Gates schließen.
   **Dann an den Nutzer übergeben, keine weitere Forschung automatisch starten.**

Kein erneuter langer Optimierungslauf und kein neuer Physikzweig, sofern er nicht
eine konkrete Lücke dieser Basisabnahme schließt. Tests allein ersetzen keine
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
