@echo off
rem TRU DLC port - diagnostica Windows. Avvia PowerShell a 32 bit (come il gioco). Non modifica nulla senza dirlo.
rem (nessun blocco tra parentesi: i percorsi tipo "Program Files (x86)" li romperebbero)
setlocal
cd /d "%~dp0"
set "PS=%windir%\SysWOW64\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PS%" set "PS=powershell.exe"
set "GAMEARG="
set "G="
set "DEFGAME=C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld"
:menu
cls
echo ==================================================================
echo   TRU DLC port - diagnostica Windows
echo ==================================================================
echo   1) CHECK COMPLETO   (gioco chiuso): offline + test Direct3D 9 nativo
echo                       in un unico zip
echo   2) CHECK LIVE       (gioco aperto): fps reali, vena, screenshot, dump
echo   3) FIX exe: Steamless + patch del port, tutto automatico [gioco chiuso]
echo   4) Prova A/B del backend grafico (dgVoodoo come in VM / nativo)
echo   5) Dump automatici dei crash di Windows (amministratore)
echo   6) Solo check offline veloce (senza test nativo)
echo   7) Ricrea lo zip dei risultati
echo   8) FIX shader per il D3D9 nativo (cmp con 2 costanti) [gioco chiuso]
echo   9) Annulla il FIX shader (ripristina i .drm originali)
echo   0) Esci
echo.
echo   Risultati: trudlcport_diag_result.zip (in questa cartella)
echo.
set "C="
set /p "C=Scelta: "
if "%C%"=="1" goto full
if "%C%"=="2" goto live
if "%C%"=="3" goto fix
if "%C%"=="4" goto backend
if "%C%"=="5" goto crash
if "%C%"=="6" goto offline
if "%C%"=="7" goto zip
if "%C%"=="8" goto fixps
if "%C%"=="9" goto fixps_undo
if "%C%"=="0" goto end
goto menu

:askgame
if defined GAMEARG exit /b 0
if exist "%DEFGAME%\tru.exe" set "G=%DEFGAME%"
if exist "%DEFGAME%\tru.exe" goto askgame_set
set "G="
set /p "G=Cartella del gioco (invio = rilevamento automatico): "
if not defined G exit /b 0
set "G=%G:"=%"
:askgame_set
if "%G:~-1%"=="\" set "G=%G:~0,-1%"
set GAMEARG=-Game "%G%"
echo Cartella del gioco: %G%
exit /b 0

:offline
call :askgame
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0trudlcport_diag.ps1" -Mode Offline %GAMEARG%
echo.
pause
goto menu

:full
call :askgame
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0trudlcport_diag.ps1" -Mode Offline %GAMEARG%
echo.
echo ---- Test Direct3D 9 nativo ----
if exist "%~dp0native_test\trudlcport_native_result.zip" del /q "%~dp0native_test\trudlcport_native_result.zip"
if exist "%~dp0native_test\SUMMARY.txt" del /q "%~dp0native_test\SUMMARY.txt"
if not defined G goto full_nog
call "%~dp0native_test\RUN_TEST.bat" "%G%"
goto full_done
:full_nog
call "%~dp0native_test\RUN_TEST.bat"
:full_done
if not exist "%~dp0trudlcport_diag_out" mkdir "%~dp0trudlcport_diag_out"
if exist "%~dp0native_test\SUMMARY.txt" copy /y "%~dp0native_test\SUMMARY.txt" "%~dp0trudlcport_diag_out\NATIVE_SUMMARY.txt" >nul
if exist "%~dp0native_test\trudlcport_native_result.zip" copy /y "%~dp0native_test\trudlcport_native_result.zip" "%~dp0trudlcport_diag_out\" >nul
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0trudlcport_diag.ps1" -Mode Zip
echo.
pause
goto menu

