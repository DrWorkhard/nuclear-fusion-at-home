# Feinster Netzfall: getrennte vollständige Wiederholung mit Präfixnachweis

Vor neuer räumlicher Rechnung registriert, 2026-09-12. Der abgeschlossene
[sechs-Netze-Versuch](MESH_NONLOCAL_RESULTS.md) bleibt mit seinem feinsten
Paarcap negativ. Als einzigen neuen Zielgegenstand das dort unvollständige,
unveränderte h=0,010-Netz wählen; keine nach Ergebnissen ausgesuchte Geometrie.

Neue separate Studie `mesh-fine-completion-v1`, kein Überschreiben des v2-Scans.
Dasselbe327000-Tetraeder-Netz, dieselben vier Tags, gleiche Originalvertices,
Blattgröße16, Boxpolster, Trenn-/Innenpunktkern und alle physikalischen Grenzen.
Feste Obergrenze **4000000 SAT-Aufrufe und1200s** für eine vollständige neue
Traversierung;3GiB Startreserve,2GiB laufend. Grobe Ressourcenabschätzung aus
dem geschlossenen274s/2M-Präfix: selbst4M sollten unter1200s liegen, ohne
Zusicherung linearer Laufzeit oder eines Erfolgs. Zusätzliche Rohdaten<300MiB
abschätzen und laufend überwachen. Alle neuen Aufrufe zusätzlich zählen,
nicht als kostenlose Fortsetzung ausgeben.

Der neue vollständige Lauf muss sämtliche alten2M zeilenweise gespeicherten
Trennnachweise in identischer Reihenfolge/mit identischen Zahlen reproduzieren.
Indexpermutation, Knotenboxen und alle alten Traversierungsereignisse müssen
ebenfalls ein exaktes Präfix bilden. Ein Cap/Fehler oder Präfixunterschied bleibt
negativ, auch falls ein anderer Teiltest besteht. Kein globales N²-Array anlegen.

Unabhängigen bestehenden Partition-/Witness-Auditor am vollständigen neuen
Zertifikat erneut ausführen; Originaldateien, alle Zähler und vollständige
N*(N-1)/2-Paarabdeckung prüfen. Alte fünf vollständige Pässe nur quellgebunden
referenzieren, nicht unnötig neu rechnen. Das feinste Netz besteht erst bei
vollständiger neuer Abdeckung, null unaufgelösten/positiven Innenpaaren und
bestandenem Präfix-/unabhängigem Audit.

Auch sechs vollständige Pässe beträfen nur Paare **ohne gemeinsame Vertexindizes**
der vier alten Grundspulen. Kein Nachweis für Nachbarpaare, komplette Symmetrie-
Baugruppen, echte Wicklungspakete oder Mechanik. Der magnetisch unzulässige
Netzquellentwurf wird nicht dadurch zugelassen. Erst nach Abschluss der aktiven
QI-Koordinatenstudie samt unabhängigem Audit starten, keine schwere Parallelrechnung.
