# Speicherbegrenzte native Abstandsreferenz: Folgestudie

19. September2026, vor Implementierung und neuen Messwerten registriert.
Vorgänger: [vollständige negative Ressourcenprüfung](CLEAR_COIL_FIELD_START_RESULTS.md)
bei97d75b8, numerischer Codea5a007c. Deren drei RAM-Fehler und`all_pass:false`
bleiben unverändert. Neues Ziel ist eine separat qualifizierte speicherbegrenzte
Referenzausführung, kein nachträglicher Pass der dichten Implementierung.
Keine neuen Projektfelder, Targets, Gleichgewichte oder Spulensuchen.

## Hypothese und unabhängige Reviews

Die native diskrete CP-Formel ist ein gewichteter Mittelwert über Kurven- und
Oberflächenpunkte. Wir zerlegen ausschließlich die Ausführung über die
Oberflächenpunkte, ohne deren Zahl oder physikalische Gewichte zu ändern.
Zwei unabhängige lesende Agentenreviews bestätigen den Faktor und die
Kovektorakkumulation. Sie verlangen synchrone Verarbeitung, genaue Arbeitszähler,
vollständige Abstände und neue Ressourcenmessung; die Laufzeit vieler kleiner
Kernel bleibt eine offene Frage. Keine externe Peer-Review.

## Quellen und vier feste neue Zellen

Genau n6/M5 und n8/M7 × Spulenquadratur256/512, je ein frischer Prozess.
Identischer synthetischer Torus, alle24/32 physischen Kurven, sämtliche128²
Flächenpunkte, Koordinaten, unnormierte Parameternormalen, Strafen0,08m CP und
0,06m CC sowie benannte DOFs wie im ursprünglichen Ressourcenlauf.

Die acht alten Worker sind vollständig und alle mathematischen Checks positiv;
alle vier Sparse-Worker bestehen einzeln auch Ressourcen und Prozessabschluss.
Vor neuen Läufen müssen diese Eigenschaften einzeln aus den gebundenen Daten
geprüft werden, ebenso alle168 alten Backendvergleiche. Nicht das negative alte
Gesamtflag überschreiben oder übergehen. Vollständige Quelldatenbindung an
`evidence/clear-coil-field-start-v1-resource.json`, SHA256
`5c77723ee9f77de7a4b176de3a69f06ccc6af6d22ad7a4572c2c631ea013acdf`;
historische Dateiidentität bei97d75b8. Alte native Python-/Binärbytes,
Python/NumPy/SciPy/JAX-Versionen sowie Sparse-Code und ursprünglicher
Ressourcenrunner müssen unverändert sein. Ein späterer Git-HEAD allein darf
zulässige additive Dateien/Dokumentation nicht als numerische Quelländerung
fehlklassifizieren. Keine neue unveränderte Sparse-Ausführung nötig.

## Additive native Blockformel

Originalfunktion`cs_distance_pure` aus dem unveränderten SIMSOPT-Checkout, nicht
die eigene Sparse-Formel als Referenz kopieren. Einmal je Worker stabile native
JAX-JIT-Funktionen für Wert und Ableitungen nach Position/Tangente erstellen;
float64 muss aktiv sein. Keine Closure-/JIT-Neuerzeugung pro Block.

Deterministische vollständige Partition der ursprünglichen flachen Fläche:
64 Blöcke mit Indizes[256b,256(b+1)),b=0..63. Alle physischen Kurven in originaler
Reihenfolge, kein Culling, Nachbarcap, Symmetriedivisor oder Auslassen leerer
Beiträge. Jeder native Blockwert und beide nativen Kovektoren werden mit
256/16384=1/64 gewichtet. Der native Blockkern enthält schon die Kurvenmittelung;
keine zusätzliche Division durch die Kurvenpunktzahl. Unnormierte Flächennormalen
unverändert übergeben. Erst vollständig blockweise summierte Orts-/Tangenten-
Kovektoren mittels nativer Kurven-VJPs in benannte Basisgradienten überführen.

Jeder Block muss synchron als Python-float oder unabhängiges NumPy-Array übernommen
werden. Keine Liste zurückgehaltener JAX-Outputs, kein vmap/Stack/Scan über die
ganze Fläche. Vollständiger Mindestabstand separat mit Nc×256-cdist-Blöcken und
globalem Minimum; kein alter dichter Mindestabstandsaufruf. Das größte
Differenzkoordinatenarray beiNc512 umfasst so3MiB statt192MiB; dies ist keine
Vorhersage des gesamten JAX-/CC-/Prozesspeaks. Nullgeschwindigkeit, Koinzidenz,
ungültige Formen oder nichtfinite Eingaben/Ergebnisse scheitern explizit.

## Feste Zustände und genaue Arbeit

