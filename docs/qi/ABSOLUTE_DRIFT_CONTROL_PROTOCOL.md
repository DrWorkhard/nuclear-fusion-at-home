# Absolute Wirkungs-/Driftnormierung an einem analytischen Spiegel

Vor neuen Kontrollrechnungen registriert,2026-09-13. Kein VMEC-, Goodman-,
SQuID-C- oder Kraftwerksresultat. Der direkte Vergleich von Wirkungsableitung
und Führungszentrumdrift ist in Schritt1 offen; zunächst einen vollständig
definierten analytischen Kontrollfall einschließlich Einheiten absichern.

## Analytisches Feld und Gültigkeitsbereich

Kartesisch, SI-Einheiten, B0=1T,k=0,7/m²:

    B(x,y,z) = B0*(-k*z*x, -k*z*y, 1+k*z²),
    psi = B0*(1+k*z²)*(x²+y²)/2,
    alpha = atan2(y,x).

Für r>0 gilt B=grad(psi) cross grad(alpha), div(B)=0. Direkte Ableitung ergibt
curl(B) cross B = -k*B0*grad(psi). Damit ist dies lokal ein statisches Gleichgewicht
mit mu0*p=0,1T²-k*B0*psi; im gewählten Flussbereich positiv. Keine geschlossene
toroidale Anlage, Stabilitäts-, Rand- oder Fusionsleistungsbehauptung.

Die neun festen Paare psi={0,01;0,03;0,06}Wb/rad und
Bstar={1,2;1,6;2,0}T, jeweils alpha={0;0,37;1,2}rad. Drei Gauß-Legendre-
Auflösungen64/128/256 ergeben81 feste Zellen. Entlang der Feldlinie:
S=1+k*z²,r=sqrt(2psi/(B0*S)),dl/dz=|B|/(B0*S).
Die beiden eindeutigen Umkehrpunkte liegen bei±z_b mit |B|=Bstar.
Root in S durch monotone kubische Gleichung, anschließend z=z_b*sin(u),
u zwischen -pi/2 und pi/2; keine Bewertung genau an singulären Endpunkten.

## Zwei physikalische Wege zur gleichen Größe

Einweg-Konvention: A=Integral sqrt(1-|B|/Bstar) dl, J=m*v*A,
T=(1/v)*Integral dl/sqrt(1-|B|/Bstar). Feste Invarianten E=mv²/2 und
mu=E/Bstar; elektrische Felder, Kollisionen und höhere Gyro-Ordnungen ausgelassen.
Dann Delta_psi=(m*v/q)*A_alpha=0 und Delta_alpha=-(m*v/q)*A_psi.
Einweg-/Vollbounce-Konventionen nicht vermischen.
[Rodríguez–Helander–Goodman, Gleichungen1.1–1.4](https://doi.org/10.1017/S0022377824000345).

Unabhängig die **allgemeine**, nicht auf Vakuum vereinfachte erste Driftordnung:

    v_d = b cross [mu*grad(|B|) + m*v_parallel²*kappa] / (q*|B|),
    kappa = (b dot grad)b,
    Delta_i = Integral (v_d dot grad(i))*dl/v_parallel.

Den vollen kartesischen Feld-Jacobian verwenden, daraus grad|B| und kappa
berechnen. Keine Ableitung der Wirkung in diesem direkten Weg.
[Primärherleitung, Gleichungen3.3–3.7](https://www.cambridge.org/core/journals/journal-of-plasma-physics/article/guidingcentre-lagrangian-and-quasisymmetry/83EF94257C74E7919D01CB0DF8C019A2).
Der lokale SIMSOPT-Cartesian-Tracer ist ausdrücklich ein Vakuum-RHS; diese
Vereinfachung darf auf den stromtragenden Kontrollspiegel nicht angewendet werden.

Zusätzlicher skalarer Wirkungsweg: B²=B0²*S²+2*B0*psi*k²*z²/S,
B_psi=B0*k²*z²/(S*|B|),L=dl/dz=|B|/(B0*S),
A_psi=Integral [sqrt(Q)*B_psi/(B0*S)-L*B_psi/(2*Bstar*sqrt(Q))]dz,
Q=1-|B|/Bstar. Die Endpunktterme der Wirkungsableitung verschwinden.
Alle ursprünglichen A/T/Driftwerte und beide Driftanteile erhalten.

## Feste Prüfungen und unabhängiger Audit

Vor Matrixauswertung: analytische Feld-/Clebsch-/Divergenz-/Kraftgleichgewichts-
und kartesische Ableitungskontrollen, ungültige Eingaben, Ladungszeichen,
Energie-/Massenskalierung. Keine Gleichsetzung dieser Kontrollen mit QI-Physik.

Je Zelle direkte normierte Winkelverschiebung gegen -A_psi relativ<=1e-8,
radiale normierte Verschiebung absolut<=1e-10. Feldidentitäten normiert<=1e-12.
64→128 und128→256 relative Änderungen für A,T und nichtverschwindende
Winkelverschiebung<=1e-7. Alle27 Linien und alle Auflösungen behalten.

Separater skalare Auditor: eigene Feldlinienformeln/Root in z und adaptive
Einwegintegrale (`quad`,epsabs/epsrel1e-10,limit200) unter derselben Sinustransformation;
alle81 Werte relativ<=1e-7, keine gemeinsame kartesische Driftimplementierung.
Für alle neun psi/Bstar-Paare zentrale Wirkungsdifferenzen mit relativen
psi-Schritten1e-4 **und**1e-5, jeweils relativ<=1e-6 gegen direkte Winkelverschiebung.
Beide Stufen bestehen müssen; keine rückwirkende Auswahl. Alle Aufrufe/Fehler
und adaptive Fehlerschätzungen speichern, keine neuen Referenzgleichgewichte.

Absolute Testteilchen: m=2e-27kg,q=±1,602176634e-19C,E=10keV sowie
20keV und verdoppelte Masse als Skalierungskontrollen. Dies sind definierte
Testparameter, keine genaue reale Ionenspezies. J in kg*m²/s,T in s,
Delta_alpha in rad,omega_alpha=Delta_alpha/T in rad/s. Bei gleicher E muss
omega massenunabhängig und proportional zu E/q sein. Radiale Drift ist in
diesem achsensymmetrischen Kontrollfall null; ein nichtverschwindender radialer
Drift-/Gauge-Fall und die echten QI-Gleichgewichte bleiben gesondert zu qualifizieren.

## Ressourcen und Abschlussgrenze

Reine kleine analytische Rechnungen ohne neue native Felder, Solverinstallation
oder Gleichgewichte. Während des budgetkontrollierten GN-Laufs nur Implementierung/
kleine reine Tests, die vollständige81-Zellen-/Auditrechnung erst nach dessen
Ende. Quelldateien/Protokoll/Versionen, alle Arrays und Ergebnisse hashbinden;
Fehlschläge behalten, Zielgrößen nicht anhand der Resultate neu definieren.
Bestehen qualifiziert den analytischen Normierungsweg, nicht den vollständigen
QI-/maximum-J-Maßstab und nicht den Abschluss von Plan-Schritt1.
