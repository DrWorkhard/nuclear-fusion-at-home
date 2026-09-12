# Feste Geometrie, optimale Ströme: lineare Kontrollkerne vorbereitet

2026-09-12. [Protokoll](FIXED_GEOMETRY_CURRENT_PROTOCOL.md) bei ebc7e79 vorab
registriert. Noch keine der beiden tatsächlichen Spulenformen neu ausgewertet,
kein gemessener zusätzlicher Fluxgewinn.

Additiver Drei-Spalten-SVD-Rechner mit den festen Rang-/Konditions-/Normalrest-
Schirmen; getrennte QR-Zerlegung mit expliziter dreistufiger Rücksubstitution
und skalaren Summen. Keine Verwendung desselben LS-Lösers für beide Antworten.
Rangverlust oder Konditionszahl>1e10 geben ausdrücklich keinen qualifizierten
Minimierer zurück. Konstante Stromsumme und explizite interne Skalierung werden
separat geprüft; keine neue Vorzeichenbeschränkung gegenüber dem Originalproblem.

Acht analytische Kontrollen bestehen: bekannte dreidimensionale Lösung mit
nichtverschwindendem Rest, nichtorthogonale überbestimmte Aufgabe, exakt
darstellbarer Nullrest, Rangverlust/zu große Kondition, NaNs/Formfehler und
konstante physikalische Stromsumme. Ruff beanstandete anfangs eine lange Zeile;
Zeilenumbruch vor Ausführung korrigiert, keine numerische Änderung.

Die strenge Normalrestnorm des Protokolls ist unverändert; aus einem
Numerikfehlschlag nahe Maschinenpräzision darf kein toleranzgeheilter Pass
werden. Nächster Schritt: echte quellgebundene Probes/Dateiaudit und alle
unveränderten Feld-Holdouts nach abgeschlossenem feinsten Netz-Audit.
