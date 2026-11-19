@echo off
rem Registrazione LIVE automatica per il port TRU DLC: doppio clic, poi avvia/gioca. Niente da premere.
rem Scrive in C:\tru-port\work\live\<data_ora>. Si ferma da sola 20 s dopo la chiusura del gioco.
title TRU LIVE - lascia questa finestra aperta mentre giochi
set PS=%SystemRoot%\SysWOW64\WindowsPowerShell\v1.0\powershell.exe
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmm"') do set STAMP=%%i
set OUT=C:\tru-port\work\live\%STAMP%
mkdir "%OUT%" 2>nul
echo Registro in: %OUT%
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0trudlcport_diag.ps1" -Mode Live -Out "%OUT%" -DumpMode Full -NoPrompt
echo.
echo FINITO. Dati in %OUT%  - avvisa Claude.
pause
