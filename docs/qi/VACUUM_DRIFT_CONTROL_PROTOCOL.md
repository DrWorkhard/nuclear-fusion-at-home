# Nichtachsensymmetrische Vakuumkontrolle: beide Driftkomponenten

Vor neuen Feld-/Matrixrechnungen registriert,2026-09-13. Additiv zur abgeschlossenen
[achsensymmetrischen Normierung](ABSOLUTE_DRIFT_CONTROL_RESULTS.md); alte Daten,
Protokolle und Rechner bleiben unverändert. Keine Stellarator-/QI-Gesamtfreigabe.

## Eigene analytische Konstruktion

B0=1T,a=0,7T/m,b=0,3T/m,g=a+b=1T/m:

    B=(-a*x,-b*y,B0+g*z), S=1+g*z/B0>0.

Das ist ein exaktes Vakuumfeld: divB=0,curlB=0, Potential
V=-a*x²/2-b*y²/2+B0*z+g*z²/2 mit B=gradV. Kein angenommener
Plasmadruck oder unbelegtes Kraftgleichgewicht nötig. Der Nullpunkt S=0,x=y=0
liegt außerhalb der Auswertung; keine toroidale Anlage oder Stabilitätsaussage.

X=x*S^(a/g),Y=y*S^(b/g),psi=B0*(X²+Y²)/2,alpha=atan2(Y,X).
Direkte Ableitung ergibt B=gradpsi cross gradalpha. X,Y sind Feldlinienkonstanten.
Auf einer Linie mit R=sqrt(2psi/B0):

    x=R*cos(alpha)*S^(-a/g), y=R*sin(alpha)*S^(-b/g),
    z=(B0/g)*(S-1), L=dl/dz=|B|/(B0*S),
    |B|²=B0²*S²+(2psi/B0)*(a²*cos²(alpha)*S^(-2a/g)
                                      +b²*sin²(alpha)*S^(-2b/g)).

Die letzte Funktion ist auf S>0 streng konvex, divergiert an beiden Enden und
hat genau ein Minimum. Für die festen Fälle ist |B|(S=1)<Bstar; je eine Root
in [1e-6,1] und [1,Bstar/B0]. Beide Brackets vor jedem Rootaufruf prüfen;
keine nachträgliche Suchbereichserweiterung. Umkehrpunkte unsymmetrisch in z.
Regularisierung z=z_mid+z_half*sin(u),u zwischen±pi/2, offene Gaußknoten.

## Feste Matrix und unabhängiger Vergleich

psi={0,01;0,03;0,06}Wb/rad, Bstar={1,2;1,6;2,0}T,
alpha={0,2;0,6;1,1}rad, N={64;128;256}:81 Zellen/27 Linien.
Diese Winkel vermeiden die achsensymmetrischen Null-Komponenten-Kontrollachsen;
kein nachträgliches Entfernen kleiner Driftwerte.

Direkter Weg: voller kartesischer Jacobian diag(-a,-b,g), grad|B|,kappa und
allgemeine erste Driftordnung aus dem qualifizierten Helfer. Beide reduzierte
Verschiebungen integrieren: dpsi=Integral(vd_reduced dot gradpsi)*dl/sqrt(Q),
dalpha analog; Q=1-|B|/Bstar. Zusätzlich stimmt hier die Vakuumvereinfachung
punktweise mit der allgemeinen Drift überein, anders als beim drucktragenden Spiegel.

Wirkungsweg A=Integral sqrt(Q)*L dz, Einweg-Tgeom=Integral L*dz/sqrt(Q).
Mit H=a²*x²+b²*y² gilt bei festem z:

    B_psi=H/(2psi*|B|),
    B_alpha=(2psi/B0)*sin(alpha)*cos(alpha)
            *(b²*S^(-2b/g)-a²*S^(-2a/g))/|B|,
    A_i=Integral [sqrt(Q)/(B0*S)-L/(2Bstar*sqrt(Q))]*B_i dz.

