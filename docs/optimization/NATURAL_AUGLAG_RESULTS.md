# Natürliche Flux-AL — durch Speicherplatzfehler unterbrochener Pilot

Protokoll/Kern 891532b, 2026-09-12. Die reine Residuenidentität besteht sieben
Kontrollen. Drei weitere Steuerungskontrollen bestätigen feste Stufenbudgets,
Cache-Wiederverwendung, fehlende Budgetübertragung bei früher Solverkündigung
und Trennung von Konstruktionsziel und Solverkonvergenz.

Erste analytische Ausführung der echten achtstufigen TRF-Steuerung:
x=(1,0000000046650739; -4,665073789293459e-9), maximale Verletzung
4,665073882748061e-9, Lagrangegradientnorm 2,220446049250313e-16.
Alle vorab festgelegten Kontrollen bestehen; 16 vollständige analytische Bundles
einschließlich eines Originalpunkts, keine Plasmaphysik. Eine zusätzliche
maschinenlesbare Wiederholung des Solverkontrolltests wird vor der Suche erfasst.

Der Adapter verwendet genau den gekoppelten nativen Fluxkovektor und die bereits
qualifizierte batched Jacobimatrix. Jede vollständige physikalische Auswertung
muss weiterhin die ursprünglichen GN-Identitätsgrenzen bestehen. Stufen-Meritwerte,
Multiplikatoren, Auswahl und Zusatzarbeit werden getrennt gespeichert.

Vollsuite: 305 Tests bestanden, 11 bekannte Warnungen. Nach fünf behobenen
Schleifenbindungswarnungen blieb zunächst eine weitere Ruff-Warnung B008 über
`lam.copy()` im Standardargument bestehen. Die frühere Ruff-Erfolgsaussage in
b35efae war verfrüht. Bindung an das nicht mutierte Stufenarray beseitigt sie;
erneut zehn betroffene Tests und jetzt Ruff bestanden. Keine Suchmathematik
oder bestehenden Suchkerne geändert.

Der maschinenlesbare Kontrollbericht `evidence/natural-auglag-control-v1.json`
bei b35efae bestätigt die oben genannten Werte und alle Kontrollgrenzen. Er
enthält nur analytische, keine physikalischen Auswertungen.

Der unabhängige Stufen-/Auswahlprüfer ist vorbereitet. Er berechnet sämtliche
Meritwerte, minimale Stufenauswahl, Multiplikator-/rho-Folge, Bundlepartition,
Zusatzarbeit, Zielstopp und benannte Feldidentität erneut. Acht Stufenkontrollen
und eine explizite Terminationsprofilkontrolle bestehen. Der Standardprüfer für
einzelne Solver behält sein altes Verhalten; die Stufenlogik muss explizit gewählt
und zusätzlich inhaltlich geprüft werden. Vollsuite jetzt 314 bestanden,
11 bekannte Warnungen, Ruff bestanden.

Die physikalische Suche startete bei 80a1d88 nach Abschluss der beiden vorherigen
Studien. Analytische Kontrolle und vollständige Start-Richtungsprüfung bestehen.
Keine Holdout-Zahlen wurden in Einstellungen oder Suchparameter übernommen.

Die erste Wiederholung hat acht Stufen und 1033 Bundles abgeschlossen (1781
Anfragen, 748 Cachetreffer, keine global verweigerte oder fehlerhafte Auswertung).
Auswahl 1029: grober Flux 2,6986169559754677e-7, interne maximale Verletzung
3,72556785421807e-9. Feld und benanntes Array sind gespeichert. 800,296 s sind
keine kontrollierte Vergleichszeit. Allein der interne Geometrieschirm besteht;
der Flux ist rund 27-mal zu groß, feine Abnahme noch offen.

Der gleichzeitig gestartete isolierte Clone füllte die Platte. Die zweite
Wiederholung scheiterte beim Checkpoint: 700 Bundles sind in JSON gesichert,
725 wurden nur auf der Konsole gemeldet. Zweites Bestfeld/Bestarray fehlen.
Die Originalberichte bleiben unverändert, ihre letzten `running`-Flags werden
durch den [gesonderten Fehlerbericht](../validation/RESOURCE_INTERRUPTION.md)
eingeordnet. Keine qualifizierte Zwei-Wiederholungs-Studie und keine Konvergenz.

Der explizite unabhängige Postmortem-Audit besteht: alle28 Einzelarmprüfungen
(Stufen-/Multiplikatorrechnung, Auswahl, Budget, native Zusatzarbeit, Ableitungen,
benannte Feldidentität) und alle700 gespeicherten Präfix-Bundles stimmen exakt.
`evidence/natural-auglag-pilot-v1-postmortem.json` hält zugleich `all_pass=false`
für die unvollständige Studie fest. Der normale Auditor ohne Postmortem-Modus
weist sie erwartungsgemäß ab, ohne einen Abschlussbericht zu erzeugen.
Die gesamte Suite bleibt bei348 bestandenen Tests,20 bekannten Warnungen;
Ruff/Dokument-/Diffprüfung bestehen.

Der [separat festgelegte Wiederholungsversuch](NATURAL_AUGLAG_RECOVERY_RESULTS.md)
ist inzwischen in beiden Armen und beiden historischen Präfixen unabhängig
bestätigt. Seine vollständigen feinen Abnahmen folgen; die Originalstudie bleibt
unvollständig. Weder eine
zulässige Konstruktion noch ein Methoden- oder SoTA-Vorteil ist nachgewiesen.

Der Wiederholungsdriver wartet ausdrücklich auf bestandenen Abschluss der neuen
nativen Integration, startet dann den unveränderten Originalrunner und führt
beide unabhängigen Audits aus. Auch dabei gilt die überwachte 2-GiB-Platzreserve.
Keine automatischen Holdouts vor Auswertung/Dokumentation der Suchergebnisse.
Fehlgeschlagene, alte kopierte oder unvollständige native Voraussetzungen dürfen
keine Suche auslösen; dafür bestehen sieben reine Steuerungskontrollen.
Gesamte Suite366 bestanden,20 bekannte Warnungen; Ruff/Dokument-/Diffprüfung
bestanden. Sieben ursprüngliche Mathematikdateien und drei SciPy-Solverdateien
stimmen weiterhin mit ihren archivierten Hashes überein.

Für den anschließenden Abnahmeschritt ist ein ressourcenüberwachter Driver
vorbereitet: `scripts/run_coil_holdouts.py`. Er verlangt eine abgeschlossene
Zwei-Arm-Studie und den hashgebundenen bestandenen unabhängigen Studienaudit.
Er führt die vier bestehenden Werkzeuge sequenziell aus, ohne deren Mathematik,
Gitter oder Grenzen zu ändern. Ein reguläres physikalisches FAIL (Exit2) bleibt
erfasst und überspringt keine weiteren Prüfungen; Ausführungsfehler, fehlende
Kandidaten oder unvollständige Auflösungsreihen stoppen hingegen den Driver.
Sein Abschlussflag bestätigt nur vier ausgeführte Prüfungen, nicht Zulässigkeit.
13 Steuerungskontrollen bestehen, einschließlich absichtlich falscher Flags und
fehlender Ergebnisse. Die 2-GiB-Reserve gilt auch hier.
