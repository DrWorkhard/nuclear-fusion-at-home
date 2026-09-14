# Flussnormierte reale Spulen: Arbeitsstand

14. September 2026. [Protokoll](COUPLED_COIL_PILOT_PROTOCOL.md) ·
[Methodenentscheidung und Reviews](COUPLED_DESIGN_OPTIONS.md).

Alle acht realen Startqualifikationen sind bei`b5c5a4d` ausgeführt und unabhängig
auditiert: sechs bestehen, beide Referenzstarts mit acht Grundspulen nicht.
Die sechs freigegebenen Suchläufe sind bei`3e803c3` abgeschlossen und auditiert;
alle feinen Diagnostikläufe sind ebenfalls fertig. Die abschließenden Auditberichte
scheiterten jedoch beim JSON-Schreiben; ihre Ausgabe wird getrennt korrigiert.
Keine zulässige Form. Die Matrix vergleicht
Referenz/neue Plasmaform, zwei Spulenklassen und zwei Zielfunktionen.

Der physikalische Protokollreview hat vor Ausführung eine wichtige Lücke gefunden:
eine gleiche256-Punkt-Winkelauflösung in Linien- und Flächenfluss könnte einen
gemeinsamen Fehler verbergen. Ergänzt wurden256/512/1024-Winkelprüfungen und ein
über alle Abnahmeauflösungen unveränderlicher physischer Strom. Kein
Nachnormieren am feinen Raster. Der Vektorfehler wird ausdrücklich dimensionslos
mit unverändertem Konstruktionsmaßstab ausgewertet. Grenzen vor neuen Daten festgelegt.

Dieser Pilot prüft Konstruktion und einen Eintrittsschirm für spätere reale
Feldphysik. Er qualifiziert weder tatsächliche QI-Flächen noch Druck, Teilchenbahnen,
endliche Wicklungspakete oder Robustheit; `transfer_pass`/`step4_pass` bleiben false.
Negative Zellen werden einschließlich aller Aufrufe und Auflösungen erhalten.

Methoden-/Codereview präzisierten zusätzlich: keine Qualifikationsprobes in der
Suchauswahl, jeder tatsächliche Suchaufruf zählt ohne Cachegutschrift, ausdrückliche
Rasterpaare, richtige native Strafen und volle physische Abstandsgeometrie.
Fluss integriert analytische Fourier-Tangenten und einen signierten radialen
Flächenfächer; kanonische DOFs und eingefrorene Diagnostik-Nenner sind verbindlich.
Alle Korrekturen erfolgten vor Messung und vor Protokoll-Freeze.

## Additive Implementierung vor realen Daten

Das Protokoll ist bei`f7a7be3` eingefroren. Neue, getrennte Module implementieren
native Konstruktion, unabhängige Fourier-/Biot–Savart-/Geometrieprüfung und
Versuchsverwaltung; eigene Skripte führen Qualifikation/Suche, feinere Diagnostik
und Gesamtaudit aus. Kein alter numerischer Kern wurde dafür verändert.

Die unabhängige Integration prüft beide Spulenklassen und Methoden, verschobene
und vollständige Torusflächen sowie ausdrücklich aktive Längen-, Krümmungs-,
Spulenpaar- und Plasmaabstandsstrafe. Beide Richtungen und Schrittweiten bestehen
an diesen synthetischen Zuständen. Ein anfangs zu schwach verformtes Testfixture
aktivierte die beabsichtigte Krümmungsstrafe nicht; das Fixture wurde korrigiert,
keine Projektgrenze oder reale Messung verändert.

Eine zweite lesende Ablaufprüfung führte vor Daten zu zusätzlicher Absicherung:
exakt gebundene Qualifikationsfreigabe, Elternprozess-/Threadprüfung und eigene
Zeitprüfung unmittelbar vor Versuchsbeginn und Kandidatenspeicherung zusätzlich
zum äußeren600-s-Wächter. Ein verspätetes Bundle behält Rohdaten, wird aber kein
auswählbarer Kandidat. Jeder Versuch und die zusätzliche wertbasierte Feldarbeit
werden gespeichert; der letzte vollständige Checkpoint bleibt bei Abbruch erhalten.

Die inneren Zielfelder werden gegen die bereits angenommenen64²-Feldarchive aus
Schritt3 geprüft, einschließlich radialer Identität, Dimensionen und tatsächlicher
VMEC-Koordinaten. Für feinere Spulengitter bleibt der ursprüngliche ausgewählte
physische Snapshot maßgeblich, nicht eine neu normierte Momentaufnahme.
Nicht beweisbare Geometrieschranken bedeuten ein offenes physisches Gate;
unbekannte Rechenfehler werden nicht als solche umetikettiert.

Die vollständige Regression besteht:959 Tests, darunter193 neue Kontrollen,
null Fehler/Skips,144 bekannte Fixture-Warnungen,67,55s. Ruff und Dokumentstruktur
bestehen. Der Gesamtauditor wurde zusätzlich mit zehn echten nativen Bundles auf
einem synthetischen Torus samt allen neun Flussgittern Ende-zu-Ende geprüft.
JUnit-Rohdatei durch`evidence/coupled-coil-pilot-v1/implementation-regression.json`
gebunden. Das ist Software-/synthetische Qualifikation, noch keine Target-Freigabe.

