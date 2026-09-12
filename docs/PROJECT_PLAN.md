# Arbeitsplan und Erfolgskriterien

Stand: 12. September 2026. [Projektfrage](README.md) · [Ergebnisstand](STATUS.md)

## Aktuelles Ziel

Langfristiger Plan **Schritt 1 und 2 wirklich abschließen**, nicht lediglich
Versuchslisten abarbeiten. Unabhängige Prüfung begleitet die gesamte Arbeit;
ein negativer Pilot ist kein Abschluss des Forschungspakets. Beide Schritte
sind noch offen. Die [Entwicklungsrichtung](README.md#langfristiger-plan-und-aktueller-schwerpunkt)
bleibt unverändert.

## Schritt 1: Rechen- und Prüfwerkzeuge absichern

| Arbeitspaket | Bereits belegt | Für den Abschluss noch erforderlich |
| --- | --- | --- |
| Lokale Reproduzierbarkeit | Frischer gesperrter Daten-/Solveraufbau, alle 21 Phasen und sechs wissenschaftliche Nicht-Skip-Tests bestehen | Bestehende Regression sichern; strenge Importwarnung getrennt klären. Unabhängige Hardware/Hosted-CI als separate Ausführungsgrenze erhalten |
| W7-X-Referenz | Ausgewählte physikalische Regression besteht | 60/63 nicht zu vollständiger Dateigleichheit umdeuten; verbleibende Ausgabedifferenzen getrennt halten |
| Magnetfeld/Spulengeometrie | Quellen, benannte DOFs, unabhängige Felder und konservative Geometrieprüfungen qualifiziert | Neue Suchzustände weiterhin unabhängig qualifizieren; Filament-/Gleitkommagrenzen explizit halten |
| QI-Maßstab | Tracer/Quadratur, Gauge-Algebra und umfangreiche Feld-/Auflösungsdiagnosen auditiert | Physikalische absolute Drift gegen Wirkungsableitung, feste Invarianten-/Mulden-Domäne, Auflösungs- und Produzentenfragen; keine unbegründete Ersetzung der Autorenreferenzen |
| Ingenieurmodelle | Sechs unveränderte Netze bestehen den abgegrenzten Nichtüberlappungstest | Nachbarpaare, vollständige Baugruppe/reale Wicklungspakete, belegte Materialien/Lagerung und Mechanik im gültigen Modellbereich |

Nächste QI-Frage: Welche verbleibenden Feldunterschiede stammen aus innerer
Moden-/Gleichgewichtsauflösung oder Produzentenkonventionen? Die 16-Zellen- und
gemeinsame-Winkel-Studie sind abgeschlossen, aber insgesamt negativ.
Die [Drift-Koordinateneinordnung](qi/QI_DRIFT_COORDINATES.md) verlangt, das ganze
Driftpaar und dieselbe physikalische Phase zu vergleichen; reine Algebra ersetzt
keine absolute physikalische Gegenrechnung.

Nächste Ingenieurfrage: Was fehlt nach dem geschlossenen Nicht-Nachbar-Paartest
für eine gültige endliche Spulenbaugruppe? Geometrische Teilnachweise erlauben
keine Übernahme der bisherigen mechanischen Spannungszahlen: Die große berechnete
Verformung liegt außerhalb der linearen Modellannahmen.

## Schritt 2: Spulen für eine feste Plasmaoberfläche entwickeln

Abschlusskriterium: eine starke klassische Lösung des unveränderten physischen
LPQA-Problems, die unabhängige Feld-, kontinuierliche Geometrie- und zusätzliche
native Abnahmen besteht. Danach Wiederholungen, mindestens fünf dokumentierte
Initialisierungen und faire Vergleiche unter gleichen Anforderungen und bilanzierten
Budgets. Mehr Freiheitsgrade, andere Starts oder Solvervarianten sind getrennte
Versuche, keine rückwirkende Umdeutung früherer Resultate.

Aktueller Stand: beste fein geprüfte Form rund 8,19-mal über der Fluxgrenze.
Die exakte Stromminimierung und die geometrische Abstiegsdiagnose sind vollständig
geschlossen: statische Stromkorrekturen helfen praktisch nicht; alle sechs
endlichen Formschritte verschlechtern den Flux trotz bestandener Ableitungen.

Nächste Reihenfolge:

1. **Registrierte [Krümmung/Konditionierungsprüfung](optimization/GEOMETRIC_CURVATURE_PROTOCOL.md) ausführen:** bereits bewährtes
   quadratisches Fluxmodell an genau den zwei aktuellen Quellen und sechs
   festgehaltenen Probes untersuchen. Keine neuen Radien aus den Ergebnissen wählen.
2. **Nächsten klassischen Suchlauf begründen und vorab festlegen:** etwa ein
   geeignet qualifiziertes krümmungsberücksichtigendes Verfahren oder eine
   Konditionierungsänderung. Keine Behauptung, dass fehlender statischer
   Stromspielraum gekoppelten Strom-/Formanpassungen jeden Nutzen nimmt.
3. **Startqualifikation, begrenzte Suche, unabhängiger Audit:** alle physikalischen
   DOFs explizit zuordnen, gesamte Rechen-/Ableitungsarbeit erfassen, keine
   parallelen schweren Installationen oder nachträgliche Budgeterhöhung.
4. **Alle unabhängigen Abnahmen schließen, auch bei Ablehnung.** Erst eine
   tatsächlich zulässige Konstruktion löst die mehrstartige Vergleichsphase aus.

Die alten AL-, SLSQP-, GN-, Archiv- und Diagnoseläufe bleiben mit ihren
Fehlschlägen unverändert im [Optimierungsbereich](optimization/README.md)
und [Journal](logbook/README.md). Es wird kein günstigerer Differenzenschritt
nachträglich zum ursprünglichen Bestehenskriterium gemacht.

## Danach: QI-Plasma und Spulen gemeinsam entwickeln

In Schritt 3 wird die Plasmaoberfläche selbst zum Entwurfsparameter; die
Einschlussphysik muss am zugehörigen Gleichgewicht geprüft werden. Schritt 4
verknüpft Plasma, endlichen Druck, Spulen, Baubarkeit und Robustheit. Schritt 5
belegt einen Vorteil gegenüber reproduzierten Referenzen unter gleichen
Anforderungen. Lernende Modelle, globale Suche und hybride Methoden werden
eingesetzt, wenn ihr messbarer Nutzen gegenüber starken klassischen Verfahren
gezeigt werden kann — nicht weil AI am Projekt beteiligt ist.

SQuID-C benötigt autoritative Daten und eine qualifizierte Reproduktion.
Das ist keine pauschale Vorbedingung für die derzeitige Arbeit, aber fehlende
Daten sind auch nicht die einzige offene Bereitschaftsprüfung.
Die vollständige [Prüfliste](squid_c/SQUID_C_READINESS.md) bleibt maßgeblich.

## Verbindliche Arbeitsweise

Neue Studien vorab registrieren und committen. Nach jedem abgeschlossenen
Arbeitsschritt Detailbericht und Prüfprotokoll ergänzen, materialisierte Befunde/
Entscheidungen ins Journal aufnehmen und beide READMEs, Stand, Plan und Bereichsindex
prüfen. Passende Tests, Dokumentprüfung, Diffreview und lokaler Commit gehören
zum Abschluss. Negative Resultate und unterbrochene Läufe bleiben erhalten.

Keine Veröffentlichungen, Pushes, Autorenkontakte oder Änderungen externer
Repositories ohne passenden Auftrag. Ressourcenvorabprüfung, laufende Reserven
und Schutz der qualifizierten Umgebungen einhalten. Ein verhinderter Commit
oder fehlende neue Autorität bleibt explizit offen.
Dauerhafte Regeln: [AGENTS.md](../AGENTS.md).
