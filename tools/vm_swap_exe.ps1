# usage: vm_swap_exe.ps1 <Z:\path\to\exe>   installs it as tru.exe (original saved once in C:\TRU_backup\tru.exe.orig); -Revert via vm_laa.ps1 -Revert
param([string]$src)
$exe = 'C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld\tru.exe'
Get-Process tru -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2
if (-not (Test-Path C:\TRU_backup\tru.exe.orig)) { Copy-Item $exe C:\TRU_backup\tru.exe.orig }
Copy-Item $src $exe -Force
(Get-Item $exe).Length