Unverändert13 Zustände je Zelle: seed, acht zentrale Wertprobes in normierten
sin/cos-Richtungen mit1e-5/5e-6 und beiden Vorzeichen, seed-repeat,
coil[0]/xc(0)+0,002m, changed-repeat ohne erneutes Setzen der DOFs, restored-seed.
Für CP und CC jeweils13 J, fünf vollständige Gradienten an Nicht-Probes und
drei Mindestabstände an seed/changed/restored. Alle Rohgeometrien, Werte,
benannten Gradienten und Arbeitspräfixe speichern.

Für diese Referenz **keine Blockkernel-Cachegutschriften**: jeder CP-J-Request
führtP×64 native Werte aus, jeder CP-dJ-RequestP×64 Positions- undP×64 Tangenten-
Ableitungskerne, danachP Paare nativer Kurven-VJPs. Jeder CP-MindestabstandP×64
cdist-Blöcke. P=24/32. Je n6-Zelle19.968/7.680/7.680/4.608 Blockaufrufe
(J/Position/Tangente/Minimum), je n8-Zelle26.624/10.240/10.240/6.144;
120/160 Kurven-VJP-Paare. Reine Wertprobes dürfen keine Gradientenkerne ausführen.
CC bleibt die unveränderte native Implementierung. Wiederholungen zählen voll.

Jeder öffentliche Aufruf vor Start persistieren. Zusätzliche Kernelzähler vor
dem jeweiligen nativen Aufruf im Speicher erhöhen, nach synchroner Rückkehr
separaten Abschlusszähler erhöhen. Pro Kurven-/Phasenblock vorab konservative
Arbeitsreservierung und danach fertige Zähler persistieren; bei abgefangener
Exception aktuellen Teilzähler sichern. Bei hartem Abbruch gilt die letzte
persistierte Fertigzahl als Untergrenze und die ganze reservierte Arbeit als
Obergrenze, nicht als behauptet exakt erledigte Kernelzahl. Keine tausenden
Einzeldateien pro Kernel, kein Überschreiben erfolgreicher Rohzustände durch
Fehlermetadaten. Unvollständige Arbeit verhindert Annahme.

## Unveränderte Schirme und separate Abnahme

Vor realer Ressourcenmatrix kleine synthetische native/Sparse-/Blockkontrollen:
Wert, voller VJP, beide FD-Schrittweiten, aktive/Nullfälle, ungleiche Kurvenraster,
komplette Partition, feste Gewichtung, DOF-Änderung/Wiederherstellung, exakte
Arbeitszähler und injizierte Fehler. Keine kleinen Tests als Vollgrößenpass.

Jede neue Zelle vergleicht sämtliche13 Zustände mit **beiden** alten Backends:
genaue Identität von Oberflächen-/Kurvenrohdaten, DOF-Namen und Zustandsreihenfolge;
Werte, fünf Gradienten und drei Mindestabstände mit unverändertem komponentenweisen
Schirm relativ≤5e-10 oder absolut≤1e-12. Je42 Vergleiche zu jeder alten Seite,
336 insgesamt. Eigene acht FD-Prüfungen pro Zelle: relativ≤2e-4 oder absolut≤1e-8.
Alle vier neuen und acht alten Zustandsreihen vollständig; kein günstigster Vergleich.
Innerhalb jedes neuen Backends exakte Wiederholungen/Restore und vier geänderte
Symmetriekopien bei Basisänderung. Keine Bitgleichheit unterschiedlich geordneter
Backend-Summierungen fordern oder nach Beobachtung verlangen/erlassen.

Je frischem Worker unverändert120s Elternzeit ab Start,0,5s Poll/5s
Terminierungsfrist und gemessener Peak-RSS≤1,5GiB; exakter int-Prozesscode0,
endliche nichtnegative Zeiten, rechtzeitige Abschlussmarke und Quellidentität
nötig. Alle vier Zellen seriell und mit bisherigen Ein-Thread-Einstellungen.
Keine schweren parallelen Tests. Platte vor jeder Zelle≥3GiB, laufend≥2GiB;
neue Rohdaten geschätzt≤100MiB, keine Installationen/Downloads.

Separates`bounded_reference_pass` verlangt sämtliche Quellen-, Mathematik-,
Wiederholungs-, Arbeits- und neuen Ressourcenschirme aller vier Zellen sowie
die vier unveränderten alten Sparse-Pässe. Alte drei Dense-Fails bleiben false.
`startup_pass`,`physical_seed_pass`,`search_allowed`,`transfer_pass`,`step4_pass`
bleiben hier stets false. Erst nach bestandenem, dokumentiertem und committedem
Folgeversuch kann der noch fehlende Gesamtworkflow der Feldstartstudie
implementiert/qualifiziert werden. Kein direkter Sprung zu Projekt-Feldwerten.

Protokoll committen → additive Implementierung synthetisch prüfen/committen →
vier frische Läufe → separate gespeicherte Abnahme → Ergebnis dokumentieren/committen.
