@echo off
rem Cattura apitrace (D3D9) di tru.exe. Avvia il gioco direttamente (non da Steam); la traccia va in C:\tru-port\work\apitrace.
rem Usare SOLO per brevi sessioni: carica il salvataggio, vai sul punto, guarda il difetto per qualche secondo, poi esci dal gioco.
rem La traccia contiene tutte le texture caricate: puo' superare qualche GB.
if not exist "C:\tru-port\work\apitrace" mkdir "C:\tru-port\work\apitrace"
cd /d "C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld"
"C:\tru-port\tools\apitrace\x\apitrace-14.0-win32\bin\apitrace.exe" trace --api d3d9 --timestamp --output "C:\tru-port\work\apitrace\tru.trace" tru.exe
echo.
echo Fine cattura. File in C:\tru-port\work\apitrace
dir "C:\tru-port\work\apitrace"
pause
