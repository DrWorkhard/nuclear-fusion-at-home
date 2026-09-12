# Gemeinsamer Feldlinienwinkel: vollständig geprüft, Parametrisierung nur Teilursache

## Echte60-Zeilen-Studie und unabhängiger Audit abgeschlossen

2026-09-12, Ausführung bei3ca9876 nach vollständigem SLSQP-/Netzabschluss,
Protokoll unverändert seit5b894e5. Alle zwölf historischen und48 frischen
Datei-/Radiuspaare bleiben erhalten. Vor neuer Koordinatenrechnung reproduzieren
sämtliche archivierten128er VMEC-Feldarrays **exakt**. Alle120 neuen64/128-
Gitter sind gespeichert; sämtliche Inversionen bestehen bei maximalem Residuum
9,9997788e-13 und minimalem D=0,6110529564. Gemeinsame Feldpunkte stimmen exakt.

Der getrennte skalare Audit umfasst61.440 Punktinversionen an allen32x32-
Untergittern und1116 Zeilenprüfungen. Maximale absolute Theta-Abweichung
1,153744e-12, skalares Rootresiduum3,297363e-14; maximale normierte Abweichungen
für R/Z<=1,916e-13,|B|<=1,308e-13, transformierte Tangenten<=3,106e-13.
Alle gespeicherten alten/neuen Vergleichszahlen, Zeilen- und Aggregatklassen
sind bestätigt. `all_pass=true` im Audit qualifiziert diese Gegenprüfung,
**nicht** die als falsch bestätigten Gesamt-Fidelitäts-/Verfeinerungsflags.

### Vollständige16-Zellen-Matrix

Maxima über s=0,25/0,5/0,75 am128er Gitter. Tangentenfehler normiert durch den
größten absoluten Referenzkomponentenwert; keine Vektornorm oder mechanische Größe.
`F` verlangt alle neuen Feld-/Volumenkriterien<=1e-3 und iota absolut<=1e-3
an beiden Gittern. `R` verlangt<=1e-5 Änderung der alten **und neuen
Fidelitätsfehler** zwischen64/128, nicht den früheren Clebsch-Verfeinerungsschirm.

| Fall | ns | Winkelauflösung | altes e_theta | neues e_u | neuer Betragsfehler | F | R |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nfp2 Vakuum |201|1|0,00048379|0,00059804|0,000009422|ja|ja|
| nfp2 Vakuum |401|1|0,00047646|0,00029623|0,000006035|ja|ja|
| nfp2 Vakuum |201|2|0,00739168|0,00063014|0,000311593|ja|nein|
| nfp2 Vakuum |401|2|0,00741061|0,00047422|0,000312566|ja|nein|
| nfp2 beta2 |201|1|0,00256102|0,02520163|0,001789601|nein|ja|
| nfp2 beta2 |401|1|0,00260312|0,02526463|0,001790273|nein|ja|
| nfp2 beta2 |201|2|0,00883725|0,02501189|0,002034720|nein|nein|
| nfp2 beta2 |401|2|0,00886029|0,02499310|0,002035724|nein|nein|
| nfp3 Vakuum |201|1|0,00390962|0,00892701|0,000267302|nein|nein|
| nfp3 Vakuum |401|1|0,00165242|0,00369061|0,000123767|nein|ja|
| nfp3 Vakuum |201|2|0,00411662|0,00883096|0,000461056|nein|nein|
| nfp3 Vakuum |401|2|0,00287718|0,00363678|0,000350458|nein|nein|
| nfp3 beta2 |201|1|0,08397835|0,16249784|0,006109305|nein|nein|
| nfp3 beta2 |401|1|0,03404126|0,07373928|0,002957249|nein|nein|
| nfp3 beta2 |201|2|0,08263211|0,15919630|0,005959907|nein|nein|
| nfp3 beta2 |401|2|0,04089195|0,08625659|0,003324516|nein|nein|

