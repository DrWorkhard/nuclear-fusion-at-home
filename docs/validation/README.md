# Validierung, Reproduzierbarkeit und Audits

Zweck: Regeln für belastbare Aussagen, reproduzierbare Umgebung und unabhängige Regressionen festhalten.

Geschärfte Basisabnahme abgeschlossen: Schritt1/2 für den lokalen Referenz-/LPQA-
Filamentpfad bestanden.720 Tests, sechs Pflichtdatenidentitäten ohne Skip, echte
wiederholte Iteration und sämtliche Kandidatenabnahmen. Kein Entwurfs-/SoTA-Pass.

Aktueller Schluss: Der ausgewählte W7-X-Physikvergleich besteht, der erweiterte Dateivergleich bleibt bei 60/63. Kernsoftwaretests ersetzen weder einen vollständigen nativen Neuaufbau noch wissenschaftliche Zulässigkeit. Der Audit vom 9. September korrigiert frühere Bereitschaftsaussagen.

[Projektübersicht](../README.md) · [Aktueller Stand](../STATUS.md) · [Arbeitsplan](../PROJECT_PLAN.md)

## Dokumente

- [Gemeinsamer CLI-Einstieg](PROJECT_ENTRYPOINTS.md) — Profile entdecken, Aufrufe ohne Rechnung planen, feste Feldstartstudie ausführen und gespeicherte Läufe unabhängig auditieren. 64 neue/1904 Gesamttests bestanden; erste Erhaltungsfehler bewahrt, alte CLI unverändert. Daten-Replay folgt separat.

- [Basisabnahme: Ergebnisse und Bedienung](FOUNDATION_ACCEPTANCE_RESULTS.md) — Beide geschärften Schritte bestanden;720 Tests, zwei24-Bundle-Pfade, separate Audits und alle vier Holdouts. Erster Metadatenfehler erhalten, Korrektur/frische Wiederholung dokumentiert, Befehle und Grenzen festgehalten.

- [Basisabnahme: geschärftes Protokoll](FOUNDATION_ACCEPTANCE_PROTOCOL.md) — Vorab registrierte Nutzerkorrektur: begrenzte Rechenbasis und reproduzierbarer24-Bundle-Iterationszyklus; getrennte Kandidatenzulässigkeit, unveränderte Grenzen und Altbestand.

- [netCDF4-Importwarnung](NETCDF_IMPORT_WARNING.md) — Drei Prozessvarianten zeigen NumPys Standardfilter und den weiterhin fehlgeschlagenen strengen nativen Import; keine Umgebungsänderung oder behauptete ABI-Heilung.

- [Evidenzintegrität: Ergebnisse](EVIDENCE_INTEGRITY_RESULTS.md) — Erste Auswahl:5501 Verweise in17 Berichten; ergänzend405 Verweise in21 weiteren abgeschlossenen Berichten, alle hashgleich. Keine rekursive Gesamtaudit-/Physikbehauptung.

- [Frische native Integration: Ergebnis](FRESH_NATIVE_INTEGRATION_RESULTS.md) — Alle21 Aufbau-/Rechenphasen und sechs strikte Tests bestanden; neue W7-X-Ausgaben, erweiterter Vergleich weiter60/63. Lokale Reproduzierbarkeit belegt, globale Physikgates offen.

- [Nativer Retry: Ressourcenprotokoll](FRESH_NATIVE_RETRY_PROTOCOL.md) — Selektiver Checkout, 5-GiB-Startprüfung und überwachte 2-GiB-Reserve; ursprüngliche Physik-/Abnahmekriterien unverändert.

- [Speicherplatzfehler und Wiederherstellung](RESOURCE_INTERRUPTION.md) — Frischer Clone scheitert vor Installation; parallele AL-Wiederholung unterbrochen. Originalberichte bleiben erhalten, gezielte temporäre Bereinigung und Ressourcenprüfung folgen.

- [Frische native Integration: Protokoll](FRESH_NATIVE_INTEGRATION_PROTOCOL.md) — Isolierter gesperrter Neuaufbau mit frisch gebautem VMEC8.52 und neuen W7-X-Ausgaben; kein Eingriff in qualifizierte Umgebung oder Systempakete.

- [Strikte wissenschaftliche Regression](STRICT_SCIENTIFIC_INTEGRATION.md) — Fester Sechs-Test-Pfad ohne fehlende-Daten-Skips oder Umgebungssynchronisierung; keine Verwechslung mit frischem nativen Neuaufbau.

- [AUDIT_2026-09-09 ](AUDIT_2026-09-09.md) — Dokument: Übergreifender Quellcode-/Evidenzaudit; Rücknahme der vollständigen Bereitschaft und geordnete Korrekturen.
- [ENVIRONMENT ](ENVIRONMENT.md) — Dokument: Gepinnte native Umgebung, bekannte Plattformkorrekturen, Thread-Regeln und isolierte Integrationspfade.
- [EVIDENCE_STANDARD ](EVIDENCE_STANDARD.md) — Dokument: Klassen von Aussagen, Mindestprovenienz, unabhängige Gegenprüfung und Umgang mit negativen Befunden.
- [EXPERIMENT_PROTOCOL ](EXPERIMENT_PROTOCOL.md) — Protokoll: Gemeinsame Vergleichsregeln: Problemidentität, Rechenbudgets, Mehrstartigkeit und zulässige Pareto-Sets.
- [W7X_EQUILIBRIUM_PROTOCOL ](W7X_EQUILIBRIUM_PROTOCOL.md) — Protokoll: Versionspassender VMEC-Vergleich, geschützter physikalischer Teilumfang und drei verbleibende Ausgabedifferenzen.

Die [Migrationsbeschreibung](DOCUMENTATION_LAYOUT.md) erklärt die neue Struktur,
Erhalt historischer Hashes und automatische Prüfungen.

Historische Protokolle wurden bei der Ordnerumstellung nicht fachlich verändert.
Darin genannte bloße Dateinamen lassen sich über diese Übersicht bzw. die
[Migrationsliste](../../manifests/documentation-layout-v1.json) auflösen.
