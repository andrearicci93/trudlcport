@echo off
rem OPTIONAL second test: also DRAWS one triangle with every pixel shader of the port.
rem Run it only if RUN_TEST.bat reports 0 rejected port shaders but the game still shows the "display driver" error.
rem It can trigger the same driver reset as the game (screen goes black for a few seconds). Save your work first.
rem If the PC/driver resets, open native_progress.txt: its last line names the shader that was being drawn.
call "%~dp0RUN_TEST.bat" "%~1" -Draw
