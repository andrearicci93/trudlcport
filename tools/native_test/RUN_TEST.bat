@echo off
rem Native D3D9 test for the TRU DLC port. Close the game first. Nothing in the game folder is changed.
set "GAME=%~1"
if "%GAME%"=="" set /p "GAME=Game folder (the one with tru.exe and mods): "
python "%~dp0native_extract.py" --game "%GAME%"
if errorlevel 1 (
  echo Shader extraction failed: check the game folder. The test continues with the probes only.
)
"%windir%\SysWOW64\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0native_test.ps1"
echo.
echo Send native_report.txt (in this folder).
pause
