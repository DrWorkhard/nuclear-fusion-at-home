# Geometriegeschützter Feldfit: registrierter Pilot

**Unqualifizierter Entwurf, begonnen am2026-09-20; pausiert am2026-09-23.**
Die Arbeit wurde vor Softwarequalifikation und Protokollcommit unterbrochen.
Kein neuer Feldfit wurde ausgeführt. Der reine Solverentwurf ist ohne seine
noch fehlenden Tests/Runner/Auditor erhalten, nicht zur Forschung freigegeben.
Die öffentliche Mitwirkungsbasis hat nun Vorrang; Zahlen unten sind geplante,
nicht ausgeführte Budgets. Ausgangspunkt ist die
abgeschlossene [kumulative Geometriequalifikation](../geometry/COIL_PERTURBATION_RESULTS.md).
Dies ist ein begrenzter neuer Versuch für4A, kein Abschluss von Schritt4.

## Frage und unveränderliche Quellen

Kann ein deterministischer Niederfrequenz-Abstieg den Feldfit verbessern, während
jeder feldberechnete Vorschlag das kumulative kontinuierliche Geometriezertifikat
gegen den ursprünglichen Seed besteht? Eine konservative Ablehnung ist kein Beweis
physischer Unzulässigkeit oder eines geometrischen Optimums.

Genau acht Zellen, Reihenfolge Referenz/ausgewählter Schritt3-Entwurf × n6/M5,
n8/M7 × N/V. Seeds, beide401-Vakuumtargets, volle benannte kartesische Koeffizienten,
Symmetrien, gemeinsame flusseliminierte Ströme, feste B²-Normierung und JN/JV-
Zielfunktionen samt Geometriestrafen stammen unverändert aus dem
[Feldstartprotokoll](CLEAR_COIL_FIELD_START_PROTOCOL.md). Voraussetzung sind dessen
numerischer Pass und alle vier erhaltenen physischen Ablehnungen sowie die
vollständige52-Zustände-Geometriequalifikation an c60aed7. Deren kanonischer Audit
hat SHA2569f8fd9a0c4ca1f93baa3b8896f803e1f1a3a6ae8cd409517abe5a24fda98c7e8.
Keine neuen Gleichgewichte, LPs, freie Einzelströme oder Zieländerungen.

## Konstruktion: exakt festgelegter Algorithmus

- Nur m≤2 einschließlich Translation sind aktiv:90/120 Koordinaten. Alle höheren
  Seedkoeffizienten bleiben bitgleich erhalten; keine native DOF-Fixierung, keine
  Änderung der vollen benannten Gradientenabbildung.
- Für jede aktive Koordinate ist P=(1+m²)^−2, sonst0. Die Richtung −Pg wird durch
  ihr maximales ungepolstertes Grundspulen-D0 dividiert: je Achse Betrag der
  Konstanten plus Summe der Sinus-/Kosinusamplituden, dann euklidische Achsennorm,
  Maximum über Grundspulen. Kein erneutes Quadrieren von P.
- Pro akzeptiertem Zustand Backtracking α=10^−3·2^−j Meter, j=0,…,15.
  Vor jedem Feldaufruf vollständiges kumulatives Zertifikat gegen denselben
  Originalseed, nie gegen den letzten akzeptierten Zustand. Abgelehnte Geometrie
  kostet einen Vorschlag, aber kein Feldbundle; keine künstlichen inf-/Nullgradienten.
- Akzeptanz nur bei Zertifikatspass, |I|≤500000A und
  J(x+αd)≤J(x)+10^−4 α gᵀd. Nach Akzeptanz erneut mit1mm starten.
  Nichtfinite Werte/native Fehler stoppen die Zelle. Nullrichtung, erschöpftes
  Vorschlags-/Feldbudget oder16 erfolglose Stufen werden getrennt berichtet,
  nicht als allgemeine Konvergenz bezeichnet.
- Auswahl kleinster eigener J ausschließlich unter akzeptierten Suchzuständen
  einschließlich Suchseed; bei Gleichstand zuerst gesehener Zustand. FD-Punkte
  und abgelehnte Trials können nicht gewinnen. N/V-J sind keine gemeinsame
  Vergleichsmetrik. Über alle Zustände unveränderte absolute Geometriegrenzen.

## Qualifikation, exakte Budgets und Replay

Vor Suche zehn neue Vollbundles: Seed, zwei deterministische Richtungen mit
sin(k+1) beziehungsweise cos(k+1), multipliziert mit S=(1+m²)^−1 für m≤2,
sonst0, euklidisch normiert; je h=10^−5 und5·10^−6 beide Vorzeichen; Seedrepeat.
Probes werden auf aktiven Indizes gebildet und vor dem Feld zertifiziert.
Zentrale FD-Abweichung≤2·10^−4 relativ ODER≤10^−8 absolut. Relativnenner
max(|analytisch|,|FD|,10^−30). Seed/Repeat exakt; ursprüngliche gebundene
Startupwerte, Gradienten und Arrays ebenfalls exakt reproduzieren.