## Reale Startqualifikation: sechs von acht freigegeben

Alle80 vollständigen Qualifikationsbundles und acht Startwiederholungen erhalten;
keine ausgelassenen Raster oder Ausführungsfehler. Alle Quellen-/Zielkoordinaten-,
Feld-/Geometriearithmetik- und Stokes-Gegenprüfungen bestehen. Größter relativer
direkter Feld-/A-Fehler1,1592e-13, größter Fluss-/Stokes-/Verfeinerungsfehler
6,6262e-16. Das qualifiziert die Rechnung, nicht die Anfangsform.

| Plasma / Klasse | Qualifikation N / V | Start-RMS Normalfeld | Start-Vektor-RMS | Gesampelter Plasmaabstand |
| --- | --- | --- | --- | --- |
| Referenz /6 Grundspulen | Pass / Pass | 0,482267 | 1,410597 | 6,054mm |
| Referenz /8 Grundspulen | Fail / Fail | 0,429338 | 0,699944 | 2,492mm |
| Neuer Entwurf /6 Grundspulen | Pass / Pass | 0,482339 | 1,434515 | 6,074mm |
| Neuer Entwurf /8 Grundspulen | Pass / Pass | 0,429403 | 0,699954 | 2,372mm |

Die beiden negativen Fälle überschreiten beim10-µm-Sinusschritt die feste
relative Ableitungsgrenze2e-4:2,28573e-4 fürN beziehungsweise2,28686e-4 fürV.
Die unabhängige Zielfunktionsrechnung bestätigt dieselbe Abweichung. Halbierte
Schrittweite reduziert den Fehler ungefähr vierfach und besteht; das ist mit
Differenzen-Trunkation vereinbar, beweist aber keine umfassend richtige Ableitung.
Beide ursprünglichen Gates bleiben negativ; kein nachträgliches Weglassen der
gröberen Schrittweite und keine Optimierung dieser beiden Zellen.

Die Anfangsformen sind sehr weit vom Eintrittsschirm entfernt. Insbesondere
liegen bereits gesampelte Plasmaabstände unter den geforderten80mm. Eine
anschließende lesende Analyse der erhaltenen n8-Rohdaten liefert darüber hinaus
Schnittzeugen: Grundspulen1–6 (nullbasiert) liegen in den gespeicherten
Randquerschnitten mit phi-Zeilen3/5/7/9/11/13. Dort liegen Punkte auf beiden
Seiten des exakten0,35m-Startkreises um(R=1,Z=0). Stetigkeit des Fourierquerschnitts
erzwingt einen Schnitt. Beide Ziele, identische Kreisparameter, Ebenenrest≤1,11e-16m,
kleinste Vorzeichenreserven innen87,276mm/außen5,657mm. Root reproduzierte diese
Agentenableitung aus denselben gespeicherten Arrays; kein neuer Feldaufruf,
kein formaler Intervallnachweis und keine vollständige Baugruppenprüfung.

Reines Vergrößern dieses konzentrischen Kreises ist ebenfalls begrenzt:
ein Referenzquerschnitt erreicht0,5787867m Abstand zum festgehaltenen Zentrum.
Eine ihn mit80mm Reserve umschließende Kreisinitialisierung benötigt deshalb
mindestens0,6587867m Radius beziehungsweise4,13928m Länge, über3,5m.
Das betrifft nur diese zentrierten Kreise, nicht verschobene/geformte Spulen
oder die Realisierbarkeit des Plasmas. Nach Abschluss des unveränderten Piloten
werden zielangepasste, außenliegende Starts eine vorrangige Folgehypothese.
N/V haben denselben jeweiligen physischen Start; ihre Gesamtzielwerte sind wegen
verschiedener Zielfunktionen kein direkter Methodenvergleich.

Evidenz: acht`evidence/coupled-coil-pilot-v1/qualification-*-audit.json`, darin
gebundene Rohdaten unter`artifacts/coupled-coil-pilot-v1/qualification-*`.
Die sechs freigegebenen Suchzellen sind inzwischen ausgeführt, siehe unten. Der achtspulige
Referenzvergleich bleibt in diesem Pilot unvollständig; keine allgemeine Rangfolge.
Numerische Quellen des abgeschlossenen Schritt3 bleiben unverändert.

## Begrenzte Suchphase: alle sechs am festen Budget beendet

Genau768 Suchversuche, alle vollständig; sechs zusätzliche frische Kandidaten-
Replays exakt. Alle unabhängigen Suchaudits bestehen Quellen, alle gespeicherten
Zielfunktionen, Auswahl, Zeit-/Aufrufzählung und Wiederholung. Auswahl jeweils
Aufruf127, außer neuer Entwurf/n6/N mit126 (nullbasiert). Keine Auswahl aus
Qualifikationsprobes oder ungespeicherten Zuständen. Suchzeit16,07–27,27s pro Zelle,
alle am128-Aufrufbudget, keine behauptete Konvergenz.

