# Frische native Umgebung und W7-X-Rechnung

Festgelegt 2026-09-12 vor neuer Installation, Build und Rechnung. Die vorhandene
strikte Sechs-Test-Regression prüft bisher vorhandene Daten. Jetzt wird ein
getrennter Wiederaufbau untersucht, ohne die qualifizierte Root-Umgebung oder
vorhandene externe Checkouts zu verändern.

## Fester Umfang und Eingaben

Neue mit mktemp angelegte Arbeitskopie unter /private/tmp, aus der committeten
Projektversion geklont. Keine vorherige virtuelle Umgebung, keine kopierten
Solverausgaben und kein kopiertes VMEC2000-Binary. Lokale Git-Repositories dienen
nur als lesender Quellcache; frisch ausgecheckte Quellen müssen dieselben
gepinnten Commits besitzen. Der vorhandene, checksumgeprüfte Goodman-Zip dient
als Downloadcache und wird neu extrahiert. Download-/Wheelcaches sind erlaubt
und werden als solche benannt; das ist keine unabhängige Hardwareplattform.

1. Vorher prüfen, dass alle erforderlichen Homebrew-Bibliotheken bereits
   vorhanden sind. **Keine Installation/Änderung von Systempaketen** in diesem
   Versuch. Fehlende Voraussetzungen als Blocker festhalten.
   `FUSION_NO_SYSTEM_INSTALL=1` lässt die Bootstraps ausdrücklich abbrechen,
   statt Systempakete nachzuinstallieren. Homebrew-Autoupdate/API-Abruf abschalten.
2. Native Benchmark-Umgebung mit `bootstrap_macos.sh`: gesperrte Auflösung
   (`uv sync --locked`), SIMSOPT-/StellCoilBench-Pins und Paket-/Kernprüfungen.
   Danach gleiche gesperrte separate VMEC++-Umgebung.
3. STELLOPT v251/VMEC8.52 aus frischem Quellcheckout mit exakt der vorhandenen
   dokumentierten Validierungs-/Plattformkorrektur bauen. Keine neue Korrektur
   dieses Versuchs still hinzufügen. Bestehende Checkouts bleiben unberührt.
4. Goodman-Zip überprüfen/neu extrahieren. Ausschließlich frische VMEC++- und
   VMEC8.52-W7-X-Ausgaben erzeugen, mit unverändertem W7-X-Eingabehash
   `f927a2a4d0adba1dc12406ae9fbf51a82d38cb6f00f0b9cab1ff8908ef35fac8`.
5. Vorhandene strikte Sechs-Test-Regression ausführen. Sie verlangt tatsächliche
   QI-/W7-X-Ausführung, null Skips, exakte Testidentitäten und die unveränderte
   physikalische W7-X-Teilprüfung. Alle drei erweiterten Dateidifferenzen werden
   weiterhin erhalten, nicht in volle63/63-Übereinstimmung umgedeutet.

Für Gleichgewichte gelten die unveränderten Sourcepins, Residualgrenzen und
Vergleiche im [W7-X-Protokoll](W7X_EQUILIBRIUM_PROTOCOL.md). Eine neue Rechnung
ist kein neuer physikalischer Fall. Der frühere Referenzlauf benötigte etwa49min;
die neue Wallzeit wird aufgezeichnet, nicht als Geschwindigkeitsvergleich gewertet.
Schwere Such-/Buildarbeiten nicht als kontrollierte Laufzeitstudie vergleichen.

## Protokollierung und Grenzen

Der Runner `scripts/run_fresh_native_integration.py NEW_REPORT_DIRECTORY`
zeichnet jede Phase vor ihrem Start auf und fixiert auch die Projektkopie auf
die Startrevision. Zwei isolierte Shell-Gegenkontrollen simulieren fehlgeschlagene
Paketabfragen: Beide Bootstraps brechen ab, ohne `brew install` aufzurufen.
Shellsyntax, Python-Syntax und Ruff bestehen; eine überlange Pfadzeile wurde
vor Ausführung aufgeteilt.

Vor jedem Schritt Kommando, Zielarbeitskopie und Quellrevision festhalten;
Ausgaben/Logs, Returncodes, Umgebung, Input-/Binary-/Wout-Hashes erfassen. Jeder
gescheiterte Installations-/Build-/Prüfschritt bleibt sichtbar. Keine alten
Wouts als Ersatz unterschieben. Neue bedeutende Abweichung benötigt eine eigene
Diagnose, nicht angepasste Toleranzen. Outputs niemals überschreiben.

Ein erfolgreicher Lauf qualifiziert diesen frischen Installations-/Daten-/W7-X-
Pfad auf demselben Rechner. Nicht automatisch frischer SIMSOPT-C++-Quellbuild
(ein gesperrtes Wheel darf aus Cache stammen), Hosted-CI, vollständige native
Spulenoptimierung aus leerem Speicher oder vollständige globale QI-/Ingenieur-
Validierung. G1-/Schritt1-Abschluss wird nur im tatsächlich abgedeckten Umfang
beurteilt; übrige Forschungslücken bleiben offen.
