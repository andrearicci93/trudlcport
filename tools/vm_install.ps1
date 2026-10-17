# Copy files from a Mac work dir into the game mods folder. Usage: powershell -File vm_install.ps1 <Z:\...\dir>
param([string]$src)
$d = 'C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld\mods'
Copy-Item (Join-Path $src '*') $d -Recurse -Force
Get-ChildItem $d -File | % { $_.Name + ' ' + $_.Length }
