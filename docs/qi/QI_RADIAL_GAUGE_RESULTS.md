# Radiale Gauge — unabhängig bestätigte Vorzeichenabhängigkeit bei nfp3

Protokoll ea567f5, Tracer80a1d88, Runner/Ausführung121f9ab, 2026-09-12.
Alle vier festen Fälle sind ausgewertet und unabhängig arithmetisch auditiert.

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

Der Runner ist vorbereitet und syntaktisch/Ruff-geprüft: alle 21 c=0-Traces je
Fall werden frisch berechnet und gegen jedes gespeicherte Array exakt geprüft,
bevor verschobene Traces entstehen. Drei identische s0-Traces werden je Fall
zwischen Gauges geteilt; 61 tatsächlich neue Traces je Fall inklusive vier
Alpha-Differenzproben. Alle Muldenlisten, Zuordnungen, Stencils und Fehler
werden gespeichert. Die alten fünf Bstar-Werte bleiben unverändert.

## Gemessene Ergebnisse

Alle **84** alten c=0-Traces stimmen in jedem gespeicherten Array exakt überein;
auch sämtliche alten radialen Stencils und Vorzeichenklassen werden exakt
reproduziert. Alle160 Pitch-/Alpha-Zellen sind eindeutig zugeordnet, insgesamt
320 Muldenfamilien mit je drei Gauge-Steigungen. 244 tatsächlich neue Traces,
die s0-Traces werden geteilt. Alle Kettenregel-, Alpha- und Radialverfeinerungen
bestehen. Maximale normierte Kettenregelabweichung **1,6624e-4** (kleinster
zulässiger Schirm0,01), größte Alpha-Verfeinerungsänderung8,8051e-5.

Vorzeichenanzahl pro80 Familien; Reihenfolge **positiv / negativ / unaufgelöst**:

| Unverändertes Gleichgewicht | c=-1 | c=0, alter Maßstab | c=+1 | Familien mit Vorzeichenwechsel |
| --- | --- | --- | --- | ---: |
| nfp2 Vakuum | 80 / 0 / 0 | 80 / 0 / 0 | 80 / 0 / 0 | 0 |
| nfp2 beta2 | 0 / 80 / 0 | 0 / 80 / 0 | 0 / 80 / 0 | 0 |
| nfp3 Vakuum | 66 / 14 / 0 | 64 / 15 / 1 | 67 / 13 / 0 | 5 |
| nfp3 beta2 | 37 / 43 / 0 | 38 / 42 / 0 | 29 / 51 / 0 | 20 |

Bei25 Familien enthalten die drei Gauges sowohl positive als auch negative
Klassen. Das ist **keine physikalische Änderung des Magnetfelds**: dieselbe
radiale Feldlinien-Neumarkierung addiert nach bestätigter Kettenregel
c*partial_alpha A zum gemessenen partial_s A. Die Gauge-Steigungen sind nur
-1/0/+1 rad pro normiertem Radius; keine Aussage für beliebige Neumarkierungen.

Der unabhängige Prüfer importiert weder den Mess- noch den Kettenregel-/Vorzeichen-
Kernel. Er prüft Hashes, exakte c=0-Arrays, alle geometrischen Zuordnungskanten,
die Bindung der Stencils an gespeicherte Muldenaktionen, alle Differenzen,
Schranken, Vorzeichen und Zusammenfassungen. **Alle vier Audits bestehen.**
Zwölf positive/adversariale Kontrollen prüfen manipulierte Ableitungen, Alpha-
Aktionen, Vorzeichen, Intervalle, Zuordnungen und doppelte Zeilen.

Evidenz: `evidence/qi-radial-gauge-v1/` und
`evidence/qi-radial-gauge-v1-audit.json`; Rohdaten unter
`artifacts/qi-radial-gauge-v1/`. Fallzeiten20,29/20,79/27,82/29,03s wurden während
einer bundlebudgetierten Spulensuche gemessen und sind kein Laufzeitvergleich.

## Wissenschaftliche Konsequenz

Die alte feste-Gauge-Aussage bleibt exakt reproduziert, ist aber bei nfp3
nachweislich keine gauge-unabhängige Teilcheneinschlussaussage. Bei nfp2 beta2
bleiben alle80 gemessenen Familien in **diesem begrenzten Test** negativ. Das ist
zusätzliche Robustheitsevidenz, kein globales Maximum-J-Zertifikat.

Vor einem Optimierungsziel sind noch der vollständige Invarianten-/Topologiebereich,
Gleichgewichtskonvergenz und eine physikalisch angemessene Festlegung von
Wirkung/Präzessionsmaßstab nötig. Eine beliebige Gauge darf keine bessere Physik
vortäuschen. Globale QI-/Maximum-J-Qualifikation und Schritt1 bleiben offen.
