# Gemeinsamer Feldlinienwinkel: algebraischer Prüfpfad vorbereitet

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
