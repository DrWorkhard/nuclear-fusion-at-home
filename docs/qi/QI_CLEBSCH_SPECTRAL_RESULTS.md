# Clebsch-Spektraldiagnose: Arbeitsstand

2026-09-12: [Protokoll](QI_CLEBSCH_SPECTRAL_PROTOCOL.md) vor neuer Rechnung
registriert. Endliche, getrennte Wout-Fourierausgaben und Lambda-Halbgitter-
Glättung sind im aktuellen gepinnten Quellcode sichtbar. Eine spektrale Ursache
der beobachteten Restfehler ist damit noch nicht gemessen oder nachgewiesen.

Projektionswerkzeuge, fester64/128-Auswerter und unabhängiger trigonometrischer
Auditor sind vorbereitet. Sieben Moden-/Konjugations-/Parseval-Kontrollen und
eine direkte DFT-Gegenprüfung bestehen. Der reine Auditor benötigt nur NumPy;
ein unnötiger netCDF-Import wurde entfernt. Alle acht Tests bestehen auch unter
strenger RuntimeWarning-Prüfung. Die separat [dokumentierte native Importwarnung](../validation/NETCDF_IMPORT_WARNING.md)
bleibt bestehen; die ursprüngliche Umgebung wurde nicht geändert.
Noch keine neue reale Spektralrechnung.
