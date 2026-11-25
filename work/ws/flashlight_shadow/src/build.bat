@echo off
rem Builds TruFlashShadow.asi (32-bit DLL) with the MSVC Build Tools (x86 target).
rem Usage: run from this folder. Adjust VCVARS if your Visual Studio is elsewhere.
set VCVARS="C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
call %VCVARS% amd64_x86 || exit /b 1
cl /nologo /LD /O2 /MT /W4 TruFlashShadow.cpp /link /OUT:TruFlashShadow.asi user32.lib kernel32.lib || exit /b 1
del TruFlashShadow.obj TruFlashShadow.exp TruFlashShadow.lib 2>nul
echo built TruFlashShadow.asi
