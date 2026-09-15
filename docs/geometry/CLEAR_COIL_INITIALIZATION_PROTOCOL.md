# Außenliegende Spulenstarts: geometrischer Folgeversuch

Vor Implementierung/Target-Auswertung registriert,15. September2026.
[Negativer Pilot](../optimization/COUPLED_COIL_PILOT_RESULTS.md) ·
[Gesamtumfang Schritt4](../optimization/COUPLED_DESIGN_OPTIONS.md).
Dieser Versuch qualifiziert ausschließlich Startgeometrie. Keine Magnetfeld-
oder QI-Zulassung, keine gemeinsame Optimierung, kein Schritt4-Abschluss.

## Hypothese und unveränderte Anforderungen

Die festen Kreise umR=1 schneiden das Plasma; auch nach Optimierung übersieht
das grobe Gitter kleine Abstände. Zielangepasste, verschobene/konvex geformte
planare Starts könnten dieselben geometrischen Anforderungen erfüllen, bevor
Magnetfeldoptimierung beginnt. Kein Schluss, dass planare Spulen das gewünschte
QI-Feld realisieren können. Spätere Suchspulen dürfen nichtplanar werden.

Dieselben zwei gebundenen401er Plasmaränder, nfp2/Symmetrie und Klassen n6/M5
sowie n8/M7. Identische SI-Grenzen: Länge≤3,5m, Krümmung≤12/m,
Spulenabstand≥0,06m, Plasmaabstand≥0,08m. Keine alten Gateänderungen.
Ein neuer Start verändert den absoluten späteren Parameterbereich; deshalb kein
isolierter Methodenvergleich unter identischer alter±0,12m-Box.

Zwölf gemeinsame, auf beide Plasmaformen bezogene Spulensätze:
zwei Klassen × Kreis-/Form-LP × drei feste Sollabstände d=0,10/0,14/0,18m.
Jeder Grundspulenwinkel phi_i=(i+1/2)π/(2*nbase) bleibt fest. Kreis-LP:
Stützfunktion bisK=1; Form-LP:K=M−1. Alle Kandidaten, auch zu lange oder
sonst ungeeignete, behalten sämtliche Prüfungen. Keine Auswahl anhand eines
noch nicht berechneten Magnetfelds, keine adaptive zusätzliche Variante.

## 3D-Plasmaschutz durch vollständig abgedeckte Randpunkte

Beide vollständigen Fourier-Ränder auf256×256 Volltoruswinkeln auswerten;
alle Moden erhalten. Gleichmäßige Winkel, keine halbe Periode als Abstandsziel.
Positive kontinuierliche Zylinderradien aus Gitterminimum und Fourier-
Ableitungspolster verifizieren; keine ungeprüfte negative-R-Darstellung.
Die vorhandenen analytischen Ableitungssuprema ergeben je Ziel den
Oberflächen-Coverradius epsilon=L_phi/(2*256)+L_theta/(2*256)+fp_pad.
Die Vereinigung der Kugeln mit RadiusE=d+epsilon um sämtliche Randgitterpunkte
überdeckt den gesamten d-Nahbereich des jeweiligen kontinuierlichen Randes.

In jeder Spulenebene e_R(phi_i),e_Z gilt für einen Randpunkt p:
offplane=p·e_phi, proj=(p·e_R,p_z). Nur Kugeln mit|offplane|≤E schneiden die
Ebene; ihre Schnittdisk hat Mittelpunkt proj und Radius sqrt(E²−offplane²).
Verwerfen nur, wenn proj_R+E<R_floor, denn jeder spätere Spulenpunkt muss
R≥R_floor erfüllen. Das verwirft den entfernten gegenüberliegenden Toruszweig
mit einer expliziten Distanzbegründung, nicht anhand eines willkürlichen
Vorzeichens. Keine andere Winkel-/Nachbarschaftsauswahl.

