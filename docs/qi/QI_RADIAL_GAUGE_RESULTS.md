# Radiale Gauge — Vorbereitung und analytische Kontrollen

Protokoll ea567f5 vom 2026-09-12. Noch keine neuen realen Gauge-Traces.

Der geometrische VMEC-Tracer akzeptiert nun einen optionalen endlichen
`alpha_offset`; beim Standardwert null bleibt der bisherige Rechenpfad unverändert.
Die neuen Kontrollen prüfen direkte Torusformeln bei verschobenem Alpha,
2pi-Periodizität mit nichttrivialem Lambda, exakte Standardwertgleichheit und
NaN/Inf-Ablehnung. Die Kettenregel-Kontrolle prüft positive/negative
Gauge-Steigungen, ein alpha-unabhängiges Beispiel und bewusst falsche Ableitungen.

Zehn neue Tests bestehen, Vollsuite **324 bestanden**, Ruff bestanden. Nun 20
NumPy/netCDF4-Abkündigungswarnungen statt11: zusätzliche synthetische Wout-
Fixtures lösen dieselbe vorhandene Warnungsart aus; keine neue Warnungsart.

Der Cambridge-HTML-Aufruf des Goodman-Papiers scheiterte beim Abruf; die
[Verlags-PDF](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/6601E449C8DD3B3FEB361DA2C5732EFC/S002237782300065Xa.pdf/constructing_precisely_quasiisodynamic_magnetic_fields.pdf)
war erreichbar und bestätigt Wirkung/Omnigenität in Abschnitt1.2 und die
Maximum-J-Definition in1.3. Die Gauge-Kettenregel wird als eigene elementare
Herleitung behandelt, nicht als Zitat. Keine Änderungen der alten Pitchwerte,
radialen Stencils oder Fehlerschranken.

Noch offen: Runner mit exaktem c=0-Replay sämtlicher alter Tracearrays, neue
Gauge-Traces, Muldenzuordnung, vollständige Stencils und unabhängiger Zahlenreplay.
Globale QI-/Maximum-J-Qualifikation und Schritt1 bleiben offen.
