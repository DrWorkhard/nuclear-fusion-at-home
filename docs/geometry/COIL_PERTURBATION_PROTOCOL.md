# Kumulative Geometrieschranke für Spulenänderungen: Qualifikationsprotokoll

19. September2026, vor Implementierung und neuer Perturbationsmatrix.
[Methodenentscheidung](../optimization/GEOMETRY_PRESERVING_SEARCH_OPTIONS.md).
Feldfreie Voraussetzung für einen später separat registrierten Formfit.
Keine neue Feldoptimierung, magnetische Zulassung oder Schritt4-Abnahme.

## Quellen und unveränderlicher Bezug

Genau die bei323cfdd angenommenen Snapshots`n6-shape-d100mm` und
`n8-shape-d100mm`, Geometrieauditsets[3]/sets[9]. Tatsächliche exportierte
kartesische Fourierkoeffizienten aus den gebundenen Rohsnapshots verwenden,
nicht die idealen Supportkoeffizienten als vermeintlichen realen Seed.
Der bei3334f1e geschlossene Feldstartaudit ist positive numerische Voraussetzung;
seine vier physischen Ablehnungen und alle früheren Fehlschläge bleiben bestehen.
Quellen, Protokoll, neue Implementierungen/Tests vor der realen Matrix committen.

Je Basis liefert die bereits gebundene`export_transfer`-Beweiskette Untergrenzen
v0 der Geschwindigkeit und S0 des orientierten Projektions-Kreuzprodukts sowie
Obergrenzenκ0 undL0. Zugehörige Support-/Exportidentität und einfache streng
konvexe Seedprojektion mit Tangenten-Drehindexbetrag1 sind Voraussetzung, keine aus einer
booleschen Gesamtmeldung erfundene Annahme. Für die Basis gilt mitα=−2πt die
Orientierungsnormale+e_phi; im (R,Z)-Bild läuft die Kurve mit Tangenten-Drehindex−1.
S bedeutet ausdrücklichn·(γ′×γ″) für diese feste orientierte Einheitsnormale.
Gemeint ist der Drehindex der Projektionstangente, nicht eine Umlaufzahl um
einen willkürlich gewählten Punkt.
Alle physischen Kopien nach benannter Rotation/Flip-Abbildung rekonstruieren.
Orthogonale Symmetrieabbildung und Kreuzproduktorientierung explizit prüfen.
Kanonisch`C_physical = matrix.T @ C_base`; die gespeicherten Flipmatrizen
haben Determinante+1. Normale entsprechend transformieren. Rundungsfehler der
Symmetriematrizen mitpolstern; direkte physische Differenzkoeffizienten dürfen
statt einer stillschweigend exakt rotationsinvarianten Gleitkommaschranke dienen.

Abstandsbasis: je physischer Spule und jedem Target das Minimum der vorhandenen
kontinuierlichen Untergrenzen über alle drei registrierten direkten Raster;
je physischem Spulenpaar entsprechend das Minimum über alle sechs Target-/Raster-
Berichte. Konservativ alle bereits verlangten Prüfungen berücksichtigen, nicht
nach einer späteren Kandidatensichtung das günstigste Zertifikat auswählen.
Keine gesampelten Minimalabstände als kontinuierliche Untergrenzen einsetzen.
Zusätzlich die gespeicherten analytischen CP-Untergrenzen je Basis und die
analytische globale CC-Untergrenze übertragen und getrennt verlangen. Der neue
Schirm ersetzt keine zuvor vorgeschriebene Distanzprüfung durch ein günstigeres
Zertifikat. Diese physische Distanzübertragung fordert ausdrücklich nicht den
alten Enclosure-Rundungsslack oder unveränderte Planarität des Kandidaten.

## Mathematische Kandidatenschranken

Kandidat und Seed haben exakt gleiche benannte DOFs, Form, Fourierordnung und
Symmetrieklasse. Mitδc=c−c_seed gilt für jede kartesische Achse:

```
a_m = hypot(δs_m, δc_m), omega_m = 2*pi*m
u0 = abs(δc0) + sum(a_m)
u1 = sum(omega_m*a_m)
u2 = sum(omega_m**2*a_m)
Dk = norm(uk)     (k=0,1,2)
```