Je Zelle maximal32 vollständige Bundles insgesamt:10 Startup +1 frischer
Suchseed +20 zertifizierte Feldtrials +1 Replay des ausgewählten Zustands mit
frischem Modell. Maximal128 Zertifikate:10+1+116 Vorschläge+1 Replay.
Unverbrauchte Reserven werden nicht auf andere Zellen übertragen. Vor jedem
Vollbundle den Modellcache explizit invalidieren; jeweils6 Werte und3 VJPs,
zusätzlich genau1 initiales Schleifen-A pro frischem Modell. Damit maximal290
native Requests pro Konstruktionszelle und2320 insgesamt. Der abschließende
Replay ist **keine Wiederholung des gesamten Suchpfads**.

Modellkonstruktion immer am unveränderten Geometrieseed; anschließend kanonische
x-Zuweisung und eingefrorener Archiv-Innenzieladapter. Kein veränderter Kandidat
wird als ursprünglicher Geometrieseed ausgegeben. Daten, Koeffizienten, voller
Gradient, Metriken, Supplement-B/A und Zertifikat jedes Vollbundles speichern.
Jeden Geometrievorschlag samt Richtung, Schritt, Vorgänger, Zertifikat und
Entscheidung speichern. Native Requests vor Dispatch und nach Ergebnis loggen.
Immutable Zustandsbelege/Checkpoints; Live-Fortschritt nicht als unveränderliche
Referenz einbetten. Auf IO-/Wächterfehler letzten erfolgreichen Präfix erhalten.

## Unabhängige Prüfung und unveränderte Endgates

Zwei ausdrücklich getrennte Phasen, jeweils qualifizierter und committeter Code
vor realer Ausführung:

1. Konstruktion plus gespeicherter unabhängiger Audit: Quellen-/Budget-/Ablauf-
   und Auswahlrekonstruktion, alle kumulativen Zertifikate unabhängig rechnen,
   alle Bundlewerte aus gespeicherten Arrays mit den qualifizierten unabhängigen
   Formeln nachrechnen, FD aus diesen Werten, exakter Seed-/Kandidatenreplay.
   Diese Phase allein erlaubt keinen fein geprüften Entwurfsgewinn.
2. Alle acht ausgewählten Zustände, auch Rückfallseeds, auf sämtlichen sechs
   bestehenden Feld-/Innenrastern und beiden vollständigen Flussblöcken prüfen.
   Vier direkte Geometrieraster des Perturbationsworkflows für beide Targets und
   alle physischen Paare, unabhängige Zertifikate und direkte64-Punkt-B/A-Prüfung.
   Strom des ausgewählten groben Snapshots einfrieren, keine feine Renormierung.
   Kein feiner Wert fließt in Konstruktion/Auswahl zurück.

Unverändert: Normal-RMS≤10^−4, Maximum≤10^−3, Innenvektor-RMS≤0,01,
|I|≤500kA, L≤3,5m, κ≤12/m, Spulenabstand≥60mm, Plasmaabstand≥80mm,
alle bisherigen Verfeinerungen (1% relativ ODER10^−7 absolut), sämtliche
Flussgates10^−6 relativ und direkten Feldgates5·10^−10 relativ.
Numerische Qualifikation, grober J-Abstieg, fein geprüfter lokaler Feldgewinn und
absolute physische Zulassung bleiben getrennte Ergebnisse. Keine nachträgliche
Lockerung der Grenzen. Kein QI-/Topologie-/Druck-/Orbit-/Ingenieur-/SoTA-Pass.

## Ressourcen und Abbruch

Serielle Ein-Thread-Zellen in frischen Prozessen, keine konkurrierenden schweren
Jobs.3GiB freier Platz vor jeder Zelle,2GiB laufend. Schätzung Konstruktion≤1GiB,
gesamter Pilot≤2GiB, keine Installation oder Kopie externer Checkouts. Je Zelle
1800s Gesamtzeit einschließlich Imports/Quellenbindung, zusätzlich600s Suchphase.
Die nachfolgende unabhängige Prüfung und feine Phase werden getrennt bilanziert;
die feine Phase benötigt maximal80 zusätzliche native Requests/Zelle einschließlich
acht Initialisierungen, zusammen maximal370/Zelle und2960 für den ganzen Piloten.
Keine versteckten Wiederholungen bei Fehlern. Ein negativer/abgebrochener Versuch
bleibt erhalten; sein Abschluss schließt weder4A noch Schritt4.

## Unabhängiges Methodenreview vor Daten

Zwei unabhängige interne Agenten prüfen Algorithmus, Normierung, Gates und
Bilanz; dies ist keine externe Begutachtung. Das erste Review empfiehlt den
obigen niedrigen Modenraum statt erneut freien L-BFGS-B und trennt den exakten
Kandidatenreplay von einer vollständigen Wiederholung. Zweites Review und
abgeschlossene Softwarequalifikation werden vor numerischem Start dokumentiert.