R_floor=0,06/[2sin(π/(4*nbase))]+0,025m. Für positive Radien und gleichmäßig
verteilte radiale Ebenen ist2R_floor sin(π/(4*nbase)) eine globale untere
Schranke des physischen Spulenpaarabstands; zusätzlich direkte Volltorusprüfung.
Der Ebenenursprung c ist das Mittel beider analytischer m=0-R/Z-Querschnittswerte
am jeweiligen Winkel. Alle Diskzentren werden relativ zu c gespeichert.
Leere Diskmengen, nichtfinite Daten oder ungeprüfte R-Geometrie sind Fehler.

## Lineare Konstruktion mit kontinuierlichen Schutzpolstern

Eine relative Stützfunktion h(α)=h0+Σ[a_m cos(mα)+b_m sin(mα)] beschreibt
q(α)=c+h*n+h'*t, n=(cosα,sinα),t=(−sinα,cosα).
Dann q'=(h+h'')t, Krümmung=1/(h+h'') bei positiver Krümmungsradiusfunktion
rho=h+h'', und Länge=2πh0. Fouriergrad der kartesischen Kurve höchstensK+1≤M;
explizite kanonische Meterkoeffizienten exportieren, kein runtime-DOF-Mapping.
Exportparameter α=−2πt reproduziert die lokale native Kreisorientierung
R=c_R+r cos(2πt), Z=c_Z−r sin(2πt). Keine nachträgliche Fouriertrunkation;
exakte analytische Modenkonvolution bisK+1 und Auffüllen bisM. Aktuelle und
gespiegelte Orientierung explizit getrennt speichern; keine Ströme/Flusswerte
in einen rein geometrischen Snapshot erfinden.
Diese bekannte Stützfunktionsdarstellung ist keine Neuheitsbehauptung.
[Antunes/Bogosel, Abschnitt2.1](https://arxiv.org/html/1809.00254#S2.SS1).

1024 gleichmäßige Normalenwinkel, delta=π/1024. Diskhülle
S(α)=max_j[(proj_j−c)·n(α)+radius_j]. Ihr Lipschitzwert ist höchstens
L_S=max_j||proj_j−c||. Hilfsvariablen u_m≥|a_m|,v_m≥|b_m| liefern
L_h=Σm(u_m+v_m), L_rho=Σm|1−m²|(u_m+v_m).
Jede LP-Zeile fordert

- h(α_j)−delta*L_h ≥ S(α_j)+delta*L_S+1e-9m;
- rho(α_j)−delta*L_rho ≥0,10m+1e-9m;
- c_R−h(π)≥R_floor+1e-9m.

Damit gelten Einschluss und positive rho auch zwischen den Normalenwinkeln,
sofern die LP-Reste unabhängig hinreichend klein sind. Die Umschließung jeder
Schnittdisk hält die Kurve außerhalb des zugehörigen offenenE-Kugelinneren;
zusammen mit dem Cover bleibt zum kontinuierlichen Plasmarand mindestensd.
Fester1e-9m-Konstruktionspuffer, Abnahme-Primalrest≤1e-10m.
Im Audit zusätzlich die tatsächlichen absoluten Fourierkoeffizienten statt
LP-Hilfsvariablen für L_h/L_rho einsetzen und alle kontinuierlichen
Schranken direkt prüfen; ein zulässiger LP-Rest allein ist kein Geometriepass.

Minimiere2πh0 mit SciPy-HiGHS,dual-simplex, primal/dual feasibility_tolerance1e-10.
Grenzen h0∈[0;1,5]m;
alle a/b∈[−0,5;+0,5]m, alle u/v∈[0;0,5]m. Dies sind neue begrenzte
Konstruktionsvariablen, keine physische Zulassung. Länge wird absichtlich erst
separat gegen3,5m bewertet, damit ein zu großer benötigter Start erhalten bleibt.
Sämtliche LP-Matrizen, Lösung/Dualwerte, Status/Fehler und Solverversion speichern.
Keine Infeasibilitätsbehauptung allein aus Solverstatus; ohne eigenes Zertifikat
ist ein nicht gelöstes LP ein ungeklärter/negativer Versuch.

## Budget, unabhängige Abnahme und Auswahl

Genau84 Grundspulen-LPs pro kompletter Matrix, höchstens eine unveränderte
Wiederholung jedes LPs(168 Solveraufrufe insgesamt). Jeder Versuch zählt auch
bei Fehler; keine adaptive Reparatur. Ein HiGHS-Aufruf höchstens30s, zusätzlich
Elternprozesswächter für den gesamten Produzenten1800s mit0,5s Takt/5s Frist.
Ein Thread, seriell; keine parallelen schweren Experimente. Keine nativen
Magnetfeld-/Gradientenaufrufe und keine neuen Gleichgewichtssolves.

Unabhängiger Auditor rekonstruiert aus den gebundenen Inputs Diskmengen,
Supportmaxima, Matrizen und Fourierkoeffizienten. Primalverletzung≤1e-10m;
Diskmitgliedschaft/IDs und Matrixdimensionen exakt; Koordinaten, Supportwerte,
Matrizen und exportierte Fourierkoeffizienten maximal5e-12 absolute Abweichung
in ihren aufgezeichneten SI-/Matrixeinheiten. Alle Werte endlich. Diese
Rekonstruktionsgrenze ersetzt keines der kontinuierlichen geometrischen Gates.
dual/stationarity/complementarity/primal-dual-gap absolut≤1e-8 bei protokollierter
Skalierung. Abweichende oder fehlende Rohdaten führen zur Ablehnung. Exakte
Wiederholung von Primal-/Dualarray und ausgewählter Geometrie verlangen;
Solvertimer und andere zwangsläufig variable Verwaltungsfelder ausgenommen.

Unabhängige direkte Kurvenrekonstruktion auf1024 Punkten, analytische
Länge/rho-Schirme und geometrische Gleitkommapolster; alle physischen Kopien
explizit. Volltorus-Punktabstände mit konservativen Fourier-Coverradien auf
1024Kurvenpunkten und256² sowie512² Plasmapunkten, zusätzlich letztere um
halbe Zellen verschoben. Beide Plasmaziele, alle drei Abstandsauflösungen.
Alle geometrischen Gates müssen bestehen. Konvexer planarer Einzelbogen mit
rho>0 und positiver R-Schranke hat keinen Selbstschnitt; diese zusätzliche
mathematische Aussage gilt nicht für spätere frei nichtplanare Optimierung.
Keine gerichtete Intervallarithmetik oder endliche Wicklungspaketqualifikation.

Auswahl pro Klasse nur unter vollständig geometrisch angenommenen Sätzen:
kleinste Summe Grundspulenlängen; Gleichstand d aufsteigend, Kreis vor Form.
Alle übrigen bleiben sichtbar. Kein ausreichender Satz ist ein negativer
Geometrieversuch, kein Beweis unmöglicher nichtplanarer Spulen oder QI-Physik.
Ein Startpass darf lediglich einen **neu zu registrierenden** fein aufgelösten
Feldfit vorbereiten; Feld-/Transfer-/Schritt4-Pass stets false.

## Qualifikation und Ressourcen vor realen Daten

Vor Ausführung Protokoll/Code committen. Synthetische verschobene Kreise,
konvexe nichtkreisförmige Fourierstützfunktion, bekannte Flächen-Cover,
schräge entfernte Kugeln/gegenüberliegender Toruszweig und enges Paar testen.
Direkte Differentiation von q, exakte Kreis-Länge/Krümmung, R-Minimum,
LP-Primal/Dualwerte und fehlerhafte/mutierte Quellen/Raster/Gates gegenprüfen.
Alte numpyskalare Gate-Lücke nicht übernehmen; typed finite native Python-JSON.
Unabhängiger Methoden-/Codereview vor Target-Auswertung.

Neue Artefakte geschätzt≤300MiB, RAM≤1GiB bei blockweisen Supportmaxima;
vor Beginn≥3GiB freier Plattenplatz, live≥2GiB. Keine Installation/Downloads/
externen Quelländerungen. Phasenweise dokumentieren und lokal committen.
