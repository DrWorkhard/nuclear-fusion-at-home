# Feldstärke als mögliche Scheinerklärung prüfen

Retrospektiver Audit vorhandener Holdouts, 2026-09-12. Keine neue Optimierung,
keine neuen Magnetfeldauswertungen, keine nachträgliche Abnahmegrenze.

Der verwendete rohe Flux skaliert bei bloßer Multiplikation des Magnetfeldes mit
einem Faktor `a` quadratisch mit `a`. Deshalb soll eine kleinere Zahl nicht
unbesehen als bessere relative Feldqualität gelten. Der Audit liest die bereits
gespeicherten feinsten 128x128-/800-Punkt-Holdouts sämtlicher zehn Kandidaten aus
dem Zeitpilot, SLSQP-256, GN-1024 und SLSQP-1024. Er prüft Feldhashes und dieselbe
Quadratur, liest die tatsächlichen Spulenströme und stellt zusätzlich
`Phi/<|B|>²` gegenüber. Diese globale Skalenkontrolle ist nicht die native lokal
normalisierte Fluxdefinition und ersetzt keinen unveränderten Grenzwert.

Die gepinnte StellCoilBench-Funktion `_make_base_currents` fixiert **die Summe der
vier Basisströme**, nicht einen einzelnen physischen Spulenstrom. Die vierte
Stromgröße ist die feste Summe minus den drei freien Größen. Das erklärt die
drei Stromfreiheitsgrade. Ein fester Gesamtstrom allein ist noch kein allgemeiner
Beweis identischer räumlicher Feldstärke für beliebige Geometrien; die tatsächlichen
feinen Feldstärken werden daher zusätzlich berichtet.

## Ergebnis

Alle zehn archivierten Felder haben dieselbe Summe der Basisströme:
**1.250.075,624635464 A**. Ihre feinste mittlere Feldstärke liegt zwischen
**0,9461234066 und 0,9461260731 T**; relative Spannweite **2,8183 ppm**.
Bloß geringere mittlere Feldstärke erklärt den beobachteten Fluxunterschied
zwischen diesen Kandidaten daher nicht.

| Zeitpilot-Wiederholung | Verhältnis roher Flux, skalar/räumlich | Nach globaler Feldstärkennormalisierung |
| --- | ---: | ---: |
| 1 | 2,3504606544 | 2,3504668303 |
| 2 | 2,3434019446 | 2,3434098531 |

Alle damaligen Abnahmefehler bleiben bestehen. Dies qualifiziert keine beliebige
Geometrie, globale Parameterfamilie oder Kraftwerksfeldstärke und macht aus den
kleineren Fluxwerten keinen zulässigen Entwurf.

Evidenz: `evidence/field-strength-audit-v2.json`. Der erste reine Metadatenlauf
startete trotz einer Ruff-E501-Warnung (zu lange Beschreibungszeile). V1-Bericht
und bytegleicher Runner-Snapshot sind erhalten; nur die Zeichenkettenformatierung
wurde korrigiert. V2 wiederholt sämtliche Zahlen und Eingabeverweise exakt.
Zuordnung/Hashes: `evidence/field-strength-audit-v1-source.json`. Vollsuite366
bestanden/20 bekannte Warnungen; Ruff/Dokument-/Diffprüfung bestanden.
