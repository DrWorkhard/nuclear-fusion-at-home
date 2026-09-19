# Nächster Feldfit: Geometrie erhalten oder nur nachträglich ablehnen?

19. September2026, nach dem numerisch positiven, physisch negativen
[Feldstartabschluss](CLEAR_COIL_FIELD_START_RESULTS.md) bei3334f1e.
Neue Methodenentscheidung innerhalb von Schritt4A, kein neuer Suchlauf.

## Befund und Entscheidung

Die neuen Startfelder sind zuverlässig gerechnet, aber Normal-RMS≈0,27 ist
rund2700-mal zu groß. Alle weichen Geometriestrafen sind am Start null.
Die konservativ über alle vorgeschriebenen Geometrieprüfungen berichtete
Plasmareserve beträgt nur etwa18,2–18,4mm über80mm. Die rund130mm gesampelten
Abstände sind keine entsprechende kontinuierliche Garantie. Eine Box von
±0,12m je Fourierkoeffizient begrenzt weder die tatsächliche Kurvenbewegung
auf12cm noch ihre erste/zweite Ableitung.

**Zunächst ein geometrisch abgesicherter lokaler Formfit.** Davor ein neues
[kumulatives Perturbationszertifikat](../geometry/COIL_PERTURBATION_PROTOCOL.md)
synthetisch und an einer festen feldfreien Matrix qualifizieren. Jeder spätere
Suchvorschlag muss gegen denselben unveränderten angenommenen Seed zertifiziert
werden; nur kleine Änderungen gegen den letzten Zustand zu prüfen wäre falsch.
Keine bloße Vererbung des alten Geometriepasses an veränderte Fourierkoeffizienten.

Diese Entscheidung bevorzugt im nächsten kurzen Versuch belastbaren zulässigen
Fortschritt, nicht maximale freie Suchweite oder einen beanspruchten Methodensieg.
Ist die konservative Hülle zu eng, heißt der Befund **zertifikatslimitiert**,
nicht konvergiert, optimal oder physikalisch unmöglich. Vor tatsächlicher Suche
werden Algorithmus, Budgets, Auswahl und feinere Ergebnisgates separat registriert.

## Zwei unabhängige lesende Reviews

Beide Agenten prüfen dieselben abgeschlossenen Quellen mit getrenntem Auftrag,
ohne neue Feldrechnungen oder Codeänderungen. Danach werden die unterschiedlichen
Empfehlungen gegenübergestellt. Interner Agentenreview, keine externe Peer-Review.

| Option | Review A (`coil_pilot_validator`) | Review B (`coil_pilot_auditor`) | Entscheidung |
| --- | --- | --- | --- |
| Freies L-BFGS-B, neue Starts/Raster | Eine8×128-Bundle-Kontrollrunde isoliert die behobene Initialisierungs-/Auflösungsproblematik; keine Geometriesicherheitsgarantie | Erneuter Geometrieverlust möglich, null Schutzgradient am Start, alte große Koeffizientenbox ungeeignet | Vergleichsoption erhalten, vorerst nicht ausführen |
| Harte kontinuierliche Geometrieschranke | Sinnvoller nächster Hebel bei Geometrieverlust; kein künstliches inf/Zerogradienten-Orakel in SciPy | Jetzt priorisieren; kurzer8-Zellen-Versuch mit höchstens32 Feldbundles/128 Geometrievorschlägen je Zelle | Zuerst Zertifikat qualifizieren, danach separaten kurzen Suchpilot registrieren |
| Glatte reduzierte Formrichtungen | Seed-Hochmoden einfrieren statt löschen; neue Skalierung/Kettenregel prüfen | Ableitungsgewichtung kontrolliert hochfrequente Krümmungsänderung; planare Supportfamilie als Kontrollarm | Skalierten Gradienten/Backtracking als einfache spätere Erstoption prüfen; kein heutiger Suchvertrag |
| Unabhängige Grundspulenströme | Ändert Serienkreis-/Hardwareklasse; gemeinsamer Zusatzstrom ist wegen Flussnormierung redundant | Feste Geometrie erlaubt separates beschränktes quadratisches Feldproblem | Getrennte spätere Architekturdiagnose, nicht mit dem Formfit vermischen |

Beide Reviews verlangen unveränderte gemeinsame physische Metriken für N/V;
unterschiedliche Gesamt-J dürfen keine Methodenrangfolge erzeugen. Alle gewählten
Kandidaten benötigen unabhängige feinere Felder/Flüsse und eigene Geometrieannahme.
Keine Seedzulassung aus niedrigem Optimierungswert; absolute Grenzen bleiben.

## Anforderungen an die neue Geometriesicherung

Aus der kumulativen Fourieränderung sind obere SchrankenD0,D1,D2 für Position,
Tangente und zweite Ableitung zu bilden, mit explizitem Einheitparameter t∈[0,1].
Abstände verlieren höchstensD0 beziehungsweiseD0i+D0j, Länge höchstensD1.
Krümmung und Selbstschnittfreiheit benötigen zusätzlich reguläre, strikt konvexe
Projektion während der ganzen geraden Koeffizientenhomotopie zum Seed.
Nur positives lokales Vorzeichen ohne erhaltene Windungszahl genügt nicht.

Die aktuelle Funktion`export_certificate` ist ausdrücklich **kein** Formänderungs-
Orakel:≤5e-12 Exportidentität und ungefähr1e-9 Enclosure-Slack schützen Rundung,
nicht einen neuen Entwurf. Die allgemeine alte Selbstnäheprüfung hat
`complete_self_proof:false`. Beide bleiben unverändert, ein neues Zertifikat
erhält eigene Quellen, Kandidatenidentität, Beweisannahmen und Negativtests.

Ein bestandener Perturbationsschirm betrifft glatte Filamentkurven und ihre
Abstände. Keine endlichen Wicklungspakete, Lasten, Fertigungsfehlerverteilung,
realisierten Flussflächen, Einschluss- oder Druckphysik daraus ableiten.
