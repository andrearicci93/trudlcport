@echo off
cd /d "%~dp0"
echo Start the game from Steam FIRST, then leave this window open while you play machine_room. Ctrl+C = stop.
python -I mr_probe.py
pause
