# Begrenzte Reproduktion des GN-Identitätsfehlers — 2026-09-12

Vor dem Wiederholungslauf festgelegt. Der fehlgeschlagene erste GN-Trust-Arm
bleibt unverändert. Keine Toleranzänderung und kein neuer Konstruktionsversuch.

Die exakt gleiche physikalische Vorbereitung, Solveroptionen, ursprüngliche
Parameterbasis und Seed-46-Prüfung wiederholen, aber nur den ersten Arm mit
höchstens **29** Bundles. Alle ersten 28 vollständigen Vektoren/Parameterhashes
und der Hash des fehlgeschlagenen 29. Vorschlags müssen exakt übereinstimmen.
Falls der Fehler nicht wiederkehrt, keine weitere Suche: Abweichung dokumentieren.

Der Fehlerpfad speichert nun zusätzlich x, den direkten Werte-/Jacobianvektor,
gebündeltes z/Dz, beide gemessenen Identitätsfehler und das serialisierte Feld
des fehlgeschlagenen Punktes. Keine zusätzliche physikalische Auswertung im
Fehlerhandler; nur vorhandene Arrays kopieren und das bekannte Feld speichern.
Ein reproduzierter Fehler ist ein erfolgreicher Diagnose-Replay, aber der
Qualifikationsstatus des Optimierungspiloten bleibt falsch.

Danach erst eine getrennte Punktdiagnose festlegen: native Einzelpunktmatrix,
explizite Direktfeldberechnung und gerichtete Differenzen können Ursachen
unterscheiden. Der Fehler wird nicht allein wegen seiner Größe als Rundung
abgetan. Feld-/Gradientgrenze 1e-10 und alle Zulässigkeitsgrenzen bleiben bestehen.
