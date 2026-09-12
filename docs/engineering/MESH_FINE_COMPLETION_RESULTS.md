# Feinster Netzfall: vollständiger nichtlokaler Pass und exakter alter Präfix

## Reale Ausführung und unabhängiger Audit abgeschlossen

2026-09-12, neue Ausführung bei c04411d, unverändertes Protokoll seit96988b4.
Der einzelne feinste Fall endet vollständig nach2.222.785 SAT-Paarprüfungen,
unter seiner vorab festgelegten4M-/1200s-Grenze. Etwa300,76s einschließlich
Speicherung,85MiB neue Rohdaten, kein Ressourcenabbruch. Alle geprüften Paare
getrennt, null unaufgelöste Fälle/Innenüberschneidungen/LPs/Rechenfehler.

Die gesamte disjunkte Paarpartition umfasst53.464.336.500 ungeordnete
Möglichkeiten:53.453.208.415 durch Boxabstände ausgeschlossen,11.128.085
Blattkandidaten vollständig bearbeitet. Davon8.905.300 Paare mit gemeinsamen
Vertexindizes ausdrücklich ausgenommen; verbleibende2.222.785 Paare durch
gespeicherte Trennachsen nachgewiesen. Keine ungeprüften Paarbereiche im
festgelegten nichtlokalen Gültigkeitsbereich.

Separater Audit bestätigt die vollständige Partition aus Originalvertices,
jeden Trennnachweis durch unabhängige Projektion und alle Quellen/Flags/Zähler.
Alle alten2.000.000 Witness-Zeilen sind bytegleiches Präfix, ebenso sämtliche
1.336.562 alten Traversierungsereignisse; Indexpermutation, alle Knotenboxen
und Polster stimmen exakt. Im neuen vollständigen Baum1.498.064 Ereignisse,
65.535 Knoten. `all_pass` und `finest_nonlocal_screen_pass` sind beide wahr.

Zusammen mit den fünf alten vollständigen Pässen ist der festgelegte
Nichtüberlappungsschirm jetzt **für alle sechs Netzauflösungen** unabhängig
abgeschlossen. Der alte v2-Bericht bleibt unverändert5/6 vollständig; der neue
Einzelfall ergänzt ihn, statt ihn umzuschreiben. Insgesamt3.581.429 Einzelpaar-
Nachweise in der kombinierten vollständigen Serie; die nochmals berechneten
alten2M-Probes verursachten zusätzliche Arbeit und sind nicht neue unabhängige
Paarinformationen. Kein Geschwindigkeits- oder Methodenvergleich.

Weiterhin ausgenommen: Nachbarpaare mit gemeinsamen Vertices, vollständige
Symmetrie-Baugruppen, reale Wicklungspakete, Material-/Lagerungsannahmen und
physikalisch gültige Mechanik. Es bleiben die vier alten, magnetisch unzulässigen
Grundspulen, nicht die zuletzt optimierten Kandidaten. Keine vollständige G5-
oder Schritt1-Freigabe.

Evidenz: `evidence/mesh-fine-completion-v1/summary.json`, Worker/Log,
`evidence/mesh-fine-completion-v1-audit.json`, beide Schutztreiber und
`artifacts/mesh-fine-completion-v1/`. Vier Präfix-/Quellenkontrollen und45
räumliche/Quelldatenkontrollen bestanden. Nächster registrierter Optimierungsteil:
feste Spulenformen, exakte Stromminimierer und unabhängige Feld-Holdouts.

## Aufbewahrte Vorbereitung

2026-09-12. [Protokoll](MESH_FINE_COMPLETION_PROTOCOL.md) bei96988b4 vorab
registriert, noch keine neue tatsächliche Netzrechnung. Ursprünglicher2M-Cap
und sechs-Netze-Studie unverändert, neuer4M-Lauf benötigt eigene Pfade.

Der neue Treiber bindet das einzige unvollständige Originalnetz, dessen alte
Paarcap-Daten und alle committed QI-/Netzaudits. Separater Worker hat denselben
unveränderten räumlichen Scanner,1200s harten Prozesscap und4M SAT-Obergrenze.
Keine erneute Konstruktion der bereits fünf vollständig geprüften Netze.

Der neue Auditor bestätigt zuerst alle alten komprimierten Witness-Zeilen
bytegenau sowie vollständige Index-/Knotenidentität und Ereignispräfixe. Danach
den bestehenden unabhängigen räumlichen Audit an sämtlichen neuen Original-
Vertex-Nachweisen ausführen. Quellen/Cap/Statusklassifikationen separat gebunden;
ein korrekt negatives oder partielles Ergebnis bleibt physikalisch negativ.

Vier kleine Kontrollen bestehen: exakter Präfix bei tatsächlich überlappenden
Toy-Tetraedern ist **kein** Geometriepass, veränderte/fehlende Witness-Zeile,
andere Boxpolster/zu wenig neue Arbeit und fehlende/umgeleitete Vorgänger werden
abgelehnt. Ein langer Fehlertext wurde vor Ausführung nach Ruff verkürzt;
numerische räumliche Kerne und alte Daten blieben unverändert.

Nächster Schritt: neuer geschützter Scan, vollständiger unabhängiger Audit,
Ergebnis und etwaige verbleibende Abdeckungslücken dokumentieren/committen.
Auch bei Erfolg keine Nachbarpaar-, volle Baugruppen- oder Mechanikfreigabe.
