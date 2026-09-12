# Was der Gauge-Test physikalisch bedeutet

12. September 2026. Keine neue Gleichgewichts- oder Teilchenrechnung.

## Definition aus einer Primärquelle

Rodríguez, Helander und Goodman geben die Drift zwischen aufeinanderfolgenden
Umkehrpunkten in Clebsch-Koordinaten als
`Delta psi = (partial_alpha J)/q`,
`Delta alpha = -(partial_psi J)/q` an (Gleichungen 1.2a,b).
Omnigenität bedeutet verschwindende Alpha-Abhängigkeit der Wirkung. Ihre
Präzessionsfrequenz ist `Delta alpha / Delta t`; die allgemeine Boozer-Formel
enthält auch Strom-/Druckterme. Die vereinfachte Gleichung 2.1 setzt verschwindenden
eingeschlossenen toroidalen Strom voraus. Diese Voraussetzungen dürfen nicht
stillschweigend auf beliebige Wout-Dateien übertragen werden.
[Primärquelle, Abschnitte 1–2 und Anhang A](https://doi.org/10.1017/S0022377824000345).

## Eigene Kettenregelableitung

Unsere reduzierte Wirkung ist `A=J/(m*v)` bei festen Teilcheninvarianten,
`s=psi/psi_a`. Bis auf den gemeinsamen Faktor `m*v/(q*psi_a)` lautet das
koordinatenbezogene Driftpaar daher

`u = (A_alpha, -A_s)`.

Die bisherigen Gauge-Rechnungen verfolgen `alpha=beta+c*(s-s0)`. Damit ist
`A_s|beta=A_s|alpha+c*A_alpha`, während am Anker `A_beta=A_alpha` gilt.
Folglich transformiert sich das Driftpaar als

`u_new = (u_s, u_alpha-c*u_s)`.

Die im [Gauge-Versuch](QI_RADIAL_GAUGE_RESULTS.md) gemessenen Vorzeichenwechsel
sind damit konsistent: Wir verglichen unterschiedliche Winkelkomponenten
desselben Driftpaares. Bei exakter Omnigenität (`A_alpha=0`) entfällt dieser
Unterschied. Bei kleinen, aber endlichen Abweichungen kann die Winkelkomponente
nahe null trotzdem das Vorzeichen wechseln. Ein willkürlich gewähltes großes `c`
ist keine Optimierung der Einschlussphysik.

Für eine **festgehaltene physikalische Phase** mit lokalen Ableitungen `(k_s,k_alpha)`
ist die skalare Phasenänderung proportional zu

`W = k_s*A_alpha-k_alpha*A_s`.

Unter derselben Koordinatentransformation gilt
`k_new=(k_s+c*k_alpha,k_alpha)`; deshalb bleibt `k_new dot u_new = k dot u`.
Nur den Winkelanteil zu transformieren und den radialen Phasenanteil wegzulassen
vergleicht andere physikalische Phasen. Dies ist eine elementare algebraische
Konsistenzbedingung, **kein neuer unabhängiger Plasmaphysiktest**.

## Verbindliche Messregel und nächste Physikprüfung

- `partial_s A` weiterhin nur mit explizit genannter Feldlinienmarkierung,
  Invarianten und geprüfter Muldenfamilie berichten. Keine freie Gaugewahl zur
  Verbesserung eines Zielwerts.
- Bei Interpretation als Drift beide Wirkungskomponenten erhalten. Bei einem
  Wellenteilchen-/Wellenvergleich dieselbe physikalische Phase samt radialer
  Komponente transformieren; die Phase nicht nach dem Ergebnis auswählen.
- Vor absoluten Frequenzen zusätzlich signierte Flussnormierung, kanonische
  Koordinatenzuordnung, Bouncezeit, Ladung/Energie und Strom-/Druckannahmen prüfen.
  Direkte Führungszentrum-Drift und Wirkungsableitung müssen dann unabhängig
  übereinstimmen. Diese Gegenrechnung ist noch offen.
- Für eine globale QI-/maximum-J-Aussage bleiben vollständiger relevanter
  Invariantenbereich, Topologie, Gleichgewichtsauflösung und Omnigenitätsfehler
  gesonderte Gates. Die 25 beobachteten Gauge-Vorzeichenwechsel werden weder
  gelöscht noch zu neuen physikalischen Instabilitäten umgedeutet.

Reine Kontrollen in `tests/test_drift_coordinates.py` prüfen Transformation,
Kontraktion, den omnigenen Grenzfall und den Fehler beim Weglassen des radialen
Anteils. Keine vorgeblichen Frequenzen oder neue Ergebnisse der vier Goodman-Fälle.

Prüfergebnis: alle elf algebraischen Kontrollen bestanden; gesamte Suite359
bestanden,20 bekannte Warnungen. Ruff/Dokument-/Diffprüfung bestehen.
