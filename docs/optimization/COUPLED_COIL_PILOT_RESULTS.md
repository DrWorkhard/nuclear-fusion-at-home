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

Nächster Schritt: geprüftes Protokoll committen, additive Implementierung
und synthetische Kontrollen. Numerische Quellen des abgeschlossenen Schritt3
bleiben unverändert; keine Installation oder Änderung externer Repositories.
