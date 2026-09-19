# Feldstarts aus geometrisch angenommenen Konturen: Arbeitsstand

19. September2026. [Protokoll](CLEAR_COIL_FIELD_START_PROTOCOL.md).

Geometriestudie bei323cfdd vollständig geschlossen: alle zwölf Varianten
angenommen, n6/n8-shape-d100mm ausgewählt. Jetzt getrennte numerische
Feldstart-/Auflösungsqualifikation vor jeder weiteren Suche. Noch keine neuen
Target-Feldwerte, keine optimierten Kandidaten und kein Schritt4-Abschluss.

Zwei getrennte lesende Agentenreviews identifizieren dieselben Integrationsfallen:
der alte Konstruktor legt Startkoeffizienten und Flussorientierung bereits an
seinen Kreisen fest; seine Geometriefläche bleibt hart64×32. Auch Gesamtprüfung,
Initialisierungszählung und Flussraster sind nicht durch Umetikettieren übertragbar.
Deshalb additive Klasse mit echtem Geometrieseed vor dem ersten Feldaufruf,
neuem Binder/Workflow/Gesamtaudit und unveränderten alten numerischen Dateien.

Gewählt wird die begrenzte Sechs-Stufen-Prüfung je vier physischer Zellen;
N/V erhalten getrennte zehnteilige Ableitungsqualifikation. Ein Vorschlag für
Innenraster128² bleibt bewusst außerhalb: dafür fehlt hier ein entsprechend
qualifiziertes Targetarchiv. Kein stiller neuer QI-Qualifikationszweig. Beide
Reviewer bestätigen den engeren Startupumfang; spätere Suchpunkte brauchen
ihre eigene feinere unabhängige Abnahme. Strom und archivierter64²-B²-Maßstab
bleiben während sämtlicher Auflösungsprüfungen fest.

Native aktive CP-Strafen erzeugen dichte Paararrays. Schon256×128² benötigt
etwa101MB nur für Differenzkoordinaten einer aktiven Kurve, zuzüglich Distanz,
Gewicht und Ableitungstemporaries; sichere Starts würden diesen Pfad auslassen.
Ein mathematisch identischer KDTree-/punktweise ausgewerteter Adapter begrenzt
den Speicher. Vor Einsatz vollständige aktive24/32-Spulen-Kontrollen bei beiden
registrierten Spulenauflösungen, einschließlich nativer Werte/VJPs, Differenzen,
Peak-Speicher und Zeit. Der zusätzliche algebraische Review bestätigt beide
Kovektoren ohne Faktor1/2 oder Symmetriedivisor. Flächengewicht muss der Betrag
der unnormierten nativen Parameternormalen sein, nicht unitnormal oder auf Summe1
normiertes Gewicht; Nenner je KurveN_curve*N_surface. Dieser rohe Integralterm
hat wie die native Implementierung die SI-Dimensionm^5, bevor die festgehaltenen
Strafgewichte angewandt werden. Synthetische Implementierungsprüfung bleibt nötig.
Reviewpräzisierung vor Code: nur den Suchradius konservativ polstern, danach
den ursprünglichen Hinge exakt anwenden; deterministische Nachbarreihenfolge,
unveränderliche feste Flächendaten und vollständiger Mindestabstand auch bei
Nullstrafe. Keine fehlenden Flächenableitungen als Co-Designgradient ausgeben.

Nächster Schritt nach Protokoll-Commit: additive Implementierung und synthetische
Qualifikation. Noch kein neuer Start numerisch angenommen oder Feldfit gestartet.
