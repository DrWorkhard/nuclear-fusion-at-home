# QI-Autoren-Eingaben und Produzenten: Zuordnung begrenzt

2026-09-12, vor neuen Gleichgewichten. Alle vier schon verwendeten Goodman-
Wouts sind hashidentisch erhalten; die zugehörigen lokalen Eingaben existieren.
`evidence/qi-producer-inventory-v1.json` bindet Dateien, Metadaten, Eingabekontrollen,
VMEC++-Pythonmodul/Binärdatei und illustrative Ausgabekernels.

| Fall | Wout-Version | ns / mpol / ntor | gespeicherte Iterationen |
| --- | --- | --- | --- |
| nfp2 Vakuum | 9.0 | 201 / 5 / 10 | 5414 |
| nfp2 beta2 | 9.0 | 201 / 5 / 10 | 4941 |
| nfp3 Vakuum | 9.0 | 201 / 9 / 10 | 6779 |
| nfp3 beta2 | 9.0 | 201 / 9 / 10 | 33284 |

Alle verlangen abschließend1e-16 und erreichen gespeicherte Residuen darunter.
Geometrische Dimensionen stimmen mit den Eingaben überein. Der absichtlich
exakte Dimensions-/Flussvergleich endet jedoch mit exit2: `PHIEDGE` ist
0,03141592653589793, Wout-`phi[-1]`0,031415926535897955. Die Differenz liegt bei
2,43e-17 Wb, rund7,73e-16 relativ, nicht bei den beobachteten1e-3-Feldabweichungen.
Diese negative Bitgleichheitsprüfung bleibt erhalten; keine Grenzlockerung,
kein daraus abgeleiteter Physikfehler oder Identitätsnachweis der vollen Eingabe.

Die vorhandene native Referenz ist VMEC8.52. Der andere lokale STELLOPT-Ordner
`PARVMEC` nennt sich intern1.0, nicht9.0. Im unveränderten installierten VMEC++
0.7.3 sind `vmec_8_52` und `parvmec` tatsächlich verfügbar. Das ist getrennt vom
gepinnten Checkout geprüft. Dessen Ausgabekernel schreibt ausdrücklich8.52 und
enthält weiterhin einen TODO zur vollständigen PARVMEC-Anpassung. Ein Wechsel
der Iterationssteuerung beweist keine identische9.0-Ausgabe oder historische
Binär-/Patchzuordnung. Der exakte historische Produzent bleibt unbekannt.

Die interne volle Lambda-Radialdarstellung darf nicht mit der Wout-Konvention
verwechselt werden: der inspizierte Ausgabekernel glättet Lambda für `lmns` auf
Halbflächen (ungerade m mit Wurzel-s-Gewichten). SIMSOPT liest `lmns[:,1:]` auf
dem Halbgitter. Kein Anlass, den alten Tracer blind auf volle Radien umzuschalten.
Aktuelle Primär-API: [VMEC++ IterationStyle](https://proximafusion.github.io/vmecpp/api/vmecpp.html).
Die lokalen, hashgebundenen Quellen sind für unsere Ausführung maßgeblich.

Nächster Schritt ist eine getrennt [registrierte Auflösungsstudie](QI_FRESH_RESOLUTION_PROTOCOL.md),
nicht eine nachträgliche Korrektur der alten Dateien. Der W7-X-spezifische
VMEC2000-Runner darf dafür nicht benutzt werden: er würde dessen festen
Referenzbericht überschreiben. Keine Umgebung, Quellrevision oder Systempakete
wurden geändert. Ruff besteht; der Metadatenlauf ist vollständig, aber sein
strenger Flussgleichheitstest negativ. Neue Gleichgewichtsrechnungen: null.
