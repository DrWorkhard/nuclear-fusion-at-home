# Schritt3-Folgeversuch: beide Wirkungsdomänen und lokale Schutzgrenzen

Vor erster neuer Auswertung registriert, 14. September2026. Der vollständig
[abgelehnte erste Entwurf](PLASMA_OPTIMIZATION_RESULTS.md) bleibt unverändert.
Neues Experiment, keine Fortsetzung seines Budgets oder Umdeutung seiner Abnahme.
Ziel: tatsächlicher gemeinsamer Vorteil auf enger und erweiterter Domäne unter
allen bisherigen numerischen und lokalen physischen Grenzen. Schritt3 bleibt offen.

## Unverändert und bewusst geändert

Dieselben vier benannten Moden, Autoren-/Solverquellen,201/401-Kaltstartprofile,
fixer Randfluss, Vakuum, R00=1m, Invariantendomäne und periodenzugeordnete Aktion
wie im [ersten Protokoll](PLASMA_OPTIMIZATION_PROTOCOL.md). Keine alten Kerne,
Ergebnisse oder externen Quellen ändern. Kein globaler QI-/Orbit-/Druck-/SoTA-Pass.

Neu: die bisherigen35 erweiterten s/q-Zellen gehen bereits in die Konstruktion
ein, auf801 phi/16 alpha. Ihr Mittel S_wide wird minimiert; der enge bisherige
Trainingswert S_narrow muss zugleich profitieren. Die bereits gesehenen Domänen
sind **kein verblindeter Transfer-Holdout mehr**. Die unabhängige Abnahme prüft
Quellen, andere Auswerter, feinere Gleichgewichte/Raster und alle lokalen Kriterien,
nicht Generalisierung auf bislang unberührte Plasmabereiche.

## Phase A: erhaltene Formen verwenden, neue Rechnungen begrenzen

Alle16 eindeutigen201er Suchzustände von `plasma-design-v2` auf dem breiten
801/16-Raster auswerten, auch wenn sie sich später nicht auswählen lassen.
Referenz ist Index0. Fehlende Mulden bleiben Fehler, nie Nullkosten. Neue Aktionen
mit unabhängiger Gaussquadratur kontrollieren; keine alten Auswertungen ersetzen.

Eine auswählbare Form muss neben den alten Volumen-/iota-/Solverwächtern bereits
auf diesem Konstruktionsraster erfüllen: mindestens0,5% enger und1,5% breiter
Vorteil, alle70 Mittelwirkungen innerhalb2%, alle Enveloppen innerhalb
max(1,1*Referenz,Referenz+0,002).1,5% ist ein zusätzlicher Konstruktionspuffer;
die physische Abschlussgrenze0,5% und der Fünffach-Unsicherheitsschirm bleiben gleich.
Unter zulässigen Formen kleinsten S_wide wählen, Gleichstand frühester Index.

## Phase B: nur falls Phase A keine auswählbare Form liefert

Acht frische201er Kaltstarts bei +/-1e-5m entlang jeder der vier Achsen um den
unveränderten Ausgangspunkt. Auf beiden Domänen auswerten. Aus symmetrischen
Differenzen relative Gradienten von S_narrow, S_wide und allen70 mittleren
Wirkungen bilden. Das ist ein lokales Vorschlagsmodell, keine qualifizierte
exakte Ableitung oder physische Zulassung. Jede tatsächliche Probe wird neu gelöst.
Fehlt eine zentrale Modellzelle, endet diese Phase negativ; keine fehlenden
Ableitungen durch Null ersetzen oder numerische Schrittweite heimlich ändern.

Lineares Modell: x=1e-4m*u, |u_i|<=1. Maximiere t>=0 bei vorhergesagtem
relativem Abstieg mindestens t in beiden S-Werten und höchstens1% Betrag
vorhergesagter Änderung jeder mittleren Wirkung. Der1%-Modellpuffer ist strenger
als der unveränderte2%-Abnahmeschirm. Bestehendes SciPy/HiGHS, ein Thread;
Matrix, Bounds, Lösung, Multiplikatoren, Status und Warnungen speichern.
Separater Audit rekonstruiert Differenzen/Matrix und prüft primale/duale
Optimalitätsbedingungen innerhalb1e-8. Kein nichtpositiver gemeinsamer Modell-
abstieg als erfolgreichen Entwurf ausgeben.

Bei t>0 alle drei festgelegten Vorschläge x, x/2, x/4 real kalt lösen und auf
beiden Konstruktionsdomänen auswerten; kein früher Stopp nach erstem Erfolg.
Dieselbe Zulassungs-/Auswahlregel wie Phase A. Ist kein Vorschlag auswählbar,
bleibt der Versuch negativ. Keine weitere Suchrunde in diesem Experiment.

## Phase C: Auswahl einfrieren und unabhängig abnehmen

Ein frischer201er Kaltstart der ausgewählten Form plus ein401er Kaltstart.
Die unveränderten, vollständig auditierten201/401-Referenzen aus v2 werden
explizit wiederverwendet, nicht als neue Solves gezählt. Maximal13 neue Solves:
acht Differenzzellen, drei Probes, Wiederholung und feiner Kandidat; Phase A
kann die ersten elf vermeiden. Alle Zustände/Fehler/Logs/Zähler erhalten.

Die vollständige vier-Zustands-/vier-Raster-Abnahme des ersten Protokolls bleibt:
35 Zellen, vier Tracegitter einschließlich verschobenen alpha, beide Kontur-
gitter,64/128-Feldidentitäten, veröffentlichter Tracer und unabhängige Aktionen.
Referenzdiagnostik darf erneut ausgewertet werden; keine behaupteten neuen
Referenzgleichgewichte. Ein explizit als solcher markierter Diagnoseadapter darf
den vorhandenen Auswerter verwenden, ist aber **kein alter Zwei-Poll-Suchbericht**.
Der neue Auditor prüft die tatsächliche Phasen-/Auswahlherkunft unabhängig.

Abschluss weiterhin: neue Form, exakte201er Wiederholung, Geometrie, vollständige
gültige Domäne, Konturen/Felder/Tracer, sämtliche Verfeinerungen, alle lokalen
2%-/Enveloppegrenzen, mindestens0,5% enger Trainingsvorteil sowie0,5% feinster
breiter Vorteil, letzterer größer als5mal die unverändert gebildete numerische
Unsicherheitssumme. Zusätzliche Konstruktionstests ersetzen kein einziges Gate.

## Ressourcen, Evidenz und Ende

Protokoll zuerst committen, danach additive Implementierung/Tests/Auditor vor
Ausführung committen. Keine Installationen.>=3GiB vor Beginn,>=2GiB währenddessen;
je Solver höchstens1800s, keine konkurrierenden schweren Jobs. Als konservative
Obergrenze grob15Minuten zusätzliche Gleichgewichtszeit plus Auswertung/Abnahme;
keine automatische Budgetverlängerung. Nach jedem abgeschlossenen Phasenschritt
dokumentieren und lokal committen. Keine Pushes, Autorenkontakte oder externen Änderungen.

Nur bestandene Abnahme schließt Schritt3 im registrierten QI-nahen Vakuumumfang.
Danach Übergabe, kein automatischer Schritt4/5. Auch dieser neue Versuch kann
negativ enden; dann ist die belegte Einschränkung festzuhalten, nicht wegzudefinieren.
