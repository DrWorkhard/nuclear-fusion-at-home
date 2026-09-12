# Geometrische Krümmung: Spektral-/Projektionskontrollen vorbereitet

2026-09-12, [Protokoll](GEOMETRIC_CURVATURE_PROTOCOL.md) bei64972fa registriert.
Noch keine neue Feld-/Matrixrechnung an den tatsächlichen Spulen durchgeführt.

Additive Spektraldiagnose mit expliziten drei Stromspalten, vollständigem und
geometrischem Feld-Jacobian sowie rein linearisiertem Stromraumprojektor.
Alle Singulärwerte und numerischen Ränge bleiben erhalten; keine Richtungen
werden entfernt. Rangverlust/zu große Kondition des Stromblocks verhindern
die Stromprojektion, löschen aber nicht die bereits berechneten anderen Spektren.

Fünf analytische/negative Kontrollen bestehen: bekannte Projektionsanteile1/2
und4/5, genau verschwindender Tangentenvektor ohne erfundene Quote, explizite
Spaltenpermutation, Rangverlust, NaNs/ungültige Formen und überlaufende skalare
Projektionsstatistiken. Der Überlaufkontrollfall veranlasste eine zusätzliche
Finite-Prüfung auch der skalaren Ergebnisse vor echter Datenverwendung.
Ruff, Dokumentstruktur und Diffprüfung bestehen. Noch kein Konditionierungs-
oder Entwurfsbefund an den realen Daten.

Nächster Schritt: quellgebundene32-Ereignis-Feldwiedergabe, zwei vollständige
gebündelte/native Matrizengegenprüfungen und unabhängiger Vorhersage-/Spektralaudit.
