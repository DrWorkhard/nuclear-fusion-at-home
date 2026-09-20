# Kumulative Spulengeometrieschranke: qualifizierte Grundbausteine

19. September2026. [Festes Protokoll](COIL_PERTURBATION_PROTOCOL.md) beiafb9307,
[Methodenentscheidung mit zwei Reviews](../optimization/GEOMETRY_PRESERVING_SEARCH_OPTIONS.md).
Die reale52-Zustandsmatrix ist noch nicht ausgeführt. Keine neuen Felder,
Gleichgewichte, LPs oder Suchaufrufe. Feldstartabschluss3334f1e unverändert.

## Implementierung vor der realen Perturbationsmatrix

Konstruktionsroutine und eigenständige mathematische Abnahme wurden durch
getrennte Agenten implementiert. Die reine mathematische API erhält den
originalen Geometriesnapshot, zugehörigen originalen Auditset und neue
Koeffizienten. Sie prüft Schema, Namen, Symmetrie und vorhandene Support-/Export-
Beweiskette, behauptet aber keine kryptografische Herkunft aus erfundenen
Snapshotreferenzen im alten Report. Diesen Teil übernimmt ein eigener Quellenbinder.

Der neue Binder besteht37 reine Kontrollen. Er bindet die bei3334f1e
committeten Lauf-/Auditbytes und jede einzelne positive N/V-/Raster-/Flussprüfung,
alle vier unverändert negativen physischen Feldentscheidungen sowie die exakten
ausgewählten Geometriesnapshots/reportindices3/9. Ganzer aktueller Rohgraph wird
gehasht, frühere Versionsgrenzen bleiben erhalten. Lesender tatsächlicher
Vorgänger-Replay ebenfalls bestanden; keine neue Kandidatengeometrie dafür.
Die Konstruktion besteht55 Tests, der getrennte mathematische Auditor108;
zwölf synthetische Fälle vergleichen die vollständigen Berichte beider Wege.
Geprüft sind unter anderem Null-/ULP-Änderung, Translation, Rotation, hohe Moden,
kumulative statt zurückgesetzter Änderungen, fehlende/gefälschte Beweisketten,
getrennte analytische Abstandsgrenzen und JSON-sichere negative Zertifikate.
Der reine Auditor importiert den neuen Konstruktor nicht. Beide verwenden
bewusst dieselben eingefrorenen Hilfen für den bereits qualifizierten alten
Seedbeweis; keine behauptete vollständige Unabhängigkeit dieser Vorgeschichte.

Ein zusätzlicher rein lesender Agentenreview findet keinen mathematischen Blocker:
Geschwindigkeits-/Kreuzprodukt-/Krümmungshüllen, homotoper Projektionsbeweis,
Symmetrierundung und beide Abstandstransfers sind schlüssig. Keine externe
wissenschaftliche Begutachtung. Quellenbinder bleibt zwingend; ein negatives
Zertifikat beweist keine reale Verletzung, Gleitkommapolster sind keine
gerichtete Intervallarithmetik.

[Softwarequalifikation](../../evidence/coil-perturbation-v1-primitives.json):
**1840 Tests bestanden**,334 bekannte Warnungen,0 Fehler/Skips,201,57s.
Davon200 neue Tests. Vollständiges JUnit unter
`artifacts/coil-perturbation-v1-primitives-qualification/regression.xml`, Hash
`275cad352bd79ccf4c162142e9e846f244f5ba905d1965f10bd95375b23f7a00`.
Repository-Ruff, Dokumentstruktur und Diffprüfung bestanden.

## Präzisierung der Symmetrierundung vor neuer Numerik

Bei nfp2 ist die ideale physische Kopie durch eine exakt orthogonale signierte
DiagonalmatrixQ* für Periode/Flip definiert. Die tatsächlich gespeicherte
MatrixQ=matrix.T kann kleine sin(π)-Reste enthalten. Normale, V0/A0 und
geerbte v0/S0/κ0/L0 aufQ* beziehen; Differenzhülle achsen-/koeffizientenweise aus

```
abs(Q @ candidate - Q @ seed) + abs((Q - Q*) @ seed) + pad
```

ableiten. Sie deckt sowohl die Bewegung gegenüber der tatsächlichen gespeicherten
physischen Seedkopie für direkte Abstände als auch die Bewegung gegenüber der
exakt orthogonalen Kopie für den Ableitungs-/Projektionsbeweis. Zusätzlicher
Rundungsverbrauch ist konservativ; kein stilles Gleichsetzen einer float-Matrix
mit perfekter Orthogonalität und keine doppelte Wiederverwendung der alten
Exportabweichung. Die Protokollbytes und physikalischen Grenzen bleiben unverändert.

## Offene Abnahme

Mathematische Routinen und synthetische Gegenprüfung sind abgeschlossen;
begrenzter realer Runner und vollständiger unabhängiger Matrixauditor fehlen.
Die auf Nutzerwunsch dazwischengeschobene [gemeinsame CLI](../validation/PROJECT_ENTRYPOINTS.md)
ist inzwischen mit64 neuen Tests und echtem gespeicherten Audit abgeschlossen;
sie umgeht diese ausstehende Qualifikation nicht. Nun den Gesamtworkflow
implementieren, qualifizieren und vor der realen Matrix committen.
Vor einer
Suchfreigabe muss die gesamte hier registrierte feldfreie Studie abgeschlossen
sein. Selbst ihr Pass wäre weder ein Feldgewinn noch ein Schritt4-Abschluss;
ein echter Feldfit erhält danach ein separates Protokoll.
