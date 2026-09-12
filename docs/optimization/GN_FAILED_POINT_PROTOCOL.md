# Isolierte Diagnose des gespeicherten GN-Fehlerpunkts — 2026-09-12

Vor neuen physikalischen Auswertungen festgelegt. Ein einziger unveränderter
Fehlerpunkt aus dem bestandenen Präfix-Replay, keine Optimierung.

1. Fehlgeschlagenes Feld frisch deserialisieren. Alle 207 Parameter explizit nach
   physikalischen Besitzern abbilden; Array/Datei/Parameterhash prüfen. Unveränderte
   Fläche 32x32, 16 Spulen mit Quadratur 200, Roh-Flux/1e-6.
2. Native Feldprojektion z_native, gebündelte Projektion z_batch und vollständige
   gebündelte Matrix D erneut berechnen. Native skalare Vollgitter-VJP und jede
   native Einzelpunkt-Matrixzeile getrennt berechnen. Den Feldpunktzustand prüfen.
3. Beide Gradienten D.T*z_native/1e-6 und D.T*z_batch/1e-6 gegen native Vollgitter-
   VJP und gespeicherten Fehlergradienten vergleichen. Auch den Beitrag
   D.T*(z_batch-z_native)/1e-6 ausweisen. Nach der Einzelpunktprüfung die native
   Vollgitterauswertung erneut ausführen, um Zustandseffekte sichtbar zu machen.
4. Für **alle drei** freien Stromparameter die Feldableitung zusätzlich durch
   zentrale Feldwertdifferenzen bei h=1 und h=0.5 prüfen. Bei fester Geometrie ist
   das Feld affin in diesen Parametern; diese Kontrolle hat keinen klassischen
   Differenzen-Abschneidefehler. Sie ist keine zulässige Stromkonfiguration und
   kein Entwurf. Nicht die fast gleichen skalaren Fluxwerte subtrahieren.
5. Eine feste Geometrierichtung (Seed 51, Stromkomponenten null, normiert in der
   ursprünglichen Fehlerpunktbasis), zentrale Feldwertdifferenzen h=1e-4,1e-5,1e-6.
   Alle Stufen bleiben erhalten. Zum Schluss unveränderten Ausgangspunkt herstellen.

Alle normierten Abweichungen und Komponenten speichern, nicht nur ein Flag.
Unveränderte 1e-10-Grenze für neue Feld-/Matrix-/Gradientidentitäten; feinste
Geometrierichtung <=1e-6. Relativer Roh-Flux-Replay <=1e-10, Parameter exakt.
Historische Fehlerflags werden nicht umgeschrieben. Abweichungen alter und frischer
Routen sind Diagnoseergebnisse, kein Grund für nachträgliche Grenzwertänderungen.

Roharrays enthalten beide Projektionen/Matrizen, native volle Gradienten vor/nach
der Einzelpunktprüfung, Stromdifferenzen und Geometrieproben. Anfragen, verwendete
Quellen und Eingänge gehasht dokumentieren. Erst nach dieser Diagnose eine
gezielte Korrektur vornehmen und separat qualifizieren; kein weiterer Suchlauf
ist durch diesen Diagnoseauftrag freigegeben.
