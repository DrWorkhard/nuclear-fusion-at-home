# Natürliche AL: unabhängige Prüfung und Wiederholung nach IO-Abbruch

Vor neuen physikalischen Auswertungen festgelegt, 2026-09-12. Die
[Originalstudie](NATURAL_AUGLAG_PROTOCOL.md) bleibt unverändert unterbrochen.
Der [Speicherplatzvorfall](../validation/RESOURCE_INTERRUPTION.md) ist kein
physikalischer Gegenbeweis, aber verhindert die Zwei-Wiederholungs-Qualifikation.

## Prüfung des Erhaltenen

Expliziter Postmortem-Modus des vorhandenen unabhängigen Auditors darf nur die
durch den Vorfallbericht hashgebundene Originalstudie lesen. Er prüft den gesamten
abgeschlossenen Arm (Auswahl, 1033 Bundles, Stufen, Multiplikatoren, native Arbeit,
Gradienten und benannte Feldidentität) sowie das exakt gespeicherte 700-Bundle-
Präfix des zweiten Arms. `all_pass` für die Studie bleibt ausdrücklich **false**,
selbst wenn `postmortem_integrity_pass` besteht. Kein ergänzter zweiter Endzustand.
Ohne expliziten Modus weist der normale Auditor die unvollständige Studie ab.

## Neuer physikalischer Versuch

Neue Ausgabeverzeichnisse `natural-auglag-recovery-v1`, unveränderter Original-
Runner und unveränderte Backend-/Solverquellen: zwei neue sequenzielle Original-
Starts, je maximal 1033 Bundles, dieselben acht Stufen/Optionen/Prüfungen. Kein
Warmstart, keine Budgetübertragung, kein Holdout-Feedback. Die mathematischen
Quellen und Solverquellen werden vor Start gegen die alte Studie hashgeprüft.
Beginn erst nach Abschluss des ressourcenintensiven nativen Neuaufbaus und bei
mindestens 2 GiB freiem Platz; keine weitere schwere parallele Arbeit.

Zusätzlich zur ursprünglichen Wiederholung/Auswahlprüfung muss der erste neue
Arm sämtliche 1033 alten Bundles exakt wiederholen; der zweite muss die 700
gespeicherten alten Bundles exakt wiederholen. Ein Präfixfehler bleibt ein Fehler,
nicht nachträglich zu einer erfolgreichen Fortsetzung umbenannt. Der neue Lauf
ist eine frische Wiederholung, kein geretteter Speicherzustand des alten Prozesses.

Nach bestandenem Audit: beide neuen ausgewählten Felder durch alle bereits
festgelegten feinen Flux-/Geometriegitter, kontinuierlichen Schranken und nativen
Zusatzprüfungen schicken. Kein Methodenrang, keine Konvergenz oder Zulässigkeit
aus internem Konstruktionsschirm allein. Bei erneut fehlender Zulässigkeit ist
dieser Versuch negativ geschlossen, nicht Langfristschritt 2 erledigt.
