# Nichtlokale räumliche Überschneidungen: sechs eingefrorene Netze

Vor echter Netzrechnung registriert, 2026-09-12. Alle sechs unveränderten
Spulennetze aus `evidence/mesh-integrity-2026-09-09.json` und dessen zwei
Quellmanifesten, in deren Reihenfolge h=0,05/0,04/0,03/0,02/0,015/0,010.
Jedes Netz muss seinen gespeicherten Hash und bestandenen intrinsischen Audit
behalten. Keine Reparatur, Umorientierung oder Neuvernetzung.

## Präziser Gültigkeitsbereich

Prüfmenge: sämtliche ungeordneten Tetraederpaare ohne gemeinsamen Vertexindex,
innerhalb und zwischen den vier tatsächlich vernetzten Grundspulen. Paare mit
gemeinsamen Vertices werden separat gezählt und ausdrücklich ausgeklammert;
der alte lokale Qualitäts-/Topologieaudit ersetzt keine globale Prüfung dieser
Nachbarpaare. Symmetriekopien, Plasma, mechanische Kontakte, echte Wickelrichtung
und reale Baugruppen bleiben außerhalb dieses Teiltests.

Die Netze verwenden die vorhandene0,05m-Querschnittsrepräsentation auf Geräteskala;
keine neue Skalierung vor dem Kollisionsvergleich. Ein positiver Teiltest ist
weder vollständige Finite-Build- noch Mechanikfreigabe.

## Konservative Vorauswahl und Nachweise

Den separat kontrollierten [Boxhierarchie-/Tetraederkern](TETRA_NONOVERLAP_METHOD.md)
verwenden: Blattgröße16; Boxpolster1e-10 mal max(1, globaler Koordinatenspannweite)
plus64epsilon mal max(1, größtem absoluten Koordinatenwert). Nur strikt größere
Boxlücken dürfen Paarmengen ausschließen; Kontakte bleiben Kandidaten.
Vollständige Knoten-/Indexpartition und jedes Traversierungsereignis speichern.
Die Paarbilanz muss exakt N*(N-1)/2 ergeben; unvollständige Traversierung ist
keine bestandene Abdeckung.

Alle verbleibenden nichtlokalen Paare mit dem festen Trennachsenkern prüfen,
Defaultpolster1e-10 und64epsilon unverändert. Jeden positiven Trennnachweis
samt Paar-ID, Achse, Ursprung und Lücke speichern. Für jedes nicht dadurch
getrennte Paar zusätzlich den unabhängigen baryzentrischen LP-Witness rechnen:
separat gelöste Gewichte>1e-10, Summenfehler<=1e-12 und skalierter
Rekonstruktionsfehler<=1e-12. Einen positiven Innenpunkt als Überschneidung
ausweisen; fehlgeschlagene/unaufgelöste LPs und Randkontakte bleiben unaufgelöst.
Nie aus fehlender Trennachse allein eine Innenüberschneidung folgern.

Ein Netz besteht diesen begrenzten Teiltest nur bei vollständiger Abdeckung,
null bestätigten Innenüberschneidungen und null unaufgelösten nichtlokalen Paaren.
Alle sechs Ergebnisse behalten, keine feinen oder negativen Netze aussortieren.

## Unabhängiger Audit und Ressourcen

Separater Auditor rekonstruiert alle Knotenboxen aus Originalvertices, die
gesamte disjunkte Index-/Paarpartition und Blattkandidaten ohne Aufruf der
Produzenten-Traversierung. Alle gespeicherten Trennrichtungen punktweise neu
projizieren; gemeinsame Vertices und LP-Gewichte separat prüfen. Physikalische
Quellen, vollständige Ereignis-/Paarzahlen, Codes, Fehlversuche und unveränderte
Netze binden. Das sind numerische Schirme mit Sicherheitsabstand, keine gerichtete
Intervallarithmetik und keine kontinuumsweite Sweep-Zertifizierung.

Höchstens1200 Sekunden und2000000 Trennachsen-Paarprüfungen pro Netz. Bei Cap,
Speicherfehler oder nichtendlicher Geometrie bisherigen Zustand als unvollständig
behalten, nicht als bestanden. Mindestens2GiB überwachte freie Plattenreserve;
kleine Arrays/Chunks statt allerN²-Paare materialisieren, zusätzliche Rohdaten
zunächst auf unter1GiB schätzen und laufend überprüfen.

Erst nach Abschluss der laufenden QI-Studie und der bereits registrierten
SLSQP-Nachoptimierung samt Abnahme starten. Keine parallele schwere Rechnung
oder Installation. Ergebnisse und unabhängige Prüfung dokumentieren/committen;
G5 bleibt für die explizit ausgeschlossenen Fragen offen.
