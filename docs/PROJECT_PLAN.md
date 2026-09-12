# Arbeitsplan und Erfolgskriterien

Stand: 12. September 2026. [Projektfrage](README.md) · [Ergebnisstand](STATUS.md)

## Nächstes entscheidendes Ergebnis

Eine klassische, unabhängig zulässige LPQA-Spulenkonstruktion. Die bisherigen
Zeit- und Auswertungsbudgets sind sauber geprüft, aber alle neuen Kandidaten
fallen durch den Holdout. Bei den neuesten Kandidaten bestehen die geprüften
Geometriebedingungen; jetzt den Magnetfeldfehler unter unveränderten Grenzen
senken, nicht bereits eine neue Optimierungsmethode als überlegen bezeichnen.

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
   unterschiedliche Feldprojektionsrundung im Prüfvergleich. Die konsistente
   native Projektion ist an drei festen Zuständen qualifiziert; beide korrigierten
   1024-Bundle-Läufe und ihr unabhängiger Protokoll-Audit bestehen, der grobe Flux
   bleibt Faktor 24,7 über der Grenze. Der getrennte SLSQP-1024-Lauf ist ebenfalls
   intern exakt reproduziert (grober Flux Faktor 12,7), scheitert aber am
   geforderten historischen Präfix. Die feine GN-Abnahme ist abgeschlossen:
   Geometrie/nativ bestehen, Flux abgelehnt. Auch SLSQP ist fein geprüft:
   Geometrie/nativ bestehen, Flux Faktor 12,665 zu hoch. Jetzt den
   durch Speicherplatzmangel unterbrochenen natürlichen Flux-AL-Piloten aufarbeiten;
   erster Arm und gespeichertes 700-Bundle-Präfix unabhängig bestätigt. Der native
   Ressourcen-Retry ist bestanden. Die getrennte AL-Wiederholung besteht nun
   beide vollständigen Suchpfade und historischen Präfixaudits bei unveränderten
   Optionen. Sämtliche feinen Abnahmen abgeschlossen: Geometrie/nativ bestehen,
   Flux Faktor26,9859 zu hoch. Dieser begrenzte Versuch ist geschlossen.
   Keine parallelen schweren Installationsarbeiten.
   Keine nachträgliche Budgeterhöhung oder
   veränderte Annahmekriterien.
   Ein anschließender [Jacobispalten-Skalierungsversuch](optimization/NATURAL_AUGLAG_JAC_PROTOCOL.md)
   ist getrennt vorab festgelegt: nur `x_scale=jac` statt1, keine geänderte Physik.
   Recovery/Abnahme ist geschlossen und committed; auch beide skalierten
   Suchläufe, unabhängiger Audit und alle feinen Abnahmen sind abgeschlossen.
   Flux rund11,4% kleiner bei höherer Krümmung, weiterhin Faktor23,91 über Grenze.
   Daneben ist die [Bestandsaufnahme vorhandener LPQA-Felder](optimization/UPSTREAM_LPQA_INVENTORY_RESULTS.md)
   unabhängig abgeschlossen: fünf Metadatenkandidaten für separate Rekonstruktion,
   keine ungeprüfte Übernahme als zulässige Baseline oder neue Suchinitialisierung.
   Deren [statische Rekonstruktion](optimization/UPSTREAM_LPQA_RECONSTRUCTION_RESULTS.md)
   ist vollständig abgeschlossen: Quellen/Felder und geometrische Gitterschirme
   bestehen, Roh-Flux bei allen fünf rund100-mal zu hoch. Als nächsten getrennten
   Konstruktionsstart den bereits vor jeder Feldrechnung erstplatzierten
   Archiveintrag untersucht: explizite Anpassung an dieselbe feste Stromsumme,
   neue Startqualifikation samt unabhängigem Audit bestanden, keine Auswahl/
   Toleranzanpassung aus Holdoutwerten. Jetzt den registrierten neuen Start im
   unveränderten klassischen1033-Bundle-Piloten geprüft: beide Wiederholungen
   exakt gleich und unabhängig auditiert, grober Flux8,95e-8. Jetzt unverändert
   alle vier feinen Abnahmephasen für beide ausgewählten Felder abschließen.
5. Bei Zulässigkeit: Wiederholungen und mehrere Startpunkte, anschließend eine
   starke klassische Vergleichsbaseline unter gleichen Rechenbudgets.

Ausgangspunkt: [direkte Ungleichungen](optimization/DIRECT_INEQUALITY_QUALIFICATION_PROTOCOL.md).
Ein negatives Ergebnis schließt diesen Versuch, nicht automatisch das Arbeitspaket.

## Forschungspakete und Abnahme

QI-Nachschärfung aus dem Gauge-Test: Die ursprünglichen Traces/Ableitungen sind
exakt reproduziert, aber25 nfp3-Familien wechseln bei bloßer Neumarkierung ihre
Vorzeichenklasse. Deshalb den physikalischen Wirkungs-/Präzessionsmaßstab und
seine Gauge-Bedeutung klären; kein naives Optimieren einer frei wählbaren
radialen Vorzeichenstatistik. Der volle Invariantenbereich bleibt offen.
Die [Koordinatenanalyse](qi/QI_DRIFT_COORDINATES.md) erklärt die Transformation
des vollständigen Driftpaares. Nächster Physiktest: absolute Normalisierung und
direkte Führungszentrum-Drift gegen Wirkungsableitung, mit identischer Phase und
geprüften Strom-/Druckannahmen. Reine Algebra ersetzt diese Gegenrechnung nicht.
Der erste separate [Flussnormierungstest](qi/QI_CLEBSCH_RESULTS.md) bestätigt
die Feldorientierung, bleibt aber mit19/24 vollständigen Gitterpässen negativ.
Die getrennte Halbflächen-/Produktzerlegung bestätigt jetzt: radiale Interpolation
allein erklärt die fünf Fehler nicht; zehn von48 Halbflächengittern scheitern
bereits ohne sie. Nächster Teiltest: Spektraltrunkierung und Wout-Ausgabekonventionen
an den unveränderten Daten klären, ohne nachträgliche Grenzlockerung.

| Paket | Noch zu lieferndes Ergebnis | Woran es beurteilt wird |
| --- | --- | --- |
| Reproduzierbarkeit | **Lokal erledigt:** frischer gesperrter Daten-/Solveraufbau und wissenschaftliche Integration; unabhängige Hardware/Hosted-CI bleiben getrennt offen | Alle21 Phasen und sechs Nicht-Skip-Tests bestanden; neue W7-X-Ausgaben, elf archivierte Rohdateien, explizite60/63-Abweichungen |
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
