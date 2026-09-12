# Unveränderte natürliche AL: Wiederholung und unabhängige Audits bestanden

Stand 2026-09-12. [Vorabfestlegung](NATURAL_AUGLAG_RECOVERY_PROTOCOL.md).
Driverstart bei `e37581e`, physikalischer Start erst nach bestandener frischer
nativer Integration. Die unterbrochene Originalstudie bleibt unverändert und
unvollständig; dieser neue Versuch ist keine rückwirkende Reparatur ihrer Flags.

## Suchergebnis

Beide neuen Wiederholungen schließen acht Stufen mit je1033 vollständigen
Bundles ab:1781 Anfragen,748 Cachetreffer, keine globale Budgetverweigerung und
keine fehlgeschlagene Auswertung. Acht getrennte Stufenbudgetverweigerungen
sind regulär erfasst. Alle vollständigen neuen Suchpfade, Stufen, Budgets und
Zusatzarbeitszähler stimmen exakt überein. Keine Solverkonvergenz behauptet.

Auswahl beider Arme: Bundle1029, roher Suchgitter-Flux
2,6986169559754677e-7 (26,986-fache Grenze), interne Geometrieverletzung
3,72556785421807e-9 innerhalb der festen1e-8-Konstruktionsauswahltoleranz.
Das ist keine unabhängige Freigabe. Benannte Arrays haben denselben SHA-256
wie der alte vollständige Arm; Serialisierungsdateien können andere interne
Objektnamen und deshalb andere Dateihashes haben. Ihre physikalische
DOF-Zuordnung ist separat überprüft.

## Gegenprüfungen und Provenienz

- `evidence/natural-auglag-recovery-driver-v1/pilot-audit.json`: beide Arme
  bestehen jeweils28 Prüfungen für Rechenweg, Auswertungsauswahl, Stufen,
  native Zusatzarbeit, Ableitungen und benannte Feldidentität; Wiederholung exakt.
- `evidence/natural-auglag-recovery-driver-v1/recovery-audit.json`: alle12
  Prüfungen bestehen. Neues erstes Präfix1033/1033 und zweites altes Präfix
  700/700 exakt, maximale Wertdifferenz0. Ursprüngliche Mathematik,
  Solverquellen/-optionen, Threads und Protokoll bleiben identisch.
- Alle drei Driverphasen erfolgreich; minimale beobachtete freie Kapazität
  6274572288Bytes bleibt über der2-GiB-Reserve. Suchlaufzeiten sind keine
  kontrollierten Methodenvergleichszeiten.

## Vollständige feine Abnahme: unzulässig wegen Magnetfeldfehler

Bei `54cbd8c` führt der sequenzielle Driver alle vier bestehenden Werkzeuge aus.
Die Berichte liegen in `evidence/natural-auglag-recovery-v1-validation/`.
Beide Felder liefern in sämtlichen geprüften Ergebnisgrößen gleiche Werte.

| Größe | Ergebnis | Feste Grenze / Bewertung |
| --- | --- | --- |
| Roh-Flux, feinstes Oberflächen-/Spulengitter | 2,698587472179773e-7 | <=1e-8: **FAIL, Faktor26,9859** |
| Gesamtlänge, vier Basisspulen | 219,89923004246256m | <=220m: PASS |
| Kontinuierliche Krümmungsoberschranke | 0,8333580202880169/m | <=1/m: PASS |
| Kontinuierliche Spulenabstandsuntergrenze | 1,0866060702842504m | >=1,06m: PASS |
| Feinster Spulen-Plasma-Abstand | 3,1735085164845853m | >=1,3m: PASS im Gittertest |
| Native mittlere quadratische Krümmung, Maximum | 5,331372951165614 | Alle Auflösungen/Verfeinerung PASS |
| Native Bogenlängenvarianz, Maximum | 3,194924013004504 | Alle Auflösungen/Verfeinerung PASS |

Alle vier Fluxgitter und geometrischen Auflösungen erhalten; Fluxverfeinerung
besteht. Die kontinuierliche Krümmung ist bei200 Punkten noch unaufgelöst,
ab400 Punkten PASS; der unaufgelöste Level bleibt dokumentiert. Native
Verkettungszahl auf beiden festgelegten Gittern null. Mittleres |B| im feinsten
Fluxgitter0,9461251760804333T. Keine vollständige Volumen-/Ingenieurfreigabe.

Driver-Exitcodes2/0/0/0 bedeuten reguläre Fluxablehnung und anschließend
vollständig ausgeführte weitere Prüfungen, keinen verschwiegenen Ausführungsfehler.
Minimale beobachtete freie Kapazität6267047936Bytes >2GiB. Keine neuen Grenzen,
keine Budgetverlängerung und kein Feedback in den abgeschlossenen Suchlauf.
Dieser begrenzte Versuch ist vollständig geschlossen; langfristiger Schritt2
bleibt offen. Nächster getrennt registrierter Versuch: Jacobispalten-Skalierung.
