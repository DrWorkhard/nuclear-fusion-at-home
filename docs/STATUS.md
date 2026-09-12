# Ergebnisstand und wissenschaftliche Bewertung

Stand: 12. September 2026, nach direktem SLSQP-Pilot, unabhängigem Holdout und lokaler Modelldiagnose.
Dieses Dokument enthält die aktuelle Einschätzung; historische optimistischere
Aussagen im Journal werden dadurch nicht wieder gültig.

## Gesamturteil

Die Mess- und Prüfwerkzeuge sind substanziell weiter als zu Projektbeginn.
Der entscheidende Entwurfserfolg steht aus: keine neue zulässige Baseline,
kein belastbarer SoTA- oder Kraftwerksfortschritt. Wir können offene Daten
verarbeiten, aber SQuID-C noch nicht vollständig wissenschaftlich reproduzieren
und Verbesserungen daran zertifizieren.

## Wichtigste Ergebnisse mit Gegenprüfung

| Bereich | Belastbares Ergebnis | Gegenprüfung und verbleibende Grenze |
| --- | --- | --- |
| Optimierungsdarstellung | Rund 2,34–2,35x geringerer Roh-Magnetfeldfehler mit räumlichen Residuen bei je 300 Sekunden | Zwei Wiederholungen je Arm; Zielfunktion/Gradient identisch, unabhängige Prüfung aller vier Felder. Nur ein Startpunkt, alle unzulässig |
| Ableitungsberechnung | Räumliche Jacobimatrix in 0,304–0,337 s statt etwa 1,05 s | Zwei eingefrorene Zustände, drei Wiederholungen; maximale normierte Matrixabweichung 8,882e-16. Kein Entwurfsfortschritt für sich |
| Geometrie | Kontinuierliche Krümmungs- und Spulenabstandsschranken; bestätigte Verletzungen zwischen Stützstellen | Analytische Kontrollen und unabhängige Positionsprüfung. Gleitkommapolster, keine gerichtete Intervallarithmetik; keine vollständige Volumengeometrie |
| W7-X | Ausgewählte physikalische Regression gegen versionspassendes VMEC 8.52 besteht | Erweiterter Vergleich 60/63; drei Ausgabedifferenzen bleiben, Auswahl teilweise retrospektiv |
| QI bei endlichem Druck | 320 zugeordnete Potentialmulden-Familien in vier Fällen; Druckfall nfp2 durchgehend negative radiale Ableitungen im untersuchten Bereich, nfp3 gemischt | Unabhängige Quadratur und zweiter Feldlinienrechner; 319 aufgelöste Vorzeichen bestätigt, eines unaufgelöst. Keine globale maximum-J-Aussage |
| Direkte Randbedingungen | 137 Ungleichungen qualifiziert; SLSQP-Pilot mit zwei exakt gleichen 256-Bundle-Läufen | Ausgewählte Felder bestehen Geometrie und zusätzliche native Metriken; Flux bleibt Faktor 23,3 über Grenze. Nicht konvergiert, nicht zulässig |
| Lokales Fluxmodell | Quadratische Vorhersage an allen vier festen Testschritten richtig im Vorzeichen; Fehler mindestens 99,907% kleiner als linear | Vollständiger nativer Jacobianvergleich und unabhängiger Kern-Audit bestehen. Lokale Diagnose, noch kein neuer Optimierungserfolg |
| Software | 271 Tests bestanden, Ruff bestanden; Dokumentstruktur automatisch geprüft | Separater Kern-Checkout zuletzt: 247 bestanden + ein erwarteter W7-X-Skip; Kern-Replay von zwei reellen und zwölf komplexen Abstandsauswertungen stimmt exakt überein. 11 bekannte NumPy-Warnungen; kein vollständiger nativer Neuaufbau |

