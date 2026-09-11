# Direkte glatte Ungleichungen: Qualifikation bestanden — 2026-09-11

Protokoll ec3a645, vor dem Physiklauf präzisiert und implementiert in 9c6101c.
Die beiden festgelegten Kontrollfelder bleiben unverändert: ursprünglicher
promovierter Start und gespeicherter räumlicher 128-Vorschläge-Kandidat. Es wurde
nicht optimiert. Evidenz: `evidence/direct-inequality-qualification-v1.json`.

## Messung und Ableitungen

Ein rohes Fluxziel (geteilt durch feste 1e-6) plus 137 Ungleichungen:
eine Gesamtlänge, vier Krümmungsobergrenzen, 120 Spulenpaar-Untergrenzen, vier
Spule/Plasma-Untergrenzen und je vier native MSC-/Bogenlängenvarianz-Bedingungen.
Unnormalisiertes Log-Sum-Exp liefert konservative Schranken der endlichen
Stichproben. Es ist keine kontinuierliche Geometriezertifizierung.

Die Implementierung summiert Ableitungen aller 16 physischen Spulen mit expliziten
vollen/freien Parameterbezeichnungen. Verfeinerte Krümmungskurven teilen exakt die
ursprünglichen Freiheitsgrade. Die Rekonstruktion erzwingt erneut die bekannte
9/10-Namensgrenze; die physikalische Zuordnung und das archivierte Kandidatenfeld
stimmen exakt. Acht Mapping- und sieben analytische Schranken-Kontrollen bestehen.

| Prüfung | Ursprünglicher Start | Räumlicher 128er-Kandidat |
| --- | ---: | ---: |
| Roh-Flux, 32x32 / 200 | 1.099364281e-6 | 4.448827890e-7 |
| Größte normierte Abweichung des nativen Fluxgradienten | 3.0451e-12 | 6.1872e-11 |
| Größter Richtungsfehler, eps=1e-5 | 4.5892e-5 | 2.1410e-5 |
| eps=1e-6 | 4.5411e-7 | 2.1407e-7 |
| eps=1e-7 | 9.1961e-8 | 4.4320e-8 |
| eps=1e-8, vorab geforderter Grenzwert 1e-6 | 3.9761e-7 | 5.7379e-7 |
| Kleinster normierter Ungleichungsspielraum | -0.000454688 | -0.038471960 |

Alle 138 Zeilen bestehen am festgelegten feinsten Differenzenschritt. Die Fehler
steigen gegenüber eps=1e-7 wieder an; alle Schritte bleiben dokumentiert, keine
Toleranz wird nachträglich angepasst. Der native Fluxgradient besteht 1e-10,
hat beim zweiten Feld aber nur rund Faktor 1,6 Abstand zu dieser Prüftoleranz.

Unabhängige Fourier-Rekonstruktion von Positionen, Länge, MSC, Varianz und feiner
Krümmung sowie native Kontrollen aller 120 Abstandsminima bestehen. Die
64x64-Volltorus-Stützstellen sind unter den verwendeten Spulensymmetrien invariant
(maximale Positionsabweichung 1.31e-15 m); das Vier-Spulen-Plasmaminimum stimmt mit
der nativen Prüfung aller 16 Spulen überein. Native Linking Number ist in beiden
Kontrollen null. Diese Stichprobe beweist keine allgemein geschützte Topologie.

## Rechenaufwand und Einschränkungen

18 vollständige Wertaufrufe einschließlich der Differenzen, davon zwei mit
Jacobian; 18 Feldgitter-Anforderungen und zwei direkte Feld-VJPs, 216 native
Metrik- und 24 native Gradienten-Anforderungen. Die Zähler enthalten 86.4 Millionen
Spulenpaar- und 58.9824 Millionen Plasma-Paarstichproben. Das sind logische
Stichproben, keine FLOP-Zähler: quadratische Distanzen werden im Schrankenkernel
und nochmals für das protokollierte rohe Minimum berechnet. Native unabhängige
Prüfaufrufe werden separat ausgewiesen. Laufzeit je Kontrollfeld ungefähr 5,0 / 4,6 s.

Der Fluxgradient wird unmittelbar aus dem Feldintegral abgeleitet. Die native
SquaredFlux-Klasse unterdrückt zusätzlich Gradienten nahe null selbst bei
threshold=0; die Kontrollzustände liegen oberhalb dieser Sonderbehandlung.
Ein entsprechender Untergrenzen-Gradiententest der nativen Klasse ist nicht behauptet.

Beide Kontrollfelder verletzen interne Suchbedingungen, insbesondere die etwas
strengeren Geometriereserven. Das widerspricht weder der Ableitungsqualifikation
noch den früheren, anders abgegrenzten Holdouts. Keine neue Zulässigkeit, keine
SoTA- oder SQuID-C-Bereitschaftsaussage. Nächster Schritt: separat festgelegter
beschränkter SLSQP-Konstruktionsversuch mit unabhängiger Kandidatenprüfung.
