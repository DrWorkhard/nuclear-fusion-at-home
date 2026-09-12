# Natürliche Flux-AL — Vorbereitung, noch kein physikalischer Lauf

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

Noch offen: physikalische Wiederholungen, Anwendung des unabhängigen Audits und
vollständige feine Abnahmen. Weder eine
zulässige Konstruktion noch ein Methoden- oder SoTA-Vorteil ist nachgewiesen.
