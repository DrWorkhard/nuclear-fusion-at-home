# GN-Pilot mit nativer Feldprojektion — laufender Zwischenstand

Stand: 2026-09-12. Protokoll/Implementierung 1913edd.
Der Pilot `evidence/gn-trust-native-v1` läuft noch; seine veränderlichen
Zwischenberichte sind noch keine abschließend eingefrorene Evidenz.

Die gemeinsame Vorqualifikation besteht an Original, Punkt 119 und Fehlerpunkt 29:
Werte, Jacobians, H_GN und physikalische Identität stimmen. Maximale normierte
Gradientfehler mit nativer Projektion: 3,883e-14 / 1,493e-14 / 3,603e-13.
Am Fehlerpunkt bleibt die alte ungekuppelte Verletzung 1,638e-10 erhalten.

Ein unabhängiger Nachprüfer ist vorbereitet: ursprünglicher Suchpräfix,
vollständige Wiederholung, Budget-/Cache-/Zusatzarbeit, analytische Startprüfung,
Auswahl und serialisierte Parameter werden erneut geprüft. Akzeptierte Iterierte
müssen zu wirklich ausgewerteten Vektoren passen. Ein Konstruktionsstopp darf
nicht als Konvergenz ausgegeben werden. Sechs adversariale GN-Audit-Kontrollen
und ein zusätzlicher expliziter Budgetkontrollfall bestehen.

Noch offen: Abschluss beider Wiederholungen, unabhängiger Ledger-Audit und alle
feinen Flux-/Geometrie-/nativen Holdouts. Keine zulässige neue Baseline und kein
Abschluss von langfristigem Schritt 1/2 aus diesem Zwischenstand.
