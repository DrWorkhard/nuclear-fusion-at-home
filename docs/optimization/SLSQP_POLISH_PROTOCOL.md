# Klassische SLSQP-Nachoptimierung des festgelegten AL-Kandidaten

Vor neuer Rechnung registriert, 2026-09-12. Neuer, ausdrücklich hybrider
Konstruktionsversuch; keine nachträgliche Verlängerung des abgeschlossenen
1033-Bundle-AL-Piloten und kein fairer Methodenvergleich mit dessen Budget.

## Start und unveränderte physikalische Aufgabe

Genau der vom Konstruktions-Ledger ausgewählte Arm1 aus
`evidence/upstream-start-study-v1/summary.json`, mit bestandenem unabhängigen
Audit und abgeschlossenen vier Abnahmephasen. Beide AL-Arme stimmen exakt überein;
kein neuer Holdout entscheidet über die Startauswahl. Bereits bekannte negative
Abnahmen sind offen dokumentiert. Es ist eine explorative Folgeentscheidung.
Feld-SHA256 `6ee2a013254b2f30195291dfd4d13c6a166d06d5286cb966db92a2646db2fb5f`,
Array-SHA256 `31dab61fb28d060c9e9f6c21905396cc469dad738c6931928dfe39fa4e250d14`.

Vier Ordnung8-Kurven/16 Kopien, gleiche207 freien Parameter, feste Stromsumme,
Roh-Flux/1e-6 und dieselben137 Ungleichungen. Unveränderte219,9m/0,99m^-1-
Konstruktionsreserven und dieselben feinen Abnahmegrenzen220m/1m^-1/1,06m/1,3m,
Roh-Flux1e-8. Keine Ordnungserhöhung, neue Regularisierung oder Toleranzlockerung.

Vorbereitung wie beim qualifizierten ersten Archivstart; dann genau die benannten
physischen DOFs aus dem gespeicherten AL-Feld übertragen. Quellarray gegen
serialisierte benannte Werte und Zielnamen prüfen; kein lexikographischer oder
unbenannter Vektorkopiervorgang. Startserialisierung gegen alle vier physischen
Kurven-/Strom-/Regularisierungszustände unabhängig prüfen. Die erste gezählte
Wert-/Jacobi-Auswertung muss die gespeicherten138 Quellwerte auf normiert1e-12
reproduzieren, bevor der Solver Vorschläge machen darf.

## Solver, Budget und Auswahl

Unverändertes `run_direct_slsqp_pilot.run_arm` mit explizit2048 Bundles pro Arm,
zwei frische sequenzielle Wiederholungen. Bestehende SLSQP-Optionen:
`x=x0+0.01*y`, `ftol=1e-10`, `maxiter=100000`, analytischer Jacobian.
Die ersten neun Bundles enthalten wiederum alle vier Seed46-Differenzentests;
letzter normierter Fehler<=1e-6. Ein Fehler stoppt die Qualifikation. Keine
Übernahme der alten AL-Multiplikatoren oder des alten Optimiererzustands.

Volles Bundlebudget statt begrenzter128er AL-Innerstufen. Reguläre Solver-
Rückkehr oder2048er Obergrenze beendet einen Arm; ein kleiner Flux allein
stoppt diesen unveränderten SLSQP-Kern nicht vorzeitig. Auswahl wie bisher:
interne Verletzung<=1e-8 zuerst, dann minimaler Flux, andernfalls minimale
Verletzung und dann Flux, jeweils erster Gleichstand. Alle Fehler/Cachetreffer
zählen wie bisher. Quellkonstruktion kostete zuvor1033 Bundles pro Pfad;
hybrider Konstruktionsaufwand deshalb bis3081 pro Pfad, zuzüglich separat
ausgewiesener Qualifikations-/Abnahmearbeit. Wiederholungskosten nicht verbergen.

Keine exakte historische SLSQP-Präfixpflicht bei absichtlich anderem Start;
die zwei neuen vollständigen Pfade, Zähler und ausgewählten physischen Zustände
müssen exakt übereinstimmen. Separater Audit prüft Budget2048, benannte
Quell-/Zielidentität, erste Quellwerte, alle Auswahl-/Arbeitszähler und Ableitungs-
schirme. Danach alle vier unveränderten feinen Abnahmephasen für beide Felder.

Start erst nach Abschluss der laufenden QI-Gleichgewichts-/Auswertungsstudie;
keine parallele schwere Rechnung. Mindestens2GiB laufend überwachter freier
Platz, keine Installation. Kein kontrollierter Wallzeitvergleich.
Ein negatives Ergebnis schließt nur diesen Versuch. Selbst eine zulässige
Einzellösung ersetzt nicht die mindestens fünf Initialisierungen und den
fairen Methodenvergleich, die für den vollständigen Schritt2 offen bleiben.
