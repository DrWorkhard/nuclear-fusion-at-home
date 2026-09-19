# Außenliegende Spulenstarts: Arbeitsstand

19. September2026. [Protokoll](CLEAR_COIL_INITIALIZATION_PROTOCOL.md).

Der vorherige [vollständig negative Spulenpilot](../optimization/COUPLED_COIL_PILOT_RESULTS.md)
motiviert eine getrennte geometrische Studie: gleiche physische Grenzen, aber
Spulen um den tatsächlich wechselnden Plasmaquerschnitt statt feste Kreise umR=1.
Noch keine neue Target-Auswertung und keine Freigabe zur Magnetfeldoptimierung.

Entwurf: gemeinsames3D-Sicherheitsenvelope beider Plasmaränder, verschobene Kreise
und konvexe Fourierkonturen über eine bekannte Stützfunktionsdarstellung.
Zwölf feste Varianten; sämtliche Parameter, Coverradien, LP-Dualwerte und feinen
geometrischen Abnahmen sollen unabhängig reproduziert werden. Keine allgemeine
planare Spulenlösbarkeit, Feldqualität oder Schritt4-Behauptung.

Der unabhängige Integrationsreview findet nach Aufnahme der Orientierung und
kontinuierlichen Schutzschranken keinen Blocker für diesen begrenzten Versuch.
Der mathematische Detailreview bestätigt die Stützfunktions-/Krümmungs-/
Längen-/Paarabstandsformeln und das84+84-LP-Budget. Er verlangt zusätzlich
ein äußeres Rundungspolster für fast tangentiale Kugel-Ebenen-Schnitte.
Dieses ist am19. September vor realen Daten im Protokoll konkretisiert, ebenso
der explizite Frequenzfaktor in der rho-Lipschitzschranke, die unskalierte
LP-Dualabnahme und die Pflicht zu jeweils bestandenen analytischen **und** allen
direkten Abstandsschirmen. Keine geometrischen Grenzen oder Ergebnisse geändert.

Erste Protokollfassung bei`bda5d4a` committed. Die unterbrochene Implementierung
hat nur einen unqualifizierten Konstruktionsmodul-Entwurf hinterlassen;
kein realer Versuch lief im Hintergrund weiter. Fortsetzung mit synthetischen
Kontrollen, getrennter unabhängiger Prüfrechnung und geschützter Ausführung.
Eine konditionierungsbedingte Abweichung am strikten Rohdatenvergleich wäre
ein offener Arithmetiknachweis, keine physische Ablehnung oder Anlass zur
nachträglichen Grenzänderung. Noch keine neue Startfreigabe oder Feldsuche.
