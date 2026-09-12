# Frische QI-Gleichgewichte: radiale und Winkel-Auflösung

Vor neuer Rechnung registriert, 2026-09-12. Ziel: prüfen, ob die begrenzte
Clebsch-Inkonsistenz bei kontrollierter numerischer Auflösung in frisch berechneten
Gleichgewichten kleiner wird. Kein eigener Plasmaentwurf, keine exakte historische
VMEC9.0-Reproduktion, keine automatische absolute Drift-/QI-Freigabe.

## Festgelegte Eingaben und Matrix

Alle vier unveränderten Autoren-Eingaben der hashgebundenen
`evidence/qi-producer-inventory-v1.json`, in dessen Reihenfolge. Unveränderte
RBC/ZBS-Randform, nfp, Symmetrie, mpol/ntor, Fluss, Druck-/Stromprofile und sonstige
physikalische Eingaben. Keine datengetriebene Auswahl günstiger Fälle.

Je Fall vier frische Kaltstarts: `(ns=201, Winkel=1)`, `(401,1)`, `(201,2)`, `(401,2)`.
Winkel1: explizit `ntheta=2*mpol+6`, `nzeta=2*ntor+4`; Winkel2 verdoppelt beide.
Geometrische Fourierbasis unverändert, nicht als vollständige mpol/ntor-
Konvergenzstudie bezeichnen. Radialfolge `[12,25,51,101,201]`, für401 um401
ergänzen. Toleranzfolge `[1e-8,1e-10,1e-11,1e-12,1e-12]`, für401 um1e-12
ergänzen; maximal10000 Iterationen je Stufe. Abweichende numerische Kontrollen
gegenüber den historischen1e-16-Eingaben explizit speichern, keine Gleichsetzung.

Installiertes, unverändertes VMEC++0.7.3 aus seiner getrennten Umgebung,
`iteration_style=vmec_8_52`, ein Thread. Quellen/Binärdatei/Lockfile binden.
Keine Restarts aus anderen Matrixzellen, keine stille Fallback-Steuerung.
Pro Zelle maximal1800 Sekunden; fehlende Konvergenz/Timeout/Fehler aufbewahren,
übrige Zellen trotzdem versuchen, solange Ressourcen sicher sind. Eine Zelle
gilt erst mit allen drei endlichen Residuen<=1e-12 und korrekten Dimensionen als
numerisch konvergiert. Erfolgsflag allein genügt nicht.

## Auswertung und unabhängige Prüfung

Eingabekonversion unabhängig gegen Autoren-Namelist und Wout-Randkoeffizienten
prüfen (normierte Toleranz1e-12, Strom/Druck/Fluss und m/n-Zuordnung erhalten).
Jeden effektiven Solverinput vor Ausführung speichern; nur deklarierte numerische
Änderungen zulassen. Alle16 Matrixzellen vollständig in der Bilanz behalten.

Für alle konvergierten Wouts s=0,25/0,5/0,75, Winkelgitter64/128 auswerten:
dieselben signierten Clebsch-Vektor-/Betrags-/Komponentenidentitäten und negativen
Vorzeichen-/2pi-Kontrollen wie zuvor, unveränderte1e-3-Physikschirme. Getrennte
allgemeine Auswertung additiv implementieren, alten16/32-Kernel nicht ändern.
Vor Nutzung dessen24 archivierte16/32-Gitter mit normierter Abweichung<=1e-12
reproduzieren. Gemeinsame64/128-Punktwerte<=1e-12 und Differenz der vier
physikalischen normierten Fehler<=1e-5 verlangen. Alle Stufen speichern.

Separater Auditor liest neue Wouts/Arrays und überprüft Eingaben, Residuen,
Gitter, Komponenten-/Vektorfehler und Klassifikation. Er verwendet nicht den
neuen Produzenten für die arithmetische Gegenprüfung. Auswertungsfehler stoppen
die Freigabe, negative physikalische Ergebnisse werden nicht ausgesondert.

Alte und neue Felder zusätzlich bei gleichem s und Winkel128 vergleichen:
R/Z-Tangenten, |B| und iota sowie Gesamtvolumen berichten; relative Feld-/Geometrie-
und Volumenabweichung<=1e-3, absolute iota-Abweichung<=1e-3 als begrenzter
Fidelitätsschirm. Kein Beweis historischer Bitgleichheit. Radiale und Winkel-
Änderungen getrennt aus der vollständigen2x2-Matrix ablesen; keine pauschale
Ursachenzuschreibung bei gemischten Ergebnissen. Alte19/24 bleiben unverändert.

## Ressourcen und Abschluss

Geschätzt unter1GiB zusätzliche Wouts/Punktarrays, keine Installation/keinBuild.
Mindestens3GiB freier Platz vor Start und2GiB laufend überwachte Reserve; keine
parallele schwere Optimierung. Studienbericht nach jeder Zelle atomar speichern.
Vorläufige Konvergenz ist kein Drift-, Maximum-J- oder Schritt1-Zertifikat.
Ergebnisse/Gegenprüfungen samt Fehlern dokumentieren und committen, bevor eine
weitere Physikstudie begonnen wird.
