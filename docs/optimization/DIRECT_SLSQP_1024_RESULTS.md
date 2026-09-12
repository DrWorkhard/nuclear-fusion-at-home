# SLSQP-1024 — laufender Zwischenstand, Präfixbedingung verletzt

Suchprotokoll e208ad9, Laufstart 1f4bb0c. Zwei frische Läufe mit festem Budget;
Auswahl, Wiederholung, feine Abnahme und Ursachenklärung sind noch offen.

Im laufenden ersten Arm stimmen die ersten 61 Vorschlagshashes und vollständigen
Wertevektoren exakt mit dem alten 256-Piloten überein. Ab Vorschlag 62 unterscheiden
sich die Parameterhashes; dessen größter absoluter Werteunterschied beträgt
2,842170943040401e-14. Die vorab verlangte **exakte** Präfixreproduktion ist damit
nicht erfüllt; eine kleine Abweichung wird nicht nachträglich zugelassen.

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