Beide Endpunktterme verschwinden. Verglichen wird dpsi=A_alpha,dalpha=-A_psi,
nicht nur die Winkelkomponente. Die Hamilton-/Einwegkonvention folgt
[Rodríguez–Helander–Goodman,Gleichungen1.1–1.4](https://doi.org/10.1017/S0022377824000345);
oben stehen eigene Feld-/Geometrieableitungen, keine publizierte QI-Konfiguration.
Die allgemeine erste GC-Ordnung stammt aus der
[Primärherleitung,Abschnitt3](https://www.cambridge.org/core/journals/journal-of-plasma-physics/article/guidingcentre-lagrangian-and-quasisymmetry/83EF94257C74E7919D01CB0DF8C019A2).

Separater Auditor ohne kartesischen Produzenten: eigene skalare Geometrie,
Roots in z mit denselben physischen Brackets und adaptive Sinusquadratur
(epsabs=epsrel1e-10,limit200). Alle27 physikalischen Linien separat;
keine Wiederverwendung zwischen unterschiedlichen alpha. Zusätzlich zentrale
A-Differenzen nach psi mit relativen Stufen1e-4/1e-5 und nach alpha mit absoluten
Stufen1e-4/1e-5rad; beide Stufen müssen bestehen. Somit243 skalare Grund-/FD-
Zustände; alle Aufrufe, Schätzfehler, Warnungen und Abbrüche behalten.

Feste Fehlernorm für nichtverschwindende Driftkomponenten: abs(a-b)/max(abs(b),1e-12).
Direkter/analytischer Wirkungsweg<=1e-8; separate skalare Quadratur<=1e-7;
beide FD-Stufen je Komponente<=1e-6. Wirkung/Transitlänge relativ<=1e-7;
alle64→128→256 Verfeinerungen der vier integrierten Größen<=1e-7.
Feld-/Clebsch-/Vakuumidentitäten normiert<=1e-12. Keine Anpassung nach Ergebnis.

## Physikalisch gleiche Phase unter Neumarkierung

psi_ref=0,03Wb/rad; am Anker psi0 jede Linie mit
beta=alpha-c*(psi-psi0)/psi_ref, c={-1;0;+1} kennzeichnen.
gradbeta=gradalpha-(c/psi_ref)*gradpsi und
d_beta=d_alpha-(c/psi_ref)*d_psi. Wirkungsableitung nach psi bei festem beta
ist A_psi+(c/psi_ref)*A_alpha. Alle direkten und Wirkungs-/Kettenregelwerte
speichern; relative Norm wie oben, Grenze1e-8.

Festgehaltene physikalische Phase F=2psi/psi_ref+3alpha. Ihr Kovektor ist
k=(2/psi_ref,3), neu k'=(2/psi_ref+3c/psi_ref,3).
Die Kontraktion k dot d muss unter Neumarkierung bis1e-10 normiert gleich bleiben.
Das qualifiziert Koordinatenkovarianz, keine wählbare positive Präzession durch Gauge.

Definierte Teilchen/Einweg-SI wie im Vorgänger: m2e-27kg,q±e,E10keV,
zusätzlich20keV und doppelte Masse. J,T,Delta_psi,Delta_alpha,beide Driftraten
und Phasenfrequenz speichern, Vorzeichen-/Energie-/Massenkontrollen<=1e-12 relativ.

## Reihenfolge und Abschlussgrenze

Zuerst reine Feld-/Ableitungs-/Root-/Drift-/SI- und Fehlerkontrollen, dann Code
committen, erst danach vollständige Matrix und separater Audit. Mindestens2GiB
Reserve, keine native Solverinstallation oder konkurrierende schwere Suche.
Alle Arrays/Code/Protokolle/Versionen hashbinden, keine alten Kontrollen ersetzen.

Bestehen qualifiziert beide Driftkomponenten und dieselbe Phase in diesem
analytischen Vakuumfeld. Echte QI-Gleichgewichte, Muldenidentität, Domäne und
Auflösung bleiben eigenständige Gates; kein Abschluss von Schritt1 allein hierdurch.
