# Arbeitsplan und Erfolgskriterien

Stand: 12. September 2026. [Projektfrage](README.md) · [Ergebnisstand](STATUS.md)

## Nächstes entscheidendes Ergebnis

Eine klassische, unabhängig zulässige LPQA-Spulenkonstruktion. Die bisherigen
Zeit- und Auswertungsbudgets sind sauber geprüft, aber alle neuen Kandidaten
fallen durch den Holdout. Deshalb zuerst die Durchsetzung der Randbedingungen
verbessern, nicht bereits eine neue Optimierungsmethode als überlegen bezeichnen.

1. Erledigt: konservative glatte Ungleichungen aus roher Länge, Krümmung und
   Abständen implementiert; analytische Kontrollen und vollständige
   Richtungsableitungen an zwei festgelegten physikalischen Zuständen bestehen.
2. Erledigt: getrennt festgelegter SLSQP-Pilot mit zwei identischen 256-Bundle-Läufen;
   der ausgewählte Kandidat bleibt im Flux-Holdout unzulässig (Faktor 23,3).
3. Erledigt für diesen Pilot: unabhängige feine Gitter, kontinuierliche
   Geometrieschranken und zusätzliche native Bedingungen. Die getrennte
   quadratische Feldmodellprüfung besteht an allen vier eingefrorenen Proben,
   einschließlich vollständigem nativen Matrixvergleich und Kern-Audit.
4. Der [GN-Trust-Pilot](optimization/GN_TRUST_PILOT_RESULTS.md) stoppt am 29.
   Vorschlag durch die Feld-/Gradient-Schutzprüfung. Der begrenzte Fehlerreplay
   stimmt exakt überein. Die isolierte Feld-/Matrix-/Stromprüfung identifiziert
   unterschiedliche Feldprojektionsrundung im Prüfvergleich. Als Nächstes die
   konsistente native Projektion ist an drei festen Zuständen qualifiziert; der
   korrigierte Pilot läuft. Als Nächstes beide Arme abschließen und unabhängig
   prüfen. Danach den getrennt festgelegten SLSQP-1024-Lauf vom Originalstart
   ausführen, ohne die alten Versuche zu verändern oder Holdouts zurückzuspeisen.
   Keine nachträgliche Budgeterhöhung des abgeschlossenen SLSQP-Piloten.
5. Bei Zulässigkeit: Wiederholungen und mehrere Startpunkte, anschließend eine
   starke klassische Vergleichsbaseline unter gleichen Rechenbudgets.

Ausgangspunkt: [direkte Ungleichungen](optimization/DIRECT_INEQUALITY_QUALIFICATION_PROTOCOL.md).
Ein negatives Ergebnis schließt diesen Versuch, nicht automatisch das Arbeitspaket.

## Forschungspakete und Abnahme

| Paket | Noch zu lieferndes Ergebnis | Woran es beurteilt wird |
| --- | --- | --- |
| Reproduzierbarkeit | Vollständige wissenschaftliche Integration aus frischem Daten-/Solveraufbau | Gepinnte Quellen, neue Umgebung, explizite Nicht-Skips und dokumentierte Abweichungen |
| Optimierungsbaseline | Zulässige starke klassische Lösung, danach mehrstartiger Vergleich | Gleiche Probleme/Budgets; serialisierte Ergebnisse bestehen unabhängige Grenzprüfungen |
| W7-X-Regression | Bestehende Teilprüfung sichern; drei Ausgabedifferenzen getrennt halten | Keine Umdeutung von 60/63 in vollständige Übereinstimmung |
| QI-Maßstab | Qualifizierte QI-/radiale-Wirkungsbewertung mit größerem Gültigkeitsbereich | Unabhängige Tracer/Integration, Domänenabdeckung, Mulden-Identität, Gauge- und Gleichgewichtsauflösung |
| Ingenieurmodelle | Physikalisch gültige endliche Spulengeometrie und Mechanik | Keine nichtlokalen Überschneidungen; belegte Materialien/Lagerung; Konvergenz im gültigen Modellbereich |
| SQuID-C | Exakte kanonische Reproduktion und übertragbare Bewertung | Autoritative Daten plus reproduzierte publizierte Größen, nicht nur erfolgreicher Import |

Die [detaillierten Gates](squid_c/SQUID_C_READINESS.md) sind die vollständige
Prüfliste. Das [Journal](logbook/README.md) enthält den Arbeitsnachweis.

## Reihenfolge nach der klassischen Baseline

QI-Messung und Ingenieurprüfungen qualifizieren, anschließend robuste Optimierung
und freie Plasmareaktion zusammenführen. Langfristig eigene magnetische
Plasmaoberflächen und QI-Gleichgewichte entwickeln: Die Oberflächenform wird
selbst zum Entwurfsparameter, die Einschlussphysik am zugehörigen Gleichgewicht
bewertet. Plasmakonfiguration und Spulen anschließend gemeinsam weiterentwickeln,
damit Anforderungen an baubare und robuste Spulen auf den Plasmaentwurf
zurückwirken. Die [Gesamtübersicht](README.md#langfristiger-plan-und-aktueller-schwerpunkt)
ordnet diese geplanten Arbeiten gegenüber dem aktuellen Schwerpunkt ein.
Erst dann lohnt sich eine Aussage über
eine bessere Physik–Ingenieur-Paretofront. Lernende Surrogate, Active Learning,
globale oder hybride Verfahren werden eingesetzt, wenn ihr messbarer Nutzen
gegen die klassische Baseline geprüft werden kann.

Es gibt keine zugesagte Reihenfolge, in der alle Forschungsprobleme lösbar sind.
Ein größerer Suchlauf darf seine schwächste Validierungsstufe nicht überholen.
Die bisherigen QI- und Ingenieurdaten erlauben interne Weiterarbeit; SQuID-C-Daten
sind dafür keine pauschale Vorbedingung.

## Arbeitsweise

Neue Versuche vorab festlegen und committen; Ergebnisse, Gegenprüfungen und
Fehlschläge danach getrennt dokumentieren und committen. Nutzeränderungen und
historische Evidenz bleiben erhalten. Keine Publikation, Autorenkontakt oder
externen Änderungen ohne entsprechenden Auftrag. Nach jedem abgeschlossenen
Arbeitsschritt werden die betroffene Detaildokumentation und das Prüfprotokoll
ergänzt, auch bei negativen Ergebnissen oder Blockern. Beide READMEs, Ergebnisstand,
dieser Plan und die jeweilige Bereichsübersicht werden dabei geprüft und bei
inhaltlichen Änderungen aktualisiert. Dokumentationsprüfung, passende Tests und
ein lokaler Commit gehören zum Abschluss; ein verhinderter Commit bleibt explizit
offen. Die dauerhafte Abschlusscheckliste steht in [AGENTS.md](../AGENTS.md).