Details: [Zeitvergleich](optimization/TIMED_SPATIAL_PILOT_RESULTS.md),
[Ableitungen](optimization/BATCHED_SPATIAL_JACOBIAN_RESULTS.md),
[Geometrie](geometry/README.md), [W7-X](validation/W7X_EQUILIBRIUM_PROTOCOL.md),
[radiale Wirkung](qi/QI_RADIAL_ACTION_RESULTS.md) und
[zweiter Feldlinienrechner](qi/QI_PRESSURE_TRACE_RESULTS.md).

## Warum weiterhin keine zulässige Baseline vorliegt

Die räumlichen Kandidaten erreichen im feineren Holdout einen Roh-Quadratic-Flux
von 4,146e-7 beziehungsweise 4,149e-7. Zulässig wären höchstens 1e-8: Es fehlt
also weiterhin ungefähr ein Faktor 41,5. Ihre geprüften Geometriegrenzen bestehen.
Die skalaren Kandidaten erreichen etwa 9,72–9,75e-7 und unterschreiten zusätzlich
mit Spulenabständen um 1,058 m den Mindestabstand 1,06 m. Alle vier sind abgelehnt.

Die Folgerung ist eng begrenzt: Diese Residuen-Darstellung hilft an diesem
Startpunkt unter diesen Solver-Einstellungen. Sie beweist weder allgemeine
Überlegenheit noch eine bessere Physik–Ingenieur-Paretofront. Eine kleine
Strafzielfunktion setzt harte Beschränkungen nicht zuverlässig durch.

Der nachfolgende [direkte SLSQP-Pilot](optimization/DIRECT_SLSQP_PILOT_RESULTS.md)
erreicht 2,331e-7 im unabhängigen Flux-Holdout, bleibt also Faktor 23,3 über der
Grenze. Geometrie und zusätzliche native Bedingungen bestehen. Der Lauf endet
am Budget; weder Konvergenz noch eine zulässige klassische Baseline sind erreicht.
Wegen geänderter Zielformulierung ist dies kein isolierter Methodenvergleich.

## Offene Arbeit, nach Bedeutung

1. **Zulässige klassische Baseline:** Mit den [qualifizierten direkten Ungleichungen](optimization/DIRECT_INEQUALITY_QUALIFICATION_RESULTS.md)
   die Schutzprüfung des am 29. Vorschlag gestoppten GN-Trust-Piloten untersuchen.
   Das quadratische Feldmodell besteht die Prüfung an vier eingefrorenen Proben,
   nicht automatisch an allen neuen Suchpunkten. Die zuvor fehlgeschlagene Abstand-Ableitungsprüfung ist
   unabhängig untersucht, der historische Fehlerstatus bleibt erhalten.
   Danach einen getrennt festgelegten Folgelauf, mehrere
   Initialisierungen und fairer Methodenvergleich. Nicht nur mehr Rechenzeit auf
   denselben Strafansatz geben.
2. **QI-Maßstab:** vollständiger relevanter Invariantenbereich, Mulden-Identität,
   Topologie, Gleichgewichtsauflösung und Koordinaten-/Gauge-Unabhängigkeit.
3. **Ingenieurphysik:** nichtlokale Selbstüberschneidung und Baugruppenabstände,
   reale Wicklungspakete, Material-/Lagerungsannahmen und gültige Mechanik.
   Die bisherige große Verformung macht absolute lineare Spannungsprognosen ungültig.
4. **Reproduzierbarkeit und Zielbaseline:** vollständiger nativer Neuaufbau,
   autorisierte kanonische SQuID-C-Daten und ausführbarer Vergleich mit den
   publizierten Zielgrößen. Fehlende Daten sind nicht das einzige Hindernis.

Die vollständige Prüfliste steht in [SQuID-C-Bereitschaft](squid_c/SQUID_C_READINESS.md).
Ein fachlicher Review sollte insbesondere die Definition der Entwurfszulässigkeit,
die QI-Zielgröße und die Modellannahmen der Ingenieurprüfungen hinterfragen.
