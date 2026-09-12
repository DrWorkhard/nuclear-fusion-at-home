# Speicherplatzfehler beim frischen Neuaufbau

12. September 2026, Laufrevision db6abf5. Der native Neuaufbau ist **gescheitert,
bevor Installation, Build oder Solver gestartet wurden**. Die gleichzeitig laufende,
nach Auswertungen budgetierte natürliche AL-Suche wurde durch denselben
Speicherplatzmangel unterbrochen. Kein Laufzeitvergleich war vorgesehen; dennoch
war die gemeinsame Nutzung der knappen Platte ein vermeidbarer Planungsfehler.

## Ursache und erhaltene Evidenz

Der lokale `git clone --no-hardlinks` checkte das gesamte StellCoilBench-Archiv
mit rund 250.000 Dateien aus. Die neu angelegte Arbeitskopie belegte rund 5,6 GB,
davon etwa 4,6 GB `submissions`. Vorab fehlten sowohl eine Platzprüfung als auch
eine Beschränkung auf benötigte Quelldateien. Das Clone-Protokoll enthält
`No space left on device`. Auch nachfolgende atomare JSON-Checkpoints schlugen
mit errno 28 fehl; sie schützen vor Teilüberschreiben, nicht vor Platzmangel.

Unverändert archiviert: `evidence/fresh-native-integration-v1/` und
`evidence/natural-auglag-pilot-v1/`. Der zusätzliche
`evidence/resource-interruption-2026-09-12.json` hält Beobachtungen und Hashes fest.
Die alten `running`-Flags sind letzte erfolgreiche Checkpoints, **keine laufenden
Prozesse und keine Abschlussberichte**. Prozessprüfung: keine Such-/Cloneprozesse
übrig. Bei der Nachprüfung waren keine temporären JSON-Dateien vorhanden.

Die erste AL-Wiederholung ist vollständig gespeichert: 1033 Bundles,
ausgewählter Vorschlag 1029, grober Flux 2,6986169559754677e-7,
maximale interne Verletzung 3,72556785421807e-9. Noch keine feine Abnahme.
Die zweite JSON-Datei enthält **700** Bundles. Die Konsole hatte bereits 725
gemeldet, aber der folgende Checkpoint scheiterte. Eine erste mündliche Angabe
von 725 gespeicherten Bundles wird damit korrigiert. Es fehlen zweites Bestfeld
und Bestarray; der verlorene Speicherzustand wird nicht erfunden. Zwei vollständige
Wiederholungen und damit Studienqualifikation liegen nicht vor.

## Gezielte Wiederherstellung und Folgerung

Nach Hashsicherung der Berichte wird ausschließlich die in diesem Versuch
angelegte Kopie `/private/tmp/fusion-native-clean-wbr4fsp3` entfernt. Sie enthält
keine einzigartigen wissenschaftlichen Ausgaben, nur reproduzierbare Checkouts.
Die Quellkopien, Root-Umgebung, ältere Testkopien und Forschungsartefakte bleiben
erhalten. Der StellCoilBench-Quellcheckout ist sauber und am unveränderten Pin.
Die Löschung selbst ist nicht rückgängig zu machen; der Inhalt ist aus Git
wiederherstellbar. Entfernung abgeschlossen (Returncode 0, Ziel existiert nicht
mehr); danach meldet `df` rund 6,9 GiB frei. Unterschiede zu gerundetem `du` sind
keine exakte Zuordnung sämtlicher zwischenzeitlicher Dateisystemänderungen.

Vor neuem nativen Versuch: benötigten Checkout-Umfang begrenzen, Platzbedarf mit
Reserve vorab und zwischen Phasen prüfen und Fehler nicht durch einen gescheiterten
Abschluss-Checkpoint verdecken. Kein erneuter Vollcheckout des Ergebnisarchivs.
Keine gleichzeitigen schweren Arbeiten während Installation/Build. Der AL-Retry
benötigt eine neue Ausgabekennung und unveränderte, vorab festgelegte Rechenbudgets;
die abgebrochene Studie bleibt unverändert. Schritt 1 und 2 bleiben offen.

Der [separate Retry](FRESH_NATIVE_RETRY_PROTOCOL.md) legt begrenzten Checkout,
Startreserve und laufende Ressourcenwächter vor neuer Ausführung fest.
Alle zehn Ressourcen-/Clone-/Prozesskontrollen und die gesamte Suite (348 Tests,
20 bekannte Warnungen) bestehen; Ruff, Dokumentstruktur und Diffprüfung bestehen.
