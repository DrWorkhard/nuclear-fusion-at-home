# Schritt3: eigene QI-nahe Plasmaoberfläche — vorab registrierte Abnahme

2026-09-13. Nutzer autorisiert ausdrücklich Schritt3 nach abgeschlossenen
Basisetappen1/2. Ziel ist echte Oberflächen-/Gleichgewichtsoptimierung, nicht noch
ein Spulenlauf. Ein lokaler numerisch bestätigter Entwurfsbeitrag genügt; SoTA
bleibt Schritt5. Ein nur lauffähiger oder negativer Versuch schließt Schritt3 nicht.

## Physikalischer Umfang und Primärquellen

Eigene kleine Fourieränderungen am offenen Goodman-nfp2-Vakuumfall, gleiches
Randfluss-/Druck-/Stromprofil und gleiche Feldperiodenzahl. Vergleich gegen seine
**neu gerechnete unveränderte Eingabe mit demselben Solver**, nicht gegen einen
als bitgleich ausgegebenen historischen Autoren-Wout. Autoreninputs bleiben erhalten.

[Goodman et al.](https://arxiv.org/abs/2211.09829) definieren Omnigenität über die
Feldlinien-Unabhängigkeit der zweiten Invariante und QI zusätzlich über poloidal
geschlossene Feldstärkekonturen. Wir verwenden die bereits kontrollierte reduzierte
Einwegwirkung A=Integral sqrt(1-B/Bstar) dl, nicht absolute Teilchendrift. Neu ist
eine explizite Zuordnung der zwei vollständigen Mulden zu zwei toroidalen
Feldperioden; kein bloßes Vermischen aller Mulden in einem Extremwert-Enveloppe.
[Proximas ConStellaration](https://github.com/proximafusion/constellaration) ist
ein relevanter öffentlicher Plasma-Benchmark; hier kein zusätzlicher Download,
Umgebungswechsel oder behaupteter Vergleich mit dessen Ergebnissen.

Abnahme gilt für einen QI-nahen Vakuumentwurf auf der registrierten Domäne unter
VMECs verschachtelter-Flussflächen-Annahme. Keine mathematisch exakte globale QI,
kein maximum-J, keine endliche Energie-/Orbit-/Turbulenz-/Transport- oder
MHD-Stabilitätsqualifikation. Auch keine passenden Spulen, Mechanik, SQuID-C oder
SoTA. Diese Aussagen werden nicht durch kleinere Zielwerte ersetzt.

## Unveränderte Quellen und veränderliche Parameter

Ausgangspunkt: `artifacts/qi-fresh-resolution-v1/nfp2-vacuum-s201-a2/original_input.json`,
zugehörige Autoreninput-/Solverhashes aus `evidence/qi-fresh-resolution-v1.json`
und `evidence/qi-producer-inventory-v1.json`. Das bestehende effektive numerische
Profil aus `qi_resolution.effective_input` bleibt für201/401 Halb-/Vollflächen
mit Angularfaktor2 und VMEC8.52-Iterationsstil unverändert. Alle drei Kraftreste
müssen<=1e-12 sein; Randkoeffizientenfehler<=1e-12. Kaltstarts, ein Thread.

Nur vier explizit benannte physische Fourierkoeffizienten dürfen sich ändern,
in dieser Reihenfolge: rbc(1,1), zbs(1,1), rbc(2,0), zbs(2,0), wobei(m,n) gilt.
R00=1m bleibt fest. Änderungen x in Metern gegenüber dem Autoreninput, |x_i|<=1e-3.
Keine automatische Modensortierung, kein Entfernen von Freiheitsgraden, keine
Änderung von phiedge/nfp/Profilen oder Umgebungen.

## Ziel und unveränderliche Invariantendomäne

Bstar(q)=1.0082953902491054+q*(1.5870966275564338-1.0082953902491054)T,
aus der erhaltenen nfp2-Domäne; für alle Entwürfe/Radien/Auflösungen unverändert.
Training: s=0.25,0.5,0.75; q=0.1,0.3,0.5,0.7,0.9;801 phi-Punkte,
16 gleichförmige alpha auf[0,2pi), zwei Feldperioden, alpha_offset=0.

Auf jeder Linie genau zwei vollständige Mulden, jeweils innerhalb ihrer
eindeutigen Periode j=0,1. Zusätzliche, fehlende oder zensierte Mulden führen
zur Ablehnung, niemals zu Nullkosten. Ziel S ist das Mittel über s,q,j,alpha
von ((A-alpha_Mittel(A))/alpha_Mittel(A))². Mittelwerte bleiben positiv/endlich;
sämtliche Aktionen, Grenzen, Rohtraces und Zähler werden gespeichert.

## Begrenzte klassische Suche

Deterministische Koordinatensuche: zunächst x=0, danach zwei vollständige
Pollrunden mit jeweils +/-Schritt entlang aller vier Achsen. Schritt zunächst
2e-4m; für Runde2 unverändert nach einer Verbesserung, sonst halbiert. Pro Runde
kleinsten S-Wert aus altem Zentrum und allen gültigen Probes wählen; Gleichstand
behält den frühesten Zustand. Kein Gradientenvorteil oder Konvergenznachweis.
Identische schon gerechnete Punkte dürfen mit vollständigem Cachezähler wiederverwendet werden.

Konstruktionswächter: numerisch konvergiert, vollständige Mulden, höchstens1%
Volumenänderung und höchstens0.02 absolute iota-Änderung bei den drei Trainingsradien.
Maximal17 angefragte Suchpunkte inklusive Start (höchstens17 Solves), danach
ein separater Kaltstart des ausgewählten201er Kandidaten sowie je ein401er
Kaltstart von Referenz und Kandidat: höchstens20 Solves. Ein identischer Start
oder fehlender reproduzierbarer Vorteil ist kein Etappenabschluss.

## Unabhängige Abnahme — kein Feedback an Auswahl

Referenz und ausgewählter Kandidat, jeweils201/401; s=0.1,0.25,0.5,0.75,0.9;
q=0.03,0.1,0.3,0.5,0.7,0.9,0.97. Traces(1601,32,2),(3201,32,2),(3201,64,2)
sowie(3201,64,2) mit um pi/64 verschobenem alpha-Gitter. Alle Kombinationen
und Fehler erhalten. Pro s/q stets beide Periodenfamilien/alle Linien gültig.

- Trainingsvorteil und feinster erweiterter Gesamtvorteil jeweils>=0.5%.
- Der feinste Vorteil muss größer als das Fünffache der Summe der absoluten
  beobachteten S-Änderungen beider Entwürfe bei radialer201->401, phi-, alpha-
  und verschobener-alpha-Prüfung sein. Keine garantierte mathematische Fehlerschranke.
- Bei jeder Verfeinerung zugeordnetes A innerhalb1e-3 relativ; erweiterte
  S-Werte innerhalb5% bzw.1e-12 absolut. Periodenidentität bleibt erhalten.
- Jede feinste s/q/j-Zelle: relative Wirkungs-Enveloppe nicht schlechter als
  max(1.1*Referenz,Referenz+0.002); mittlere Wirkung ändert sich höchstens2%.
  Kein Ausblenden schlechter Zellen durch den Gesamtmittelwert.
- Feldstärkekonturen: dieselben35 Zellen bei256x512 und512x1024; zwei poloidal
  geschlossene einfache Wurzelgraphen, unveränderte vorhandene Ablehnungslogik.
- Native/Clebsch-Feldidentitäten auf64/128 bei den drei bisherigen Innenradien:
  bestehende1e-3-Schirme und1e-5 Fehlerverfeinerung unverändert. Dies ersetzt keine
  historische Autorenfidelität oder vollständige topologische Flussflächenprüfung.
- Unabhängige Tracing-Gegenrechnung aus der erhaltenen Autorenroutine auf
  Trainingsgittern beider401er Wouts: B<=1e-8 relativ, Länge/A<=1e-3 relativ.
- Separater Auditor prüft Quellen, Änderungen ausschließlich der vier erlaubten
  Moden, vollständige Pollauswahl, reale201er Wiederholung und feinere Gleichgewichte.
  Er berechnet alle Aktionen aus den Rohtraces mit unabhängiger64-Punkt-Gauss-
  Quadratur neu (<=1e-6 relativ) und S aus den Aktionen separat. Fake-Zulassung,
  fehlende Domänenzellen und nichtfinite Daten werden kontrolliert abgewiesen.

## Reihenfolge, Kosten und Ende

Protokoll committen, danach neue additive Kerne/Runner/Auditoren mit synthetischen
und negativen Kontrollen implementieren/committen. Keine alte numerische Datei
oder Evidenz verändern. Vor Solves aktuelle Quellen prüfen, >=3GiB freier Platz;
laufend>=2GiB, keine konkurrierenden schweren Prozesse. Solver pro Kaltstart
höchstens1800s, tatsächliche Versuche/Abbrüche/Logs erhalten. Der bekannte Import-
Warnungsstatus wird nicht durch neue Filter versteckt.

Bei bestehender Laufzeit von etwa47s für den201er Referenzfall liegt der
Suchaufwand grob im Bereich von Minuten bis einigen zehn Minuten plus Abnahme.
Kein Budget automatisch verlängern. Negative Abnahme bleibt negativ; Diagnose
und neu registrierter Folgeversuch dürfen nach dokumentiertem Zwischenabschluss
folgen, niemals nachträgliche Schwellenlockerung. Erst bestandenes Quellen-,
Physik-, Vorteil- und Reproduzierbarkeitsgate schließt Schritt3 in diesem Umfang.
Danach dokumentieren/committen/übergeben, Schritte4/5 nicht automatisch beginnen.