Alle16 Koordinatenschirme bestehen, aber nur4/16 neue Fidelitäts- und5/16 neue
Vergleichsfehler-Verfeinerungsschirme. Größte64/128-Differenz der Fidelitätsfehler:
VMEC7,90755e-4, neue Winkel1,83037e-4, beide über1e-5. Alte F-070-Ergebnisse
(2/16 ursprüngliche Fidelität,9/16 Clebsch-Auswertungsverfeinerung) bleiben exakt.

### Wissenschaftliche Folgerung und Grenzen

Bei nfp2 Vakuum/Winkel2 fällt der Tangentenvergleich deutlich besser aus,
z.B. bei401 Radien von0,0074106 auf0,0004742. Das stützt einen wesentlichen
Parametrisierungsbeitrag in **diesen** Fällen. In anderen Fällen steigt der
Tangentenfehler; nfp3 beta2 erreicht im neuen Vergleich bis0,16250. Das ist kein
16%-Fehler eines invarianten Magnetfelds, sondern der hier definierten
Koordinatentangente. iota/Volumen ändern sich nicht; nfp2 beta2 hat weiterhin
iota-Unterschiede um0,0017, die diese Winkeltransformation nicht erklären kann.
Kein vollständig koordinateninvarianter Oberflächenabstand, keine generelle
physikalische Gleichheit und keine absolute Drift-/Maximum-J-Freigabe.

Evidenz: `evidence/qi-pest-fidelity-v1.json`,
`evidence/qi-pest-fidelity-v1-audit.json`, beide Schutztreiber und226MiB
Punktarrays unter `artifacts/qi-pest-fidelity-v1/`. Originale Daten/Protokolle
unverändert. Dieser diagnostische Versuch ist geschlossen. Weitere Gleichgewichts-
Moden-/Produzenten- und Driftprüfungen bleiben nötig; als nächster bereits
registrierter Lauf folgt der separate Abschluss des feinsten Spulennetzes.

## Aufbewahrte Vorbereitung vor echter Ausführung

2026-09-12. Das [Protokoll](QI_PEST_FIDELITY_PROTOCOL.md) wurde bei5b894e5
vorab registriert. Noch keine historische oder neue QI-Datei in diesen neuen
Koordinaten ausgewertet; kein beobachteter Parametrisierungsbeitrag behauptet.

Additiver Vektorkern für u=theta+lambda und die beiden transformierten
kartesischen Tangenten; feste50 Newton-Schritte, maximal0,5rad pro Update,
Residuum1e-12, D>1e-8. Bereits konvergierte Punkte bleiben eingefroren,
unaufgelöste oder singuläre Punkte behalten explizite negative Flags. Keine
Umwicklung auf einen anderen Winkelzweig und keine ergebnisabhängige Phasenwahl.

Der unabhängige skalare Auditor verwendet explizite Fourier-Summen und Brent
auf der vorgeschriebenen Koeffizientenklammer; keine Newton-Aufrufe. Zwölf reine
Kontrollen bestehen: Identität, bekannte Verschiebung/Inverse, Periodizität,
exakte verschachtelte Gitter, beide Tangenten gegen kartesische Differenzen,
singuläre/falsch orientierte Daten, ungültige Moden/Arrays und echter50-Schritte-
Cap mit erhaltenem Fehlschlag. Die letzte Kontrolle lässt den separaten
Brent-Rechner bestehen, ohne den negativen Newton-Status umzudeuten.

Diese Kontrollen qualifizieren Algebra/Fehlerbehandlung, nicht Wout-Lesen,
historische Reproduktion oder QI-Physik. Dateileser, vollständige feste Matrix,
gespeicherte Punktfelder und unabhängige Dateiaudits sind als Nächstes umzusetzen.
Echte Auswertung weiterhin erst nach SLSQP-Abnahme und sechs-Netze-Abschluss.

## Additive Dateileser an analytischen Wout-Kontrollen

Neuer Koeffizientenleser und beliebige VMEC-/gerade-Winkel-Auswertung erhalten
volle/halbe Radialgitter, physikalische m/n-Moden und signierten Fluss. Separater
Auditor liest dieselbe Datei unabhängig, interpoliert Radien mit expliziten
Nachbargewichten, invertiert jeden Winkel skalar und summiert Fouriermoden in
einer anderen Schleifenimplementierung. Alte numerische Reader unverändert.