:live
call :askgame
echo.
echo  Lascia questa finestra aperta, poi avvia il gioco da Steam.
echo  F6  = marcatore (premilo quando provi il wall-run o vedi i pantaloni beige; a schermo intero premi anche F12)
echo  F7  = marcatore + screenshot + dump (usalo UNA volta sul difetto)
echo.
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0trudlcport_diag.ps1" -Mode Live %GAMEARG%
echo.
pause
goto menu

:fix
call :askgame
echo.
echo  FIX COMPLETO dell'exe: se serve rifa l'exe sbloccato con Steamless (--realign),
echo  applica la patch del port, salva il backup e aggiorna il registro di installazione.
echo  Se serve, chiede i diritti di amministratore. Chiudi il gioco prima di continuare.
echo  Annullabile con:  python fix_exe.py --restore
set "OK="
set /p "OK=Procedo? (s/n): "
if /i not "%OK%"=="s" goto menu
set "PY="
where py >nul 2>nul && set "PY=py -3"
if defined PY goto fix_run
where python >nul 2>nul && set "PY=python"
if defined PY goto fix_run
echo Python 3 non trovato: installalo (python.org, con "Add to PATH") e riprova.
pause
goto menu
:fix_run
if defined G goto fix_g
%PY% "%~dp0fix_exe.py"
goto fix_end
:fix_g
%PY% "%~dp0fix_exe.py" --game "%G%"
:fix_end
echo.
echo ---- Controllo finale (offline veloce) ----
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0trudlcport_diag.ps1" -Mode Offline -SkipDxdiag %GAMEARG%
echo.
pause
goto menu

:backend
call :askgame
echo.
echo   a) dgVoodoo2 come in VM (FPS illimitati)
echo   b) dgVoodoo2 come in VM, FPS bloccati a 60
echo   c) Direct3D 9 nativo di Windows (toglie d3d9.dll dalla cartella del gioco)
echo   r) RIPRISTINA come era prima
echo   x) annulla
set "B="
set /p "B=Scelta: "
set "ACT="
if /i "%B%"=="a" set "ACT=dgvoodoo"
if /i "%B%"=="b" set "ACT=dgvoodoo60"
if /i "%B%"=="c" set "ACT=native"
if /i "%B%"=="r" set "ACT=restore"
if not defined ACT goto backend_end
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0trudlcport_diag.ps1" -Mode Backend -Action %ACT% %GAMEARG%
:backend_end
pause
goto menu

:crash
set "K="
set /p "K=Attivare (on) o disattivare (off) i dump automatici? "
if /i "%K%"=="on" "%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0trudlcport_diag.ps1" -Mode CrashDumps -Action on
if /i "%K%"=="off" "%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0trudlcport_diag.ps1" -Mode CrashDumps -Action off
pause
goto menu

:zip
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0trudlcport_diag.ps1" -Mode Zip
pause
goto menu

:fixps
call :askgame
set "PY="
where py >nul 2>nul && set "PY=py -3"
if defined PY goto fixps_run
where python >nul 2>nul && set "PY=python"
if defined PY goto fixps_run
echo Python 3 non trovato: installalo (python.org, con "Add to PATH") e riprova.
pause
goto menu
:fixps_run
echo.
echo  Corregge i pixel shader del port rifiutati dal Direct3D 9 nativo (backup in mods_backup_psfix).
if defined G goto fixps_g
%PY% "%~dp0fix_ps.py"
goto fixps_end
:fixps_g
%PY% "%~dp0fix_ps.py" --game "%G%"
:fixps_end
pause
goto menu

:fixps_undo
call :askgame
set "PY="
where py >nul 2>nul && set "PY=py -3"
if defined PY goto fixps_undo_run
where python >nul 2>nul && set "PY=python"
:fixps_undo_run
if defined G goto fixps_undo_g
%PY% "%~dp0fix_ps.py" --restore
goto fixps_undo_end
:fixps_undo_g
%PY% "%~dp0fix_ps.py" --game "%G%" --restore
:fixps_undo_end
pause
goto menu

:end
endlocal
