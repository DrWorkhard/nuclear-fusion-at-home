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

## Quellenursache eingegrenzt, 2026-09-13

Eine rein lesende Prüfung des bereits in `uv.lock` festgelegten öffentlichen
netCDF4-1.7.4-Quellarchivs bestätigt dessen SHA256
`cdbfdc92d6f4d7192ca8506c9b3d4c1d9892969ff28d8e8e1fc97ca08bf12164`
und838.352Bytes. `include/netCDF4.pxi` Zeile376 deklariert `numpy.ndarray`
erneut ohne ausdrückliche `check_size`-Regel. `setup.py` Zeile397 setzt zugleich
`NPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION`. Der lokale NumPy-Header macht damit
`PyArrayObject` zu einem absichtlich verkürzten Kopf-Typ; NumPys eigene Cython-
Deklaration setzt dagegen ausdrücklich `check_size ignore`.

Laut [Cython-Primärdokumentation](https://docs.cython.org/en/latest/src/userguide/extension_types.html#name-specification-clause)
ist ohne Angabe `warn` die Voreinstellung: Ein größerer Laufzeittyp ist dann
erlaubt, erzeugt aber eine Warnung. Das liefert eine konkrete, quellengestützte
Erklärung für die beobachtete16/96-Warnung. **Noch kein experimentell bewiesener
Build-Patch und kein allgemeines ABI-Zertifikat.** Aktuelle Upstream-master-Dateien
sind nicht mit dem installierten1.7.4-Build gleichzusetzen; für lokale Aussagen
wird deshalb das gehashte Releasearchiv verwendet. Mehrere Web-Raw-Aufrufe waren
nicht verfügbar; die0,84-MB-Releasequelle wurde ohne Installation im Speicher
hashgeprüft und gelesen.

Ein neuer reiner Quelleninventar-Treiber soll Archiv, ausgewählte Quellhashes,
installierte Python-/Header-/Binärhashes und exakte Deklarationszeilen sichern.
Drei Kontrollen bestehen: gesperrter Hash, eindeutige normale Archivmitglieder,
Abweisung von Duplikaten/Links. Keine Archivpfade werden in das Dateisystem
extrahiert. Ruff/Dokument-/Diffprüfung bestehen. Keine Änderung an Paketen,
Warnungsfiltern, nativer Umgebung oder laufendem GN-Suchprozess.
