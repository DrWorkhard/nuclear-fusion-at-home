# SLSQP-Nachoptimierung: Vorbereitung

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
