# Importabhängige netCDF4-Warnung: reproduziert, Umgebung unverändert

2026-09-12. Beim isolierten Spektralaudittest trat die RuntimeWarning
`numpy.ndarray size changed` mit Größen16/96 auf. Der Test mit
`-W error::RuntimeWarning` scheiterte beim Import des netCDF4-C-Moduls, nicht bei
einem berechneten Feldwert. Die normale gesamte Suite bestand498 Tests mit20
anderen, bekannten DeprecationWarnings; das ist kein Nachweis strikter Warnungsfreiheit.

`scripts/audit_netcdf_import_warning.py` prüft drei frische Prozesse. Der Bericht
`evidence/netcdf-import-warning-v1.json` enthält Befehle, Rückgabecodes, vollständige
Ausgaben sowie Hashes von NumPy-Initialisierung und netCDF4-Binärmodul:

- Standardimport nach NumPy: Exit0, keine sichtbare Größenwarnung.
- RuntimeWarnings nach NumPy explizit sichtbar: Exit0 mit derselben Warnung.
- RuntimeWarnings nach NumPy als Fehler: Exit1 mit derselben Warnung.

NumPy2.5.2 setzt in seinem lokalen `__init__.py` Zeilen695–698 selbst Filter für
diese Cython-Größenwarnungen. Deshalb war auch ein früherer einfacher
Python-Aufruf mit `-W error` vor dem NumPy-Import kein ausreichender Gegenbeweis.
Der [Upstream-Issue1354](https://github.com/Unidata/netcdf4-python/issues/1354)
dokumentiert denselben Größenvergleich bereits2024, auch mit NumPy<2.0.
Das beweist nicht die allgemeine ABI-Sicherheit unserer gesamten nativen Umgebung.
Kein beobachteter Datenfehler oder fehlgeschlagener numerischer Vergleich wird
aus der Warnung allein abgeleitet; ebenso wird sie nicht als behoben ausgegeben.

Der neue reine Punktarray-Spektralauditor benötigte netCDF4 nur mittelbar durch
einen importierten Dateihashhelfer. Diese unnötige Abhängigkeit wurde vor seiner
ersten physikalischen Ausführung entfernt, ohne einen Warnungsfilter hinzuzufügen.
Alle acht Spektral-/Auditkontrollen bestehen danach auch mit striktem RuntimeWarning-
Fehlerfilter. Der native Import selbst bleibt unter diesem Filter fehlgeschlagen.
Keine Paketinstallation, kein Versionswechsel, keine Änderung älterer Prüfer oder
der bereits qualifizierten wissenschaftlichen Umgebung. Ein etwaiger sauberer
Source-Build wäre ein eigener isolierter Umgebungsversuch mit erneutem Physikvergleich.
