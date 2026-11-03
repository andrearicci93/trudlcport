@echo off
rem Wrapper Windows per credits_convert.py / Windows wrapper for credits_convert.py
rem Uso / Usage:  credits_convert.bat "<cartella contenuto Xbox DLC1>" [opzioni]
rem Opzioni utili / useful options: -o <cartella> --game-dir "<cartella gioco>" --rad "<...\radvideo64.exe>" --ffmpeg "<...\ffmpeg.exe>"
setlocal
set "HERE=%~dp0"
where py >nul 2>nul && ( py -3 "%HERE%credits_convert.py" %* & goto :end )
where python >nul 2>nul && ( python "%HERE%credits_convert.py" %* & goto :end )
echo ERRORE: Python 3 non trovato. Installarlo da https://www.python.org/downloads/
echo ERROR: Python 3 not found. Install it from https://www.python.org/downloads/
exit /b 1
:end
exit /b %ERRORLEVEL%
