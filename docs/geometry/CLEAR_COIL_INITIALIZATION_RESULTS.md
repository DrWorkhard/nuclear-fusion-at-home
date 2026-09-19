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

## Synthetische Implementierung und Pre-Data-Review

Konstruktion, unabhängige Rechnung und Prozessverwaltung werden getrennt
implementiert. Die Konstruktion verwendet native Flächen und analytische
komplexe Modenkonvolution; die Gegenprüfung eigene R/Z-Reihen und reelle
Produktformeln. Es werden weder magnetische Felder aufgerufen noch Ströme
oder Flussnormierungen für die rein geometrischen Snapshots erfunden.

Ein dritter lesender Codereview fand vor Targetdaten: HiGHS benötigt eigene
Threadoptionen; bloße Umgebungsvariablen reichen nicht als Nachweis. Zusätzlich
konnten ein NaN-Radiusunterwert und verborgene asymmetrische Moden die
Konstruktion erreichen, obwohl die unabhängige Prüfung sie verworfen hätte.
Explizite native Solveroptionen, strikte reelle/finite Eingaben und neue
Negativtests beheben diese Lücken. Die Weiterleitungswarnung von SciPy wird
gespeichert und weiterhin sichtbar ausgegeben.47 Konstruktionskontrollen
bestehen, darunter native Optionsübergabe, schräger Tangentialfall mit
höherpräziser Gegenrechnung, nichtaxisymmetrische Flächen und exakter Export.

Der Runner erhält außer dem1800s-Gesamtwächter einen äußeren30s-Wächter je
LP-Aufruf, mit vorab gespeicherten Startmarken und erhaltenen verspäteten
Rohdaten. Ein unabhängiger Review fand außerdem eine Zeitprüflücke für spät
fehlschlagende Aufrufe; diese wird vor Freigabe geschlossen. Der kombinierte
Zwischentest bestand112 Kontrollen und scheiterte an acht noch nicht
synchronisierten Optionsvergleichen des Auditors. Das ist ein offener
Implementierungs-Zwischenstand, kein gescheiterter physischer Versuch und
keine abgeschlossene Softwarequalifikation.

Beide Ausführungslücken werden separat negativ getestet: verspätete Exceptions
dürfen keinen abgeschlossenen LP-Versuch erzeugen; ein abnormaler Prozessabschluss
nach vollständigem Workerprotokoll darf keinen erfolgreichen Gesamtlauf vortäuschen.
Die Fehlerdateien und letzten erfolgreichen Checkpoints bleiben erhalten. Eine
vollständige synthetische Integration prüft zusätzlich alle zwölf Varianten,
sechs Flächenraster,168 echte LP-Aufrufe und72 unabhängige direkte
Abstandszertifikate. Diese künstlichen Torusflächen sind keine Projekt-Targetdaten.

Erster vollständiger synthetischer Durchlauf einschließlich gespeichertem
CLI-Audit bestanden: beide Spulenklassen auswählbar, alle72 direkten Prüfungen
ausgeführt. Im selben Zwischenlauf bestanden69 Kontrollen; eine zusätzliche
Testassertion erwartete die Zahl3,5 bitgenau statt3,5000000000000004. Die
physikalische Grenzablehnung war bereits korrekt; korrigiert wird nur der Test
dieser Darstellung, kein Abnahmegate.56 separate Workflowtests bestehen nach
Schließen der Zeit- und Prozessabschlusslücken. Der letzte Geometriereview
fordert noch explizite Übertragung der kleinen Fourierexport-Abweichung auf die
analytischen Längen-/Krümmungsschranken der tatsächlich gespeicherten Kontur.
Gemeinsame abschließende Regression und Code-Freeze stehen noch aus.

## Abgeschlossene unabhängige Detailqualifikation

Der endgültige Exportvergleich überträgt Positions- und Ableitungsfehler auf die
tatsächlichen Längen-/Krümmungs-/Abstandsschranken. Eine strikt konvexe Projektion
sichert den Selbstschnittschirm auch bei kleiner numerischer Nichtplanarität;
keine behauptete exakte Planarität oder gerichtete Intervallarithmetik. Neue
Grenzmutationen innerhalb des erlaubten5e-12-Rohvergleichs werden korrekt
abgelehnt, wenn tatsächliche Länge oder Krümmung die physische Grenze verletzt.
Der analytische Paarabstand verliert zweimal die maximale Positionsunsicherheit;
Plasmaschutz mindestensd−E0. Alle direkten Cover-Gates bleiben zusätzlich nötig.

87 unabhängige Kontrolltests bestehen in77,51s, darunter erneut der vollständige
synthetische168-LP-Durchlauf und sämtliche72 Abstandszertifikate.181 erwartete
SciPy-Optionsweiterleitungswarnungen bleiben sichtbar und werden exakt geprüft.
Das End-to-End-Testprogramm führt den Worker im Testprozess aus und ersetzt nur
den Quellenbinder durch neu erzeugte künstliche Torusdaten. Der separate
Prozesswächter und Fehlerabschluss werden durch die Workflowtests geprüft;
kein behaupteter eigener Subprozess im synthetischen Gesamtpfad. Noch keine
realen Target-Auswertungen. Gemeinsame Vollregression läuft vor dem Code-Commit.

Die abschließende gemeinsame Vollregression besteht **1172 Tests, null Fehler,
null Skips** in153,53s. Das umfasst190 neue Kontrollen;334 sichtbare Warnungen
bestehen aus144 bekannten Fixturewarnungen und190 explizit gespeicherten bzw.
erneut ausgegebenen HiGHS-Optionsmeldungen. Ruff für das gesamte Repository,
Dokumentstruktur- und Diffprüfung bestehen. Der
[Qualifikationsnachweis](../../evidence/clear-coil-initialization-v1-qualification.json)
bindet die getesteten Quellen und den JUnit-Bericht. Damit ist diese
Implementierungsphase abgeschlossen; ihre Zwischenfehler bleiben oben erhalten.
Nächster Schritt nach Commit: ausschließlich die registrierten echten
zwölf geometrischen Varianten, keine Feldsuche oder neue Gleichgewichtsrechnung.

## Ausführung nach Code-Freeze

Im vorhandenen, unveränderten nativen Environment mit einem frischen absoluten
Artefaktpfad; keine Installation. Produzent und unabhängiger Auditor getrennt:

```bash
PYTHONPATH=src MPLCONFIGDIR=/private/tmp/fusion-mpl-cache OMPI_MCA_btl=self \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python scripts/run_clear_coil_initialization.py \
  --raw /Users/sebastianwirkert/workspace/fusion/artifacts/clear-coil-initialization-v1

PYTHONPATH=src MPLCONFIGDIR=/private/tmp/fusion-mpl-cache OMPI_MCA_btl=self \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python scripts/audit_clear_coil_initialization.py \
  --run /Users/sebastianwirkert/workspace/fusion/artifacts/clear-coil-initialization-v1/run.json \
  --output /Users/sebastianwirkert/workspace/fusion/evidence/clear-coil-initialization-v1-audit.json
```

Vor Wiederholung andere frische Pfade wählen, niemals bestehende Rohdaten
überschreiben. Ein Exitcode2 kann eine korrekt abgeschlossene negative Abnahme
bedeuten; `status`, Quellenprüfung und geometrische Gates getrennt lesen.
`field_pass`, `transfer_pass` und `step4_pass` bleiben auch bei Geometrieerfolg false.
