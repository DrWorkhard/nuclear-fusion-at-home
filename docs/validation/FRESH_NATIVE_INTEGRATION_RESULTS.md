# Frischer nativer Aufbau: lokale wissenschaftliche Integration bestanden

Laufrevision b32bc88, 12. September 2026. Der
[ressourcenbegrenzte Retry](FRESH_NATIVE_RETRY_PROTOCOL.md) ist abgeschlossen:
alle21 Phasen bestehen, einschließlich neu gebautem VMEC8.52, zwei frisch
berechneten W7-X-Ausgaben und strikter Sechs-Test-Integration ohne Skip.
Der [erste Speicherplatzfehlschlag](RESOURCE_INTERRUPTION.md) bleibt erhalten.

## Tatsächlich ausgeführt

- Neue abgetrennte Projektkopie am festen Commit; keine bestehende virtuelle
  Umgebung, kein altes VMEC8.52-Binary und kein altes Wout als Recheneingabe.
- Gesperrte native und VMEC++-Paketinstallation aus erlaubten Quell-/Wheelcaches.
  Keine Systeminstallation. Gepinnte Quellen frisch ausgecheckt; StellCoilBench
  ohne das umfangreiche Ergebnisarchiv. Goodman-Zip geprüft und neu extrahiert.
- VMEC8.52 frisch aus gepinntem STELLOPT mit unverändertem Validierungs-/macOS-Patch
  gebaut. Frische VMEC++- und VMEC8.52-Rechnungen für den unveränderten W7-X-Input.
- Strikte sechs Testidentitäten, null Auslassungen, Fehler oder Fehlschläge.
  Der W7-X-Test verlangt ausdrücklich **60/63** im erweiterten Vergleich mit
  genau `pres`, `presf`, `chipf` als verbleibenden Abweichungen. Die korrigierte
  physikalische Teilprüfung und verfeinerte Realraumprüfung bestehen.

VMEC8.52: `ns=201`, `mpol=ntor=10`, 3708 letzte Iterationen,
`fsqr=9,999927325032304e-13`, `fsqz=1,8494510116665705e-13`,
`fsql=2,3245726620722707e-15`; normale Terminierung.
Beobachtete reine Phasenzeiten: Build135,56s, VMEC++268,67s,
VMEC8.52496,44s. Kein kontrollierter Geschwindigkeitsvergleich; die frühere
Referenzzeit von rund49min wird nicht als unveränderte Laufzeit behauptet.
Kleinster abgetasteter freier Platz:6.381.441.024 Bytes, oberhalb der2-GiB-Reserve.

## Evidenz und Archiv

`evidence/fresh-native-integration-v2/`: alle Phasenlogs, Projekt-/Quellpins,
Kommandos, Paket-/Buildprovenienz, Binary-/Input-/Wout-Hashes und strikter
JUnit-Bericht. Der innere generische Testlauf bezeichnet sich allein als
Datenregression; erst der äußere Neuaufbau belegt die frische Herkunft.

Der alte Referenzrunner schreibt in der isolierten Kopie seinen fest benannten
Bericht `evidence/w7x-vmec2000-v852-reference.json` neu. Deshalb ist deren
Worktree am Ende erwartbar schmutzig (dieser Bericht und neue Integrationslogs).
Die gleichnamige historische Root-Evidenz wurde **nicht** überschrieben.

Die frischen Binär-/Eingabe-/Solverausgaben werden nach Abschluss bytegleich
unter `artifacts/fresh-native-integration-v2/` archiviert und mit den ursprünglichen
temporären Pfaden verbunden; Berichte werden nicht nachträglich umgeschrieben.
Elf Dateien sind verifiziert archiviert, einschließlich beider Wouts, Binary,
Eingabe, Referenzbericht und Hilfsausgaben:
`evidence/fresh-native-integration-v2-archive.json`. Alle Phasen-/Quell-/Loghashes,
erneute JUnit-Prüfung und native Hilfsausgabehashes bestehen. Die neue Testkopie
bleibt zusätzlich erhalten; Root-Umgebung und historische Ausgaben unverändert.

Ein erneuter separater Dateivergleich an den Archivkopien bestätigt60/63
(erwarteter Exit1), der anschließende Physikaudit besteht (Exit0), einschließlich
beider Realraumgitter und1e-12-Residualgrenzen. Berichte:
`evidence/fresh-native-integration-v2-comparison.json` und
`evidence/fresh-native-integration-v2-physics-audit.json`.
Root-Vollsuite366 bestanden,20 bekannte Warnungen; Ruff/Dokument-/Diffprüfung
bestanden. Diese Tests liefen als kurze Prüfungen während des bundlebudgetierten
AL-Retry, ohne Laufzeit-Rangfolge.

## Reichweite des Erfolgs

Der lokale frische Installations-/Daten-/W7-X-Integrationspfad ist nun belegt.
G1s entsprechender Teilpunkt ist erfüllt. Keine andere Hardware, keine Hosted-CI,
kein frischer SIMSOPT-C++-Build (erlaubtes Cache-Wheel), keine vollständige
native Spulenoptimierung aus leerem Speicher und kein globales QI-/Ingenieur-
Zertifikat. **Langfristschritt1 bleibt wegen der übrigen physikalischen Gates
offen; Schritt2 benötigt weiterhin eine zulässige Spulenbaseline.**