Diese Schranken gelten für sämtliche t und sämtliche homotopen Zustände
c_seed+λδc,0≤λ≤1. Ableitungen sind nach t∈[0,1], nicht Winkel/Bogenlänge;
die Faktoren2π dürfen nicht fehlen. V0,A0 sind unabhängige Fourier-Suprema der
ersten/zweiten Ableitung des tatsächlichen Seeds. Je physischer Kurve:

```
v_lower = v0 - D1
E = D1*A0 + V0*D2 + D1*D2
S_lower = S0 - E
kappa_upper = kappa0*(v0/v_lower)**3 + E/v_lower**3
L_upper = L0 + D1
CP_lower(target,i) = CP0(target,i) - D0_i
CC_lower(i,j) = CC0(i,j) - D0_i - D0_j
```

Streng positivev_lower/S_lower sind notwendig. Die Krümmungsabschätzung nutzt,
dassv/(v−D1) fürv>D1 fällt. S_lower>0 sichert reguläre positive orientierte
Projektion entlang der gesamten Homotopie. Zusammen mit dem Seed-Tangenten-Drehindex1
bleibt diese Projektion einfach/streng konvex und damit die Raumkurve selbst
schnittfrei. Positives Kreuzprodukt an endlich vielen Punkten allein wäre
kein solcher Beweis. Keine Übertragung auf endliche Wicklungspakete.

Für Gleitkommaarbeit vor Summen auf den **Betrag** jeder Koeffizientenänderung
p=128*eps*max(1,maxabs(seed),maxabs(candidate)) addieren: Konstanttermabs(δc0)+p,
a_m=hypot(abs(δs_m)+p,abs(δc_m)+p). Nichtδc+p, das negative Beträge verkleinern
könnte. DarausDk ableiten. V0/A0 analog auf den Beträgen der Seedkoeffizienten
nach außen polstern, mit dem Maßstabmax(1,maxabs(seed)).
An jedem finalen skalaren unteren/oberen Ausdruck zusätzlich
128*eps*max(1,Summe der Beträge seiner Terme) abziehen/addieren; Größen dabei
jeweils in der angegebenen SI-/t-Darstellung behandeln. Keine behauptete
gerichtete Intervallarithmetik. Einzelne Kurven/Paare nicht durch globale
Mittelwerte ersetzen. Nichtfinite Werte oder unsichere Division liefern explizit
`uncertified`, niemals einen Nullkosten-/Zulässigkeitspass.
Bei v_lower≤0 wird insbesondere keine Krümmungsdivision ausgeführt; ihre
abgeleitete Obergrenze bleibt mit Grund`not_available` erhalten. D0/D1/D2 und
alle sonst wohldefinierten Größen trotzdem prüfen, negative Zertifikate nicht
als Ausführungsfehler oder ausgelassene Matrixzelle behandeln.

Alle physischen Grenzen unverändert: L≤3,5m,κ≤12/m,CC≥0,06m,CP≥0,08m;
Regulärität/Projektionsbeweis zusätzlich. Bezugsseed bleibt immer derselbe.
Kein Verbrauchsreset an einem akzeptierten Zwischenzustand. Unterschiedliche
schwache Schranken dürfen einen Kandidaten ablehnen, ohne eine reale Verletzung
zu beweisen. Flags für Rechenvollständigkeit/Zertifizierung getrennt halten.

## Synthetische Qualifikation

Additive Konstruktion und eigenständige Abnahme, keine Änderung der eingefrorenen
alten Geometrie-/Feldkerne. Analytische Kreise, Translation, gemeinsame orthogonale
Rotation, einzelne hohe Fouriermode und Änderungen mit bekannten ersten/zweiten
Ableitungen;1-ULP/Nulländerung, Form-/Namens-/Quellenmutation, nichtfinite/degenerierte
Eingaben und fehlende Provenienz. Kontrollen müssen unsichere Geschwindigkeit,
Krümmung, CP/CC/Länge und fehlende einfache Seedprojektion ablehnen.
Ein doppelt durchlaufener Kreis mit positivem Kreuzprodukt darf nicht als
einfacher zulässiger Seed akzeptiert werden. Eine Folge kleiner Änderungen muss
denselben kumulativen Endschirm wie der direkte Schritt erhalten.