| Plasma / Klasse / Methode | Konstruktions-RMS Normalfeld | Innerer Vektor-RMS | Gesampelter Plasmaabstand | Max. gesampelte Krümmung |
| --- | --- | --- | --- | --- |
| Referenz /6 /N | 0,195211 | 0,714244 | 45,944mm | 16,773/m |
| Referenz /6 /V | 0,102345 | 0,503960 | 46,666mm | 15,449/m |
| Neuer Entwurf /6 /N | 0,132932 | 0,738202 | 51,778mm | 12,724/m |
| Neuer Entwurf /6 /V | 0,101789 | 0,484707 | 52,384mm | 15,830/m |
| Neuer Entwurf /8 /N | 0,282875 | 0,807754 | 38,568mm | 25,336/m |
| Neuer Entwurf /8 /V | 0,234517 | 0,646938 | 34,708mm | 23,016/m |

Das sind Konstruktionswerte, keine feine Abnahme. Gegenüber den Kreisen sinken
Normalfeldfehler und Abstandsstrafen, aber sämtliche Kandidaten verfehlen schon
gesampelte Plasmaabstands-/Krümmungsgrenzen und liegen weit über den Feldfehler-
schirmen. V verbessert den inneren Vektorfehler und den relativen Normalfeld-RMS
gegenüber N in allen drei vorhandenen Methodenpaaren, aber nicht sämtliche
Geometriegrößen. Kein zulässiger Gewinner, keine Pareto- oder allgemeine Rangfolge.

Sechs`search-*-audit.json` binden sämtliche lokalen Such-/Replay-Rohdaten.
Die Suchphase ist committed; sämtliche feinen Diagnostiken sind inzwischen
ausgeführt. Vor einem Folgestudienentscheid muss das nachstehende Ausgabeproblem
des Gesamtaudits geschlossen werden.

## Feine Diagnostik vollständig, Audit-Ausgabe zunächst gescheitert

Bei`e98339a` alle42 feinen Feldzustände,18 Linien-/36 Flächenflussgitter und sechs
Geometriezertifikatsrechnungen ausgeführt, keine Produzentenausfälle. Die sechs
Gesamtauditor-Aufrufe scheitern erst beim JSON-Schreiben: NumPy-Wahrheitswerte
unter`geometry.self_nearness[*].exact_repeated_node` sind nicht direkt
serialisierbar. Kein finaler Auditbericht wurde dabei gespeichert. Rohdaten und
Quellbindungen bleiben unverändert; der Fehlervermerk bindet sämtliche sechs
Produzentenberichte:`evidence/coupled-coil-pilot-v1/validation-output-failure.json`.
Die ursprünglichen sechs Tracebacks stehen im Toolverlauf, nicht in separat
umgeleiteten Logdateien; diese Einschränkung wird nicht rückwirkend verschleiert.

Der Quellreview identifiziert zusätzlich ein mögliches Falsch-Negativ: Die Prüfung
`is False` erkennt einen NumPy-Falsewert nicht als Python-False. Ein sonst gültiger
Geometriebericht könnte deshalb fälschlich abgelehnt werden. Das muss bei der
Ausgabekorrektur explizit gegengeprüft werden; kein bloßer Schreibfehler-Pass.
Der Fehlversuch ist bei`39951e3` committed. Ein neuer, getrennter Adapter
`scripts/serialize_coupled_coil_audit.py` führt den unveränderten Gesamtauditor
auf genau den sechs gebundenen Altberichten erneut aus. Er normalisiert skalare
NumPy-Typen verlustfrei, protokolliert jede Konvertierung und berechnet die
Eintrittsgates nochmals auf normalen Python-Typen. Jede Klassifikationsänderung,
nichtfinite/unsupported Ausgabe, unvollständige Prüfung oder positive
Eintritts-/Transfer-/Schritt4-Behauptung führt zur Ablehnung. Neue Ausgabepfade,
gebundener Fehlbericht und committed Adapter/Testquellen sind Pflicht.

Ein unabhängiger lesender Agentenreview bestätigt mit dem tatsächlichen Gate
den synthetischen Falsch-Negativ-Fall; die Recovery verweigert dessen Umdeutung.
Mit einer zusätzlichen echten Abstandsverletzung bleibt die Ablehnung bestehen.
Die Reviewhinweise führten vor Anwendung zu strikten Status-/Scopeflags und
sauberer Ablehnung von NumPy-Skalaren ohne verlustfreie Python-Konvertierung.
Alte Kerne, Kriterien und Evidenz bleiben unverändert. Diese Ausgabe-Recovery
qualifiziert insbesondere keinen allgemein reparierten positiven Geometriepfad.
Nächster Schritt: Adapter/Testqualifikation committen, dann alle sechs
Originalaudits mit frischen Ausgabedateien wiederholen; keine neuen Such-/
Gradientenbundles oder Gleichgewichtssolves.
