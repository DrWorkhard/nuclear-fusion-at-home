# Radiale Feldlinien-Gauge — begrenzte Diagnose

Festgelegt 2026-09-12, vor Implementierung und neuen Traces. Schritt 1 hat noch
keinen global qualifizierten QI-/Maximum-J-Maßstab. Hier prüfen wir eine konkrete
offene Einschränkung der schon gemessenen radialen Bouncewirkungsableitungen.

## Physikalische Frage und eigene Herleitung

Die vorhandene Messung fixiert die VMEC-Feldlinienmarke
`alpha=theta+lambda-iota(s)*phi`. Für eine radial neu markierte Familie
`alpha=a+c*(s-s0)` ist nach der Kettenregel
`dA/ds|a = partial_s A|alpha + c*partial_alpha A|s` bei s=s0.
Das ist eine andere Fortsetzung benachbarter Feldlinien, keine Änderung des
Gleichgewichts. Bei exakt omnigenem Feld ist partial_alpha A=0; bei endlicher
Abweichung darf man eine punktweise radiale Vorzeichenaussage nicht ohne Prüfung
als gauge-unabhängig behandeln. Diese Kettenregel ist unsere direkte Ableitung,
kein neu behauptetes Resultat der Autoren.

Physikalische Definition von Wirkung, Omnigenität und Maximum-J:
[Goodman et al., Abschnitte 1 und 5](https://www.cambridge.org/core/journals/journal-of-plasma-physics/article/constructing-precisely-quasiisodynamic-magnetic-fields/6601E449C8DD3B3FEB361DA2C5732EFC).
Die Diagnose ersetzt weder die vollständige Invariantenmenge noch die
physikalische Präzessionsberechnung oder Gleichgewichtskonvergenz.

## Eingefrorener Umfang

Alle vier bisherigen Fälle nfp2/nfp3, Vakuum/beta2 aus
`evidence/qi-radial-action-v1/`. Wout-Hashes und **dieselben fünf Bstar-Werte**
übernehmen, niemals den zugänglichen Bereich passend verschieben. s0=0,5,
acht gleiche Alpha-Anker, vier Feldperioden, identische geometrische
Muldenzuordnung mit zentralem Zwei-Perioden-Fenster.

Gauge-Steigungen c=-1,0,+1 rad pro normiertem Radius. Alle sieben alten Radien,
nphi=801/1601/3201, h=0,04/0,02/0,01. An s0 sind alle Gauges derselbe Trace;
diesen unverändert verwenden, keine doppelten Rechenarbeiten verschweigen.
c=0 wird vollständig gegen alle alten B/L/Theta/Speed-Arrays geprüft: numerisch
**exakt**, nicht nur derselbe zusammengefasste Vorzeichenanteil.

Zusätzlich alpha_offsets=+-0,01 und +-0,005 am s0, jeweils nphi=3201;
dieselbe Muldenfamilie weiterverfolgen und zentrale partial_alpha A-Differenz
bestimmen. Eine fehlende/mehrdeutige Fortsetzung oder unzugängliche Pitch-Zelle
bleibt ein Fehler und wird nicht ausgelassen.

Für jede Familie dieselbe radiale Stencil-Auswertung und empirische
Vorzeichenprüfung wie im [ursprünglichen Protokoll](QI_RADIAL_ACTION_PROTOCOL.md).
Erneut alle positiven, negativen und unaufgelösten Familien ausgeben. Erwartet
wird nicht automatisch Vorzeicheninvarianz: Änderungen sind wissenschaftliche
Ergebnisse, kein Anlass für Grenzwertänderungen.

Separater Kettenregel-Test auf den feinsten Stencils:
`abs(Dc-(D0+c*Dalpha))/A0 <= max(0.01,0.05*abs(Dc/A0))` für beide c.
Alle Fehler und beide Alpha-Schrittweiten erhalten; Alpha-Verfeinerung derselbe
relative/absolute Schirm. Das ist ein empirischer diskreter Konsistenztest,
keine rigorose Fehlergrenze und keine Aussage für beliebig große c.

## Vorabkontrollen, Ausführung und Abgrenzung

Tracer erhält nur einen optionalen endlichen Alpha-Offset; Standardaufrufe
müssen alte Arrays erhalten. Synthetischer Torus: direkte Theta-/Speed-Formeln
bei Offset, 2pi-Periodizität auch mit Lambda, NaN/Inf-Ablehnung.
Analytische Wirkung `A(s,alpha)=2-s+0.1*sin(alpha)` prüft Vorzeichen und Faktor
der Kettenregel; eine alpha-unabhängige Kontrolle muss invariant bleiben.

Protokoll zuerst committen, getesteten Adapter/Runner vor Ausführung committen.
Neue Traces/volle Stencils, Herkunft und Prüfwerte unveränderlich speichern.
Ein unabhängiger arithmetischer Replay prüft Differenzen/Zuordnung/Vorzeichen
aus gespeicherten Daten; keine Übertragung dieser Ergebnisse in einen Spulenlauf.
Der bereits festgelegte AL-Suchcode bleibt unberührt.
