# GN-Pilot mit konsistenter nativer Feldprojektion — 2026-09-12

Nach isolierter Diagnose, vor korrigierter physikalischer Qualifikation/Suche.
Der alte Pilot und seine ungekuppelte Identitätsverletzung bleiben erhalten.

Die Korrektur betrifft ausschließlich den Feldkovektor in der Identitätsprüfung:
Für D.T*z/1e-6 dieselbe native Projektion z wie im direkten Feldwert/Gradienten
verwenden. z_batch bleibt eine getrennte Feldgegenprüfung (relative Fluxabweichung
und normierte Projektionsabweichung <=1e-10). Die normierte Gradientgrenze bleibt
1e-10. Den alten ungekuppelten Gradientfehler zusätzlich speichern, nicht verbergen.
Direkte Werte/Gradienten, D, H_GN und Solveroptionen bleiben unverändert.

Vor der Suche Original, Punkt 119 und Fehlerpunkt 29 gegen die jeweils gehashten
Arrays qualifizieren: explizite physikalische Namensabbildung, Werte/Jacobians und
H_GN normiert <=1e-10. Am Fehlerpunkt muss die alte ungekuppelte Prüfung weiterhin
fehlschlagen und die neue konsistente Prüfung bestehen. Der Kernkontrollfall
erzwingt Projektionsrundungsverstärkung bei unverändertem Ziel/Gradienten/H_GN.

Danach ein **neuer** benannter Pilot mit denselben zwei Originalstart-Wiederholungen,
1024-Bundle-Grenzen, neun Start-Prüfbundles, Solveroptionen und Abbruch-/Auswahlregeln
aus [dem ursprünglichen Protokoll](GN_TRUST_PILOT_PROTOCOL.md). Die ersten 28
vollständigen Vektoren/Hashes und der 29. Parameterhash müssen dem gescheiterten
Pilot exakt entsprechen. Kein versteckter Neustart von einem günstigeren Punkt.
Beide vollständigen neuen Historien/Zähler müssen exakt wiederholbar sein.

Eine zusätzliche native B-Anfrage je kompletter GN-Auswertung wird separat
gezählt (typischerweise Cachezugriff, trotzdem eine Anfrage). Keine Zeitgleichheit
gegen SLSQP behaupten. Unveränderte feine Flux-/Geometrie-/native Holdouts für
beide ausgewählten Felder, ohne Rückmeldung in die Auswahl.

Bestandene Punktqualifikation erlaubt diesen begrenzten Pilot, nicht weitere
unbeschränkte Suche oder die Abnahme von Schritt 1/2. Alte Evidenzdateien bleiben
unverändert. Bei einer weiteren Schutzverletzung stoppen und separat untersuchen.