Sieben zusätzliche reine Toy-Wout-Tests bestehen: drei feste Radien reproduzieren
alte Punktfelder, umparametrisierte Punkte stimmen mit analytischem Torus und
separatem Auditor überein; zusätzliche toroidale Mode prüft Winkelvorzeichen,
veränderlichen Feldbetrag und Halbflächengewichte. Nicht konvergierte Inversion
liefert keine qualifizierten Feldarrays; falsche Symmetrie/nichtendliche Daten
werden abgelehnt. Insgesamt19 neue Koordinaten-/Readerkontrollen bestanden.

Beim ersten Toy-Test war eine willkürliche Mindeständerung von0,01 angesetzt;
die analytisch korrekte Änderung des kleinsten Radius beträgt nur0,009136.
Die Kontrolle verlangt jetzt tatsächliche Ungleichheit und weiterhin die
unveränderten strengen analytischen/skalaren Übereinstimmungen. Keine physikalische
Akzeptanzgrenze geändert. Alle neuen Dateiaufrufe betreffen kleine synthetische
Testdaten, keine historischen/frischen QI-Gleichgewichte. Vollständige Studie und
Datei-/Ergebnisaudit noch umzusetzen, kein neuer QI-Fidelitätsbefund.

## Vollständiger Studien-/Auditpfad an einer synthetischen Matrix geprüft

Der neue Treiber verlangt exakt zwölf historische und48 frische Wout/Radius-
Paare samt abgeschlossenem QI-Originalaudit und committed SLSQP-/Netzvorgängern.
Er reproduziert zuerst alle60 gespeicherten128er VMEC-Feldarrays, einschließlich
der gespeicherten nativen/Clebsch-Vektoren, bevor ein neuer Winkel ausgewertet
wird. Danach sämtliche64/128-Gitter; alte und neue Vergleichsfehler stehen
nebeneinander. Fehlende Koordinatenreferenzen werden negativ statt still entfernt.

Der separate Auditor berechnet die32x32 gemeinsamen Punkte je Datei/Radius mit
eigenen skalaren Roots/Fouriersummen, prüft Quellidentität, gespeicherte Root-/Feld-
Zuordnung, beide Tangenten, verschachtelte Arrays, vollständige Fehlerarithmetik,
alte Fidelitätsklassen und neue Aggregate. Theta-Vergleich ausdrücklich absolut
<=1e-10, andere Feldgrößen normiert; keine Umdefinition der ursprünglichen Studie.
Der alte128er Replayeintrag ist als Ausführungs-Gate protokolliert; die neue
unabhängige Wout-Gegenrechnung betrifft die vorab festgelegten32er Punkte.

Drei zusätzliche Softwarekontrollen bestehen, darunter eine vollständige
synthetische60-Zeilen-Matrix mit120 Gittern und61.440 unabhängigen skalaren
Punktinversionen. Ein absichtlich veränderter Vergleichswert wird abgelehnt.
Eine NaN-Negativkontrolle fand vor echter Ausführung einen Fehler im neuen
Auditor: Python-max konnte ein NaN im zweiten Positionsanteil verdecken.
Explizite Form-/Endlichkeitsprüfungen aller Eingabearrays beheben dies; die
Negativkontrolle besteht. Keine reale QI-Rechnung oder Evidenz war betroffen.

Nächster Schritt: unveränderte registrierte echte Matrix erst nach Commit
dieses qualifizierten Pfads ausführen, anschließend separaten Auditor und
alle negativen Klassifikationen dokumentieren. Alte Autorenreferenzen bleiben.

Gesamtregression vor echter Ausführung:613 Tests bestanden,144 bekannte
NumPy/netCDF-Fixture-DeprecationWarnings einschließlich der neuen Kontrollen;
Ruff, Dokumentstruktur und Diffprüfung bestanden. Die separat dokumentierte
strenge native Importwarnung bleibt offen; keine behauptete ABI-Freiheit.
