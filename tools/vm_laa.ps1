# Sets the LARGE_ADDRESS_AWARE bit in tru.exe (backup in C:\TRU_backup\tru.exe.orig). Use -Revert to restore.
param([switch]$Revert)
$exe = 'C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld\tru.exe'
$bak = 'C:\TRU_backup\tru.exe.orig'
Get-Process tru -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2
if ($Revert) { Copy-Item $bak $exe -Force; 'restored'; exit }
New-Item -ItemType Directory -Force C:\TRU_backup | Out-Null
if (-not (Test-Path $bak)) { Copy-Item $exe $bak }
$b = [System.IO.File]::ReadAllBytes($exe)
$pe = [BitConverter]::ToInt32($b, 0x3c)
$o = $pe + 22
$ch = [BitConverter]::ToUInt16($b, $o)
'before 0x{0:x}' -f $ch
$b[$o] = [byte]($b[$o] -bor 0x20)
[System.IO.File]::WriteAllBytes($exe, $b)
$b2 = [System.IO.File]::ReadAllBytes($exe)
'after 0x{0:x}' -f [BitConverter]::ToUInt16($b2, $o)
