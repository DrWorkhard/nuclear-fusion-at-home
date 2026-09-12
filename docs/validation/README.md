# Validierung, Reproduzierbarkeit und Audits

Zweck: Regeln für belastbare Aussagen, reproduzierbare Umgebung und unabhängige Regressionen festhalten.

Aktueller Schluss: Der ausgewählte W7-X-Physikvergleich besteht, der erweiterte Dateivergleich bleibt bei 60/63. Kernsoftwaretests ersetzen weder einen vollständigen nativen Neuaufbau noch wissenschaftliche Zulässigkeit. Der Audit vom 9. September korrigiert frühere Bereitschaftsaussagen.

[Projektübersicht](../README.md) · [Aktueller Stand](../STATUS.md) · [Arbeitsplan](../PROJECT_PLAN.md)

## Dokumente

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
