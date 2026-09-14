# Flussnormierte reale Spulen: Arbeitsstand

14. September 2026. [Protokoll](COUPLED_COIL_PILOT_PROTOCOL.md) ·
[Methodenentscheidung und Reviews](COUPLED_DESIGN_OPTIONS.md).

Noch kein neuer physischer Rechenlauf. Registriert wird eine gepaarte Matrix
aus Referenz/neuer Plasmaform, zwei Spulenklassen und zwei Zielfunktionen.
Erst generische Eingabe-/Spulenabbildung, unabhängige Flussrechnung und vollständige
Ableitung der Flussnormalisierung qualifizieren, dann begrenzt optimieren.

Der physikalische Protokollreview hat vor Ausführung eine wichtige Lücke gefunden:
eine gleiche256-Punkt-Winkelauflösung in Linien- und Flächenfluss könnte einen
gemeinsamen Fehler verbergen. Ergänzt wurden256/512/1024-Winkelprüfungen und ein
über alle Abnahmeauflösungen unveränderlicher physischer Strom. Kein
Nachnormieren am feinen Raster. Der Vektorfehler wird ausdrücklich dimensionslos
mit unverändertem Konstruktionsmaßstab ausgewertet. Grenzen vor neuen Daten festgelegt.

Dieser Pilot prüft Konstruktion und einen Eintrittsschirm für spätere reale
Feldphysik. Er qualifiziert weder tatsächliche QI-Flächen noch Druck, Teilchenbahnen,
endliche Wicklungspakete oder Robustheit; `transfer_pass`/`step4_pass` bleiben false.
Negative Zellen werden einschließlich aller Aufrufe und Auflösungen erhalten.

Methoden-/Codereview präzisierten zusätzlich: keine Qualifikationsprobes in der
Suchauswahl, jeder tatsächliche Suchaufruf zählt ohne Cachegutschrift, ausdrückliche
Rasterpaare, richtige native Strafen und volle physische Abstandsgeometrie.
Fluss integriert analytische Fourier-Tangenten und einen signierten radialen
Flächenfächer; kanonische DOFs und eingefrorene Diagnostik-Nenner sind verbindlich.
Alle Korrekturen erfolgten vor Messung und vor Protokoll-Freeze.

## Additive Implementierung vor realen Daten

Das Protokoll ist bei`f7a7be3` eingefroren. Neue, getrennte Module implementieren
native Konstruktion, unabhängige Fourier-/Biot–Savart-/Geometrieprüfung und
Versuchsverwaltung; eigene Skripte führen Qualifikation/Suche, feinere Diagnostik
und Gesamtaudit aus. Kein alter numerischer Kern wurde dafür verändert.

Die unabhängige Integration prüft beide Spulenklassen und Methoden, verschobene
und vollständige Torusflächen sowie ausdrücklich aktive Längen-, Krümmungs-,
Spulenpaar- und Plasmaabstandsstrafe. Beide Richtungen und Schrittweiten bestehen
an diesen synthetischen Zuständen. Ein anfangs zu schwach verformtes Testfixture
aktivierte die beabsichtigte Krümmungsstrafe nicht; das Fixture wurde korrigiert,
keine Projektgrenze oder reale Messung verändert.

Eine zweite lesende Ablaufprüfung führte vor Daten zu zusätzlicher Absicherung:
exakt gebundene Qualifikationsfreigabe, Elternprozess-/Threadprüfung und eigene
Zeitprüfung unmittelbar vor Versuchsbeginn und Kandidatenspeicherung zusätzlich
zum äußeren600-s-Wächter. Ein verspätetes Bundle behält Rohdaten, wird aber kein
auswählbarer Kandidat. Jeder Versuch und die zusätzliche wertbasierte Feldarbeit
werden gespeichert; der letzte vollständige Checkpoint bleibt bei Abbruch erhalten.

Die inneren Zielfelder werden gegen die bereits angenommenen64²-Feldarchive aus
Schritt3 geprüft, einschließlich radialer Identität, Dimensionen und tatsächlicher
VMEC-Koordinaten. Für feinere Spulengitter bleibt der ursprüngliche ausgewählte
physische Snapshot maßgeblich, nicht eine neu normierte Momentaufnahme.
Nicht beweisbare Geometrieschranken bedeuten ein offenes physisches Gate;
unbekannte Rechenfehler werden nicht als solche umetikettiert.

Die vollständige Regression besteht:959 Tests, darunter193 neue Kontrollen,
null Fehler/Skips,144 bekannte Fixture-Warnungen,67,55s. Ruff und Dokumentstruktur
bestehen. Der Gesamtauditor wurde zusätzlich mit zehn echten nativen Bundles auf
einem synthetischen Torus samt allen neun Flussgittern Ende-zu-Ende geprüft.
JUnit-Rohdatei durch`evidence/coupled-coil-pilot-v1/implementation-regression.json`
gebunden. Das ist Software-/synthetische Qualifikation, noch keine Target-Freigabe.

Nächster Schritt: Code-Freeze, dann alle acht realen
Startqualifikationen mit getrenntem Audit; nur bestandene Zellen dürfen suchen.
Numerische Quellen des abgeschlossenen Schritt3 bleiben unverändert; keine
Installation oder Änderung externer Repositories.
