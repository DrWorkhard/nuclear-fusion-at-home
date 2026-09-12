# GN-Pilot mit nativer Feldprojektion — unabhängig geprüft, Flux abgelehnt

Stand: 2026-09-12. Protokoll/Implementierung 1913edd.
Beide Läufe in `evidence/gn-trust-native-v1` sind abgeschlossen und eingefroren.
Der unabhängige Audit `evidence/gn-trust-native-v1-audit.json` besteht.

Die gemeinsame Vorqualifikation besteht an Original, Punkt 119 und Fehlerpunkt 29:
Werte, Jacobians, H_GN und physikalische Identität stimmen. Maximale normierte
Gradientfehler mit nativer Projektion: 3,883e-14 / 1,493e-14 / 3,603e-13.
Am Fehlerpunkt bleibt die alte ungekuppelte Verletzung 1,638e-10 erhalten.

Der unabhängige Nachprüfer bestätigt: ursprünglicher Suchpräfix,
vollständige Wiederholung, Budget-/Cache-/Zusatzarbeit, analytische Startprüfung,
Auswahl und serialisierte Parameter werden erneut geprüft. Akzeptierte Iterierte
müssen zu wirklich ausgewerteten Vektoren passen. Ein Konstruktionsstopp darf
nicht als Konvergenz ausgegeben werden. Sechs adversariale GN-Audit-Kontrollen
und ein zusätzlicher expliziter Budgetkontrollfall bestehen.

Beide Wiederholungen sind in sämtlichen Vorschlagshashes, Werten, Zählern,
Arbeitsmengen und der Auswahl exakt identisch. Je 1024 vollständige Bundles,
3585 Anforderungen, 2560 Cachetreffer, eine verweigerte weitere Auswertung und
keine fehlgeschlagene Auswertung. Zusätzlich je 1024 räumliche GN-Matrizen,
16384 Spulenkontraktionen, 32768 geometrische Ableitungsanforderungen,
16384 Strom-VJPs und 1024 native Projektionsabfragen. Wallzeiten 780,926 und
792,856 s; leichte Kernprüfungen liefen zeitweise gleichzeitig, daher kein
kontrollierter Wallzeitvergleich.

Ausgewählter Vorschlag 1020: Roh-Flux **2,4713685440167177e-7**, keine interne
Ungleichungsverletzung, Feld-SHA `e429e3bf425d290810a3eaff7c267e5bc2e9c019db06be61ddd989d3c8159507`.
`construction_screen_pass` betrifft nur die 137 internen Ungleichungen, nicht
die zusätzliche Flux-Abnahme. Bereits grob liegt der Flux Faktor **24,714** über
1e-8. Budgetende, keine Konvergenz; zuletzt protokollierte Optimalität 0,01171.
Maximale gekoppelte Gradientabweichung 5,811e-13 (Grenze 1e-10); die erhaltene
ungekoppelte Diagnose erreicht 4,031e-10. Der exakt erhaltene alte Präfix stützt,
dass die Korrektur die Schutzprüfung, nicht die Suchmathematik verändert hat.

## Unabhängige Abnahme beider Felder

Die beiden Felder ergeben exakt gleiche Abnahmewerte. Alle vier Fluxgitter,
Geometriestufen 200/1000/5000/20000, Plasmaauflösungen 64/128/256/512 und sämtliche
Stufen der kontinuierlichen Schranken bleiben erhalten. Keine Holdout-Rückmeldung.

| Größe | Feinster Wert / Schranke | Grenze | Urteil |
| --- | ---: | ---: | --- |
| Roh-Flux, 128x128 / 800 Spulenpunkte | 2,4713046015452125e-7 | <=1e-8 | **Abgelehnt**, Faktor 24,713 |
| Gesamtlänge | 219,821748818 m | <=220 m | Bestanden |
| Kontinuierliche Krümmungsobergrenze | 0,764994807 /m | <=1 /m | Bestanden |
| Kontinuierliche Spulenabstandsuntergrenze | 1,122587112 m | >=1,06 m | Bestanden |
| Feinster Spule/Plasma-Stichprobenabstand | 3,085070251 m | >=1,3 m | Bestanden |
| Höchste native MSC | 6,618675179 | <=10,100286075 | Bestanden |
| Höchste native Bogenlängenvarianz | 3,099528483 | <=102,015778794 | Bestanden |

Fluxverfeinerung und native MSC-/Varianzverfeinerung bestehen; Linking ist bei
200 und 800 Punkten null. Krümmung N=200 bleibt unaufgelöst, ab N=400 bestehen
alle feineren Schranken. Gleitkommapolster, keine gerichtete Intervallarithmetik.
Keine vollständige Wicklungspaket-, Mechanik- oder Teilchentransportabnahme.

Evidenz: `evidence/gn-trust-native-v1-{holdout,curvature,clearance,native}.json`.
Der begrenzte Versuch einschließlich Kandidatenprüfung ist abgeschlossen und
negativ hinsichtlich Flux-Zulässigkeit. Keine neue Baseline und kein Abschluss
von langfristigem Schritt 1/2. Der separat festgelegte SLSQP-1024-Lauf und ein
natürlicher Flux-AL-Folgeansatz bleiben getrennte Konstruktionen.
