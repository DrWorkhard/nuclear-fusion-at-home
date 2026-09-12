# VMEC-Clebsch-Normierung: 19 von24 Gittern bestehen

2026-09-12: [Protokoll](QI_CLEBSCH_PROTOCOL.md) vorab registriert, reale Auswertung
und separater Audit abgeschlossen. Gepinnter SIMSOPT-Code verwendet ein Minuszeichen zwischen seiner
Clebsch-Flusskonstante und `wout.phi[-1]/(2*pi)`. Dieses Vorzeichen muss gegen
kontravariantes Wout-Feld bestätigt werden, bevor absolute Drift interpretiert wird.
Die unabhängige QI-Koordinatenprüfung ist vom laufenden LPQA-Suchversuch getrennt.

Auswerter und separater Punktarray-Auditor sind vorbereitet. Neun analytische
Torus-/Vorzeichen-/Singularitätskontrollen und eine unabhängige Replaykontrolle
bestehen; zusammen mit bisherigem Tracer17 Tests bestanden (19 bekannte Warnungen).
Der geometrische Jacobian wird ausdrücklich nicht
aus radialen Geometrieableitungen rekonstruiert; dieser anschließende Gate bleibt offen.

## Ergebnis und unabhängige Gegenrechnung

Ausführung bei0dca1ec; alle24 Gitter abgeschlossen. Berichte
`evidence/qi-clebsch-v1.json`, `evidence/qi-clebsch-v1-audit.json`, Wächterbericht
`evidence/qi-clebsch-v1-driver/summary.json`; Punktarrays unter
`artifacts/qi-clebsch-v1/`. Kleinster beobachteter freier Platz6134104064Bytes.
Workerexit2 ist hier die reguläre Abweichungsmeldung, kein abgebrochener Versuch.
Separater Auditor bestätigt alle24 Punktarray-/Gitter-/Fehlerrechnungen exakt;
er bestätigt auch die negative Teilabnahme, ohne neue Feldrechnung.

| Fall | Alle Bedingungen bestanden | Max. poloidaler Fehler | Max. kartesischer Feldfehler |
| --- | --- | --- | --- |
| nfp2 Vakuum | 4/6 | 1,0242432e-3 | 2,4698897e-4 |
| nfp2 beta2 | 6/6 | 8,3502012e-4 | 2,2336314e-4 |
| nfp3 Vakuum | 6/6 | 6,1349189e-4 | 4,3209499e-4 |
| nfp3 beta2 | 3/6 | 1,6005473e-3 | 7,1519903e-4 |

Alle toroidalen Identitäten, kartesischen Feldvektoren und Betragsvergleiche
bestehen1e-3. Die falsche Vorzeichenkontrolle ergibt Fehler nahe2, fehlendes2pi
nahe5,283; beide werden auf allen Gittern deutlich zurückgewiesen. Der gewählte
Minuszweig ist mit diesen Feldrepräsentationen konsistent, keine freie Vorzeichenwahl.

Fünf poloidale Gleichungen überschreiten die feste1e-3-Grenze:
nfp2vac s0,75 bei16/32; nfp3beta2 s0,5 bei16/32 und s0,75 bei32 Punkten.
Die Grenze wird nicht gelockert, **der vollständige Normierungstest bleibt negativ**.
Die Quelle der Restfehler ist noch nicht bestimmt. Eine mögliche Ursache ist,
dass radiale Interpolation von Produkten nicht mit dem Produkt interpolierter
Größen übereinstimmt; das ist derzeit eine Hypothese, keine gemessene Erklärung.

Die anschließende [Produktzerlegung](QI_CLEBSCH_INTERPOLATION_RESULTS.md) ist
abgeschlossen und unabhängig bestätigt: zehn von48 Halbflächengittern scheitern
bereits ohne radiale Interpolation. Diese allein erklärt die fünf Fehler nicht;
Spektraltrunkierung und Ausgabekonventionen bleiben zu untersuchen.
Noch keine absolute Drift, keine neue Bewertung der320 Bouncefamilien und
keine globale QI-/maximum-J-Zertifizierung.
