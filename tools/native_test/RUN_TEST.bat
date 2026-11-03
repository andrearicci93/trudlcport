@echo off
rem Native Direct3D 9 test v3 for the TRU DLC port (B269). Close the game first. Nothing in the game folder is changed.
rem Usage: RUN_TEST.bat ["<game folder>"]     (empty = synthetic probes only, no game data needed)
setlocal
set "HERE=%~dp0"
set "GAME=%~1"
if "%GAME%"=="" set /p "GAME=Game folder (the one with tru.exe and mods), or just Enter to test without the game: "
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if "%GAME%"=="" goto :run
if "%GAME:~-1%"=="\" set "GAME=%GAME:~0,-1%"
if not defined PY (
  echo Python 3 not found: the port's shaders cannot be extracted, only the synthetic probes will be tested.
  goto :run
)
%PY% "%HERE%native_extract.py" --game "%GAME%"
if errorlevel 1 echo Shader extraction failed: check the game folder. The test continues with the probes only.
:run
"%windir%\SysWOW64\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%HERE%native_test.ps1" -Game "%GAME%" %2
echo.
echo Please send trudlcport_native_result.zip (in this folder). SUMMARY.txt is the short version you can paste in a chat.
pause
