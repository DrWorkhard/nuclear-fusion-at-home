# Ursache eingegrenzt: unterschiedliche Rundung der Feldprojektion

Datum 2026-09-12, Protokoll/Implementierung 51245f3. Evidenz:
`evidence/gn-failed-point-v1.json`. Keine Optimierung.

Die frische native skalare Ableitung ist **exakt gleich** der im fehlgeschlagenen
Lauf gespeicherten Ableitung und nach dem Einzelpunkt-/Strom-/Geometriereplay
unverändert. Der Befund spricht gegen einen zustandsabhängigen Cachefehler.

| Ableitungsweg gegen frische native Vollgitter-VJP | Maximale normierte Abweichung |
| --- | ---: |
| Gespeicherte native Ableitung | 0 |
| Gebündeltes D, dieselbe native Feldprojektion z | 3,603e-13 |
| Gebündeltes D, separat gebündelte Feldprojektion z | 1,638e-10 — alte Grenze verletzt |
| Native Einzelpunktmatrix, native Feldprojektion z | 1,304e-13 |

Die Matrixprüfung, beide affinen Feldwertdifferenzen für alle drei freien
Stromparameter und die feinste unabhängige Geometrierichtung bestehen. Die zwei
nahezu gleichen Feldprojektionen führen beim empfindlichen Gradientenprodukt
zu unterschiedlich großen Fehlern. Der vorherige quadratische Modelltest hatte
bereits die native Projektion verwendet; erst der neue Suchadapter benutzte
stattdessen die separat aufsummierte Projektion im Identitätsvergleich.

Gezielte Folgerung: Die Identitätsprüfung soll dieselbe native Feldprojektion
verwenden, aus der der direkte Zielfunktionswert und sein Gradient entstehen.
Die gebündelte Projektion bleibt eine getrennte Feldgegenprüfung. Dies ändert
weder direkte Werte/Gradienten noch D oder H_GN und lockert keine Toleranz.
Die bisherige ungekuppelte Prüfverletzung bleibt ausdrücklich erhalten.

Vor weiterer Suche muss die korrigierte Kopplung an Original, Punkt 119 und
dem gescheiterten Punkt 29 qualifiziert werden. Auch der alte Suchpräfix muss
unverändert reproduziert werden. Die Behebung dieser Schutzprüfung ist für sich
kein Entwurfsfortschritt, keine globale Ableitungsgarantie und kein abgeschlossener
langfristiger Schritt 1/2.
