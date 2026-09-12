# GN-Trust-Pilot v1: Schutzprüfung stoppt beim 29. Vorschlag

Datum 2026-09-12, Protokoll/Implementierung e159155. Evidenz:
`evidence/gn-trust-pilot-v1/summary.json` und `gn-trust-1.json` im selben Ordner.

Analytischer Solver-Kontrollfall und vollständige physikalische Zustandsprüfungen
an Original/Punkt 119 bestehen. Die erste Suche beendet sich nach 23,241 Sekunden:
28 vollständige Bundles, ein fehlgeschlagenes Bundle, 51 Cachetreffer,
80 Anfragen, keine Budgetverweigerung. Der zweite Arm wurde nicht gestartet.

Die Feld-/Gradientidentität im zusätzlichen GN-Backend schlägt am 29. Vorschlag
fehl. Sein Parameterhash ist
`fbfa2c2c55998b24f94e2ec0a38b99ff8dcc276306102061719eec854aaa3f59`.
Der größte Gradientfehler der 28 zuvor akzeptierten Bundles war 6,935e-11;
die feste Grenze ist 1e-10. Die numerischen Fehlerwerte und vollständigen Arrays
des fehlgeschlagenen Bundles fehlen: Der ursprüngliche Fehlerpfad speichert
nur seinen Hash. Das ist eine Lücke in der Fehlerdiagnostik, keine Erlaubnis,
die Schutzprüfung zu ignorieren oder die alte Evidenz zu überschreiben.

Das gespeicherte beste Feld (Vorschlag 22) hat Roh-Flux/1e-6=0,590416404 und
besteht den internen Geometrieschirm. Es wurde nicht unabhängig zugelassen und
begründet keinen Fortschritt gegenüber dem vorherigen SLSQP-Kandidaten.

Nächster begrenzter Schritt: deterministischer Wiederholungslauf ausschließlich
zur Erfassung und Gegenprüfung des fehlgeschlagenen Bundles. Grenzwerte,
physikalisches Problem und Solveroptionen bleiben unverändert. Kein weiterer
Optimierungspilot vor der Klärung. Alter Bericht und gespeichertes Feld bleiben
erhalten; langfristige Schritte 1/2 bleiben offen.
