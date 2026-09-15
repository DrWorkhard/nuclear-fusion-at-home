# Außenliegende Spulenstarts: Arbeitsstand

15. September2026. [Protokoll](CLEAR_COIL_INITIALIZATION_PROTOCOL.md).

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
Ein zweiter mathematischer Detailreview läuft noch; er muss vor Target-Auswertung
abgeschlossen sein. Der erste Protokollstand wird vor Implementierung committed;
eventuelle Präzisierungen erhalten ebenfalls einen Commit vor echten Daten.
