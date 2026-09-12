# SLSQP-1024 — Suche abgeschlossen, historische Präfixbedingung verletzt

Suchprotokoll e208ad9, Laufstart 1f4bb0c. Zwei frische Läufe mit festem Budget
sind abgeschlossen. Auswahl-/Zählprüfungen und interne Wiederholung bestehen;
der historische Präfixvergleich scheitert. Feine Abnahme/Ursachenklärung offen.

In beiden neuen Armen stimmen die ersten 61 Vorschlagshashes und vollständigen
Wertevektoren exakt mit dem alten 256-Piloten überein. Ab Vorschlag 62 unterscheiden
sich die Parameterhashes; dessen größter absoluter Werteunterschied beträgt
2,842170943040401e-14. Die vorab verlangte **exakte** Präfixreproduktion ist damit
nicht erfüllt; eine kleine Abweichung wird nicht nachträglich zugelassen.
Bis Vorschlag 256 unterscheiden sich 195 der 256 Vorschläge. Der maximale
absolute Unterschied der 138 Werte erreicht 0,8162242024, die maximale normierte
Abweichung 0,07436129006. Die anfängliche Abweichung bleibt also nicht klein.
Ohne vollständige historische Punkt-Jacobians ist ihre Ursache noch nicht
lokalisiert. Der Codevergleich allein schließt zustands-/numerikbedingte
Unterschiede nicht aus. Kein unveränderter historischer Suchpräfix nachgewiesen.

## Neue Suche und unabhängiger Audit

Beide neuen 1024-Bundle-Läufe stimmen untereinander exakt in vollständigen
Vorschlagshashes, Werten, Zählern, Arbeit und Auswahl überein: je 3007 Anfragen,
1982 Cachetreffer, eine Budgetverweigerung, null Fehler. Wallzeiten 468,667 und
554,710 s; leichte Entwicklungsprüfungen liefen gleichzeitig, kein kontrollierter
Wallzeitvergleich. Ausgewählt ist Vorschlag 921 mit Roh-Flux
**1,2664815589163422e-7** und interner Verletzung **8,929310818528435e-7**.
Damit kein interner Zulässigkeitsschirm, keine Flux-Abnahme, keine Konvergenz.
Das Feld hat SHA `18a8587012e655146c57347529075379f0e0d44350dad75761994caf509edb0c`.

`evidence/direct-slsqp-1024-v1-audit.json`: beide Armprüfungen und neue Wiederholung
bestehen; **all_pass=false** wegen beider historischer Präfixprüfungen. Das engere
`qualification_pass=true` der Suchzusammenfassung prüft nur die beiden neuen
Wiederholungen und darf nicht als Bestehen des gesamten Protokolls gelesen werden.
Die unveränderten unabhängigen Holdouts folgen als Kandidatendiagnostik; sie
können den fehlgeschlagenen historischen Vergleich nicht nachträglich heilen.

## Unabhängiger Nachprüfer

`scripts/audit_direct_slsqp_pilot.py STUDY OUTPUT --budget-1024` prüft das
vorab festgelegte 1024-Limit, sämtliche Werte-/Zähl-/Auswahlregeln, benannte
Parameteridentität, Ableitungsschirm und beide historischen 256-Präfixe. Die
historische Standardbetriebsart behält ihr Limit 256. Der Präfixprüfer meldet
erste Abweichung und deren Größe, akzeptiert aber auch eine einzige ULP nicht
als bitgenaue Übereinstimmung. Sieben analytische/adversariale Kontrollen bestehen.
Diese Prüferimplementierung verändert keine laufende Suchroutine.

Der reine Prüfernachtrag war kurz in 577016e an das Protokoll angehängt. Er steht
jetzt getrennt hier, damit die beim Laufstart gebundene Protokolldatei unverändert
bleibt. Keine Auswertungs-, Budget-, Such- oder Annahmekriterien geändert.
