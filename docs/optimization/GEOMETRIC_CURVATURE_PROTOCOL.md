# Krümmung und Konditionierung der sechs eingefrorenen geometrischen Schritte

Vor jeder neuen Feld-/Matrixauswertung registriert, 2026-09-12. F-077 zeigt
sechs falsche endliche lineare Fluxvorhersagen bei bestandenen Ableitungsprüfungen.
Jetzt das vorhandene quadratische Fluxmodell an genau diesen Daten prüfen;
keine neue Formsuche, Radiuswahl oder Grenzlockerung.

## Feste Quellen und physikalische Definition

Die zwei Quellen und alle32 vollständigen Bundles aus
`evidence/geometric-probes-v1.json`, gebunden an dessen abgeschlossenen
unabhängigen Audit und beide vorherigen Modell-/Stromstudien samt Holdouts.
Reihenfolge AL/SLSQP, pro Quelle genau die vorhandenen16 Ereignisse: Quelle,
je vier FD-Probes und ein echter Kontrollschritt für r1e-6/1e-5/1e-4.
Keine neuen Punkte; alle sechs Probes bleiben geometrisch und magnetisch
unqualifizierte Diagnosedaten. Die aktuelle native Studie/Audit muss committed sein.

Unveränderte207 benannte Parameter, vier Grundspulen/16 physikalische Kopien,
Ordnung8, feste Stromsumme1250075,624635464A,32²-Halbperioden-Feldgitter und
200 Spulenpunkte. Exakte physikalische DOF-Abbildung statt Laufzeit-Sortierung.
Alle drei Stromparameter bleiben bei der neuen Feldwiedergabe wie gespeichert.

## Feldwiedergabe und vollständige Matrixqualifikation

Je gespeichertes Ereignis einmal das native kartesische B auf demselben Gitter
berechnen und auf das unveränderte räumliche Residuumz projizieren. Alle32
Roh-Fluxwerte müssen ihre archivierten nativen Werte relativ<=1e-10 reproduzieren.
Keine neue Auswertung der137 Geometriebedingungen; deren vollständige Werte/
Jacobimatrizen sind bereits qualifiziert und werden quellgebunden übernommen.

An beiden Quellen die volle1024x207-MatrixD mit dem unveränderten gebündelten
Filamentkern und separat über1024 native Einzelpunkt-B/VJP-Abfragen bilden.
Matrixvergleich komponentenweise normiert durchmax(1,|Referenz|)<=1e-10;
gebündelte/native Projektion ebenso, Roh-Flux relativ<=1e-10. Für den Vergleich
`D^T*z/1e-6` gegen den gespeicherten nativen Fluxgradienten **dieselbe native
Projektionz** verwenden, normierter Fehler<=1e-10. Die alte ungekuppelte
Projektionsabweichung zusätzlich angeben, nicht als Datenkorrektur verbergen.
Native Beobachtungspunkte müssen nach Einzelpunkt-VJPs exakt wiederhergestellt sein.

Die drei explizit identifizierten Stromspalten müssen die gespeicherte affine
StrommatrixA der ursprünglichen Stromqualifikation normiert<=1e-12 reproduzieren.
Alle sechs vorhandenen geometrischen Richtungen zusätzlich mit den neu gespeicherten
Feldresiduen der ursprünglichen FD-Punkte prüfen: beide eps1e-7 und1e-8,
komponentenweise normierter Fehler<=1e-6. Kein Auswählen der günstigeren Stufe.

## Quadratisches Modell und unveränderte Nützlichkeitsprüfung

Fürs=1e-6 und den tatsächlichen archivierten Parameterschrittd:

    f = ||z||²/(2s),
    q(d) = ||z+D*d||²/(2s),
    H_GN = D^T*D/s,
    e = z(x+d) - z - D*d,
    f(x+d)-q(d) = ((z+D*d)^T*e + ||e||²/2)/s.

Unveränderten bereits analytisch geprüften Modellkern wiederverwenden. Direkte
Norm/Matrixform und explizite Restidentität normiert<=1e-10 prüfen. GN ist eine
positive semidefinite Näherung, nicht die gesamte Hessematrix des nichtlinearen
Flux. Primärreferenz: [SciPy Least-Squares-Dokumentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html),
Abruf2026-09-12,1.18.0; Definition zusätzlich unmittelbar aus der obigen Quadratform.

