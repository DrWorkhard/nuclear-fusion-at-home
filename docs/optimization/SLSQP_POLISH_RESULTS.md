# SLSQP-Nachoptimierung: vor Solverstart an der Ableitungsprüfung gestoppt

## Ergebnis und Postmortem, 2026-09-12

Ausführung bei438aef4 nach geschlossener QI-Studie. Die physische Startübernahme
und alle138 gespeicherten Quellwerte stimmen exakt. Dennoch stoppt Arm1 nach
neun Qualifikations-Bundles: der vorgeschriebene reale Differenzentest bei1e-8
verfehlt1e-6. **Null SLSQP-Iterationen, kein zweiter Arm, keine neue qualifizierte
Konstruktion oder feine Abnahme.** Die ursprüngliche AL-Abnahme bleibt unverändert.

| Schrittweite | Größter normierter Ableitungsfehler |
| --- | ---: |
|1e-5|1,1903535e-3|
|1e-6|1,1964563e-5|
|1e-7|6,0270492e-7|
|1e-8|3,4025508e-6|

Bei der verlangten letzten Schrittweite scheitern genau vier Paarabstände:
(0,13), (1,12), (4,9), (5,8). Alle18 Nicht-Paar-Zeilen bleiben unter1e-6,
Maximum2,751679e-7. Die Fehlerfolge passt zu Abschneidefehler bei großen und
Rundungsauslöschung bei kleinen Schritten, beweist diese Ursache aber nicht.
Nicht nachträglich den günstigeren1e-7-Wert als bestandenen alten Test auswählen.

Der separate Postmortem besteht17 Prüfungen: alle neun benannten physischen
Punkte und Hashes,138 erste Werte, vier komplette Differenzenarithmetiken,
Budget/Arbeitszähler und gespeicherte Auswahl. Der reguläre Konstruktionstest
bleibt ausdrücklich in `gradient_screen` und `correct_stop` negativ. Der
gespeicherte beste Punkt ist nur eine Differenzentest-Probe (Bundle5), kein
SLSQP-Entwurf und kein für weitere Optimierung ausgewählter Ersatzstart.
Zusätzliche Physikaufrufe im Postmortem:0; keine Ursachenfreigabe allein daraus.

Evidenz: `evidence/slsqp-polish-v1/`, `evidence/slsqp-polish-v1-driver/`,
kanonischer Postmortem `evidence/slsqp-polish-v1-failure-audit-v2.json`.
Der erste identische Auditbericht bleibt erhalten; sein vor einer reinen
Zeilenumbruch-Korrektur gebundener Quelltext ist bytegleich archiviert und über
`evidence/slsqp-polish-v1-postmortem-source-archive.json` zugeordnet.
Zehn Start-/Postmortem-Tests, Ruff und Dokument-/Diffprüfung bestanden.

Nächster Schritt: separat registrierte komplexe-Schritt-Gegenprüfung aller120
Abstandszeilen genau am unveränderten AL-Start, mit unabhängig rekonstruierten
Fourierkurven und expliziter Quell-DOF-Richtung. Erst nach dieser Qualifikation
über einen neuen, anders benannten zusammengesetzten Prüfpfad entscheiden.
Grenzen, alte Suchkerne und gescheiterte Berichte bleiben unverändert.
Die [separate Ableitungsqualifikation](POLISH_START_DERIVATIVE_RESULTS.md) ist
inzwischen bestanden und unabhängig bestätigt. Sie stützt numerische Auslöschung
als Erklärung, erklärt aber diesen alten Suchversuch nicht nachträglich für bestanden.

## Aufbewahrte Vorbereitung

2026-09-12: [Protokoll](SLSQP_POLISH_PROTOCOL.md) bei c622067 registriert.
Additiver Runner nutzt den unveränderten SLSQP-Arm mit dessen bestehendem
Budgetparameter2048. Keine Änderung alter Optimierungs-/Prüfkerne.

Die neue Startübernahme ordnet Kurven und sämtliche Strombaum-Blätter nach
ihrer physischen Rolle zu und bildet daraus eine explizite bijektive Permutation
benannter DOFs. Quellarray und vollständige serialisierte Kurven-/Stromzustände
müssen übereinstimmen. Die erste ohnehin gezählte Auswertung prüft die138
Quellwerte; ein falscher erster Punkt oder eine Abweichung stoppt vor dem Solver.
Kein zusätzliches verstecktes physikalisches Vorab-Bundle.

Acht neue Tests bestehen: Permutation statt Vektorblindkopie, falsches Quellarray,
geänderte Strombaumstruktur, unvollständige/nichtendliche Startwerte, gezählte
erste Auswertung und unabhängige Ablehnung korrumpierter Werte. Der separate
Auditor prüft alle vier Differenzenschrittweiten gegen die tatsächlich
gespeicherten Plus-/Minus-Bundles, sämtliche Budget-/Auswahl-/Arbeitszähler und
vollständige Wiederholungsidentität. Vorarbeit1033 und neues Limit2048 werden
getrennt und als bis3081 Bundles pro hybriden Konstruktionspfad ausgewiesen.

Noch keine neue Suche: die registrierte QI-Matrix und ihre Auswertung müssen
zuerst vollständig geschlossen, unabhängig auditiert und committed sein.
Anschließend neuer Suchlauf, separater Audit und alle vier feinen Abnahmephasen.
Auch ein positives Einzelresultat wäre noch kein vollständiger Schritt2.