Direkte eigenständige Fourierauswertung kontrolliert die D0/D1/D2- und
Krümmungs-/Projektionsschranken. Für gleiche skalare Rechnungen relativ≤5e-12
oder absolut≤1e-12; jede boolesche Klassifikation exakt. Kein numerischer
Vergleich ersetzt die dokumentierte mathematische Beweiskette. Alle bisherigen
Regressionen, Dokumentprüfung/Ruff/Diff vor Implementierungscommit ausführen.

## Feste reale, ausschließlich geometrische Matrix

Pro Klasse26 Zustände: Seed,24 signierte Probes, Seed-repeat. Drei Richtungen
in vollständiger benannter Koeffizientenordnung:

1. sin(k+1)/(1+m²)², k=0,...,ndof−1; m der Fouriermode, m=0 für den Konstantterm.
2. cos(k+1)/(1+m²)², gleiche Ordnung.
3. Nur z-sin(M) der Grundspule0 ungleich null.

Jede Richtung mit der **ungepolsterten** D0-Formel so normieren, dass das Maximum
über Grundspulen1 beträgt. Radii exakt1e-5,1e-4,1e-3,0,03m; jeweils+ und−.
Reihenfolge Richtung, Radius, Vorzeichen+ vor−. Keine Wahl nach Kandidatensichtung.
Jeden Zustand zweimal identisch zertifizieren; Seed-repeat zusätzlich mit
bitgleichen Ausgangskoeffizienten. Insgesamt52 Zustände/104 Zertifikatsaufrufe.
Die mathematische konservative Annahme/Ablehnung aller Probes ist Ergebnis,
keine pauschale Pflicht zu52 Geometriepässen.

Unabhängige Geometrie-Stichproben je Zustand bei256/512/1024 Kurvenpunkten,
bei1024 zusätzlich um halbe Kurvenzelle versetzt. Sämtliche physischen Kopien,
direkte Ableitungs-/Krümmungs-/orientierte Projektionswerte sowie alle Spulenpaare.
Plasma-Punktabstände zusätzlich auf beiden unveränderten vollen256²-Torusflächen.
Flächen einmalig binden, vollständige KDTree-Abfragen mitworkers1; Minimumzeugen
und Abstandsvektoren statt dichter1024×65536-Distanzmatrizen speichern.
Alle analytischen Schranken müssen die jeweiligen Punktwerte einschließen;
für Längen numerische Integrale nur als Kontrolle der Differenzabschätzung
gegen denselben Seedrasterwert, nicht als exakter Nachweis eines kontinuierlichen
Integrals behandeln. Keine nachträgliche feinere Auswahl eines guten Probes.

Gesamtpass der Qualifikation verlangt Quellen-/Formel-/Wiederholungs-/Präfix-
identität, alle direkten Einschließungen, beide Seeds sowie sämtliche zwölf
signierten kleinsten1e-5-Probes zertifiziert. Falls das scheitert: konservatives
Orakel nicht in eine Suche übernehmen; Ursache dokumentieren, keine Grenze lockern.
Andere Probes dürfen `uncertified` sein; kein Beweis physischer Unzulässigkeit.

## Ressourcen und Abschluss

Zwei Klassen seriell, je ein frischer Prozess/ein Thread, höchstens1800s ab
Workerstart einschließlich Import/Binder, Elternpoll0,5s/Terminierungsfrist5s.
Jeden Versuch vor Berechnung persistieren, letzter erfolgreicher Checkpoint
bleibt bei Fehler/IO/Timeout erhalten. Gesamter neuer Rohdatenumfang geschätzt
≤0,5GiB; mindestens3GiB vor jeder Klasse/2GiB laufend. Keine schweren Paralleljobs,
keine Installationen und keine Änderungen externer Quellen.

Keine nativen B/A-/Feld-VJPs, Gleichgewichte, Suchaufrufe oder neuen LPs.
Direkte geometrische Arbeit separat zählen:52 Zustände,208 Kontrollraster und
jeweils alle Kopien/Paare/beide Plasmaziele; unabhängige Abnahme separat berichten.
Die104 Zertifikatsaufrufe enthalten Repeats; die208 direkten Raster werden nur
einmal je Zustand ausgewertet, nicht stillschweigend für jeden Repeat erneut.
Alle Ergebnisse und Negativbefunde unverändert speichern, unabhängig abnehmen,
dokumentieren und committen. Erst danach das genaue Feldsuchprotokoll registrieren.
`search_allowed`, `field_pass`, `transfer_pass`, `step4_pass` hier immer false.