Nützlichkeit besteht nur, wenn **alle sechs** quadratischen Vorhersagen das
richtige Änderungs-Vorzeichen haben und ihr absoluter Fehler höchstens10% des
jeweiligen linearen Fehlers ist. Implementierungsqualifikation, Modellnützlichkeit
und Entwurfszulässigkeit bleiben drei getrennte Aussagen. Negative Ergebnisse
werden vollständig erhalten; keine vorhergesagte Verbesserung als neuer Entwurf.

## Konditionierung und Stromkopplung: rein lokale Zusatzdiagnose

Je Quelle alle Singulärwerte von `D/sqrt(s)`, seinem204-Spalten-Geometrieblock,
dem Geometrieblock nach Projektion orthogonal zum dreidimensionalen Stromraum
und dem unskalierten StromblockA berichten. Numerischer Rang bei rcond1e-12;
Kondition nur aus nichtverschwindenden Extremwerten, sonst ausdrücklich fehlend.
Kein Entfernen schwacher Formrichtungen und kein bereits konstruierter Präconditioner.

FürA muss Rang3/Kondition<=1e10 gelten. Reduziertes QR liefert die orthonormale
StrombasisQ; Orthogonalitätsfehler<=1e-12. Für jeden der sechs alten Schritte
den Anteil `||Q^T*D*d||²/||D*d||²` und die Norm von
`(I-Q*Q^T)*(z+D*d)` angeben; bei genau verschwindendem Tangentenvektor Anteil
ausdrücklich fehlend. Das ist eine analytische Projektion im **linearisierten**
Feldmodell, keine tatsächlich ausgeführte Stromnachoptimierung der neuen Form.
Der projizierte Geometrieblock ist nicht ohne Weiteres die exakte Ableitung
eines nichtlinear stromeliminierten Residuals. Keine solche Behauptung.

Ein separater Auditor benutzt die native Einzelpunkt-Matrix und eigene Summen
für alle sechs Vorhersagen/Restidentitäten, FD-Prüfungen und Projektionen.
Spektren werden aus der unabhängigen Matrix nachgerechnet; normierte
Singulärwert-Abweichung durchmax(1,größtem Quell-Singulärwert)<=1e-10. Ränge und
kleine Singulärwerte können numerisch empfindlich sein: beide Rechnungen berichten,
keine Rang-/Konditionsübereinstimmung nahe dem Cutoff erfinden oder verlangen.
Keine neuen nativen Rechnungen im Audit; keine zweite vollständige Optimierung.

## Budget, Fehlererhaltung und Entscheidung

Maximal32 native vollständige B-Gitteranfragen plus2048 native Einzelpunkt-B-
und2048 Einzelpunkt-VJP-Anfragen. Zwei gebündelte Matrixassemblierungen mit
32 Spulenkontraktionen,64 Geometrie-Ableitungs- und32 Strom-VJP-Anfragen bei
vollständigem Abschluss. Null neue vollständige138-Zeilen-Bundles, keine LPs,
keine neuen Feld-Holdouts. Je Quelle vier SVDs und ein QR für die Zusatzdiagnose;
sechs analytische Stromraum-Projektionen. Auditorarbeit getrennt bilanzieren.
Anfragen einschließlich Cachelesezugriffen zählen; bei Fehlern gestartete und
vollständig abgeschlossene Arbeit unterscheiden, fertige Felder/Matrizen behalten.

Neue Rohdaten enthalten alle32 Felder/Residuen, die zwei vollständigen Matrizen
beider Rechner, Namen/Abbildung sowie Spektren/Projektionsdaten. Quellen, aktive
numerische Kerne, installierte SIMSOPT-Quellen und Umgebung hashbinden. Analytische
Projektions-/Spektral-/Fehlerkontrollen und synthetischer Gesamtablauf zuerst;
3GiB Start-/2GiB laufende Reserve, keine parallele schwere Studie/Installation.

Bei bestandenem Modelltest einen neuen klassischen krümmungsberücksichtigenden
Suchlauf von der bereits festgelegten besten Form gesondert registrieren; die
alte GN-Suche vom anderen Start bleibt unverändert. Die Spektraldiagnose kann
eine weitere Konditionierungsänderung motivieren, beweist deren Nutzen nicht.
Schritt1/2 bleiben bis zu ihren wirklichen Abnahmen offen.
