# SLSQP-Nachoptimierung mit unabhängig qualifiziertem Startgate

Vor neuem Suchlauf registriert, 2026-09-12. Separater Wiederanlauf nach dem
gescheiterten realen Startup-Differenzentest, keine Umdeklaration seines Berichts.
Die [Startqualifikation](POLISH_START_DERIVATIVE_RESULTS.md) und ihr35-Prüfungen-
Audit sind Voraussetzung. Keine neue Startauswahl aus den Differenzentest-Proben.

## Identische Aufgabe und geänderte Qualifikation

Genau derselbe ursprüngliche AL-Kandidat wie im [Polishing-Protokoll](SLSQP_POLISH_PROTOCOL.md).
Qualifizierter Feldhash65b9b85e942fa3ce54467ad29c319b92f1c2756489df4f668e563aa49d5836eb,
Qualifikationsarray9ee89d4ca82a9d104b8d5bf5e2b814bd12962cdcd1f4bc0385099527879250ad.
Vier Ordnung8-Kurven,16 Kopien,207 DOFs, kanonische Stromsumme, alle bisherigen
138 Werte/137 Ungleichungen und unveränderte Konstruktions-/Abnahmegrenzen.
Explizite Quell-/Ziel-DOF-Permutation und vollständige physische Startidentität.

Die erste gezählte Auswertung jeder Wiederholung muss die komplette gespeicherte
138x207-Qualifikationsmatrix und138 Werte in richtig zugeordneten Spalten
normiert<=1e-12 reproduzieren, Quellparameter exakt. Anfangsarray samt Jacobian
speichern, bevor der Optimierer laufen darf. Keine zusätzliche native Auswertung
für diesen Vergleich. Qualifikation und unabhängigen Audit vollständig hashbinden.

Alle vier ursprünglichen realen FD-Schritte1e-5/1e-6/1e-7/1e-8 erneut berechnen;
insgesamt dieselben neun Startup-Bundles. Seed46 in der **ursprünglichen
Quellbasis** benutzen und Richtung explizit ins Ziel umordnen. Alle neun Punkte
und138 Werte müssen gegen den alten fehlgeschlagenen Startup-Ledger reproduzieren
(physische Quellbasis-Hashes exakt, Werte normiert<=1e-12).
Den originalen all-row-FD-Pass/Fail getrennt berichten, nicht auf bestanden setzen.

Neues Gate: alle18 Nicht-Paar-Zeilen beim ursprünglichen letzten Schritt<=1e-6,
für alle120 Paarzeilen die vorher unabhängig bestandene komplexe/reelle
Startqualifikation plus obiger vollständiger Start-Jacobian-Replay. Nicht die
günstigste reale Schrittweite auswählen oder ein fehlendes natives Ergebnis
durch einen gespeicherten Wert ersetzen. Ableitungen an allen späteren Punkten
unverändert vom nativen Backend. Dies qualifiziert den Start, nicht den gesamten
zukünftigen Suchraum.

## Suchablauf, Kosten und Abnahme

Additiver SLSQP-Arm, alten Arm nicht editieren. Außer expliziter Quellrichtung,
Start-Replay/Speicherung und geändertem Startgate derselbe Suchablauf:
x=x0+0,01y, analytisch, ftol1e-10, maxiter100000, Budget2048 je Wiederholung,
gleicher Cache/Fehlerzähler und Auswahlregel (v<=1e-8 zuerst, dann kleinster Flux).
Zwei frische sequenzielle Wiederholungen, volle Pfade/Zähler/Auswahl exakt gleich.
Reguläre Solver-Rückkehr oder Budgetcap beendet; keine neue Flux-Frühstopregel.
Quellvergleich/Startgate müssen vor erstem SLSQP-Aufruf bestehen.

Getrennte Kostenbilanz: bereits1033 AL-Bundles pro konstruiertem Ausgangspfad,
neun Bundles des gescheiterten Starttests, ein neues natives Qualifikations-Bundle
sowie sieben unabhängige Paarwertrechnungen und deren Auditor. Neue Suche bis
2048 je Arm einschließlich neuer neun Startup-Bundles. Nominaler AL+Suchpfad
bis3081, tatsächliche Diagnose-/Wiederholungs-/Abnahmekosten separat; kein
gleichbudgetierter Methodenvergleich oder Verschweigen gescheiterter Vorarbeit.

Separater Audit prüft vollständigen Quell-/Jacobian-Replay und beide Gateflags,
alle alten neun Bundles, Budget/Arbeit/ausgewählten Zustand und vollständige
Wiederholungsidentität. Alle vier unveränderten feinen Abnahmephasen für beide
Kandidaten folgen erst danach; keine Rückkopplung ihrer Werte in diesen Lauf.
Mindestens2GiB laufend überwachte Reserve, keine parallele schwere Rechnung,
keine Installation. Keine historische SLSQP-Präfixpflicht jenseits des expliziten
Startup-Replays. Selbst ein zulässiger Entwurf ist noch kein fünfstartiger fairer
Methodenvergleich oder vollständiger Schritt2.
