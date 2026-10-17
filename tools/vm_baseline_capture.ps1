# Cattura lo stato REALE della VM (sola lettura sul gioco) in Z:\tru-port\work\baseline\<Id>\
#   saves\      copia di tutti i file di salvataggio + cartella impostazioni (Documents\Eidos\Tomb Raider - Underworld)
#   gamedir.tsv relpath<TAB>size<TAB>md5 di tutti i file nella cartella del gioco (esclusi mods\, che e' in mods.tsv)
#   mods.tsv    relpath<TAB>size<TAB>md5 di OGNI file in mods\ (ricorsivo)
#   configs\    dgVoodoo.conf, ini/cfg del gioco, hook/modloader (DLL e config) copiati
#   env.txt     versioni, exe md5, data, processi attivi, tastiera
# uso: powershell -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_baseline_capture.ps1 -Id B0_raw
param([string]$Id = 'B0_raw')
$g = 'C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld'
$out = "Z:\tru-port\work\baseline\$Id"; New-Item -ItemType Directory -Force "$out\saves", "$out\configs" | Out-Null
$sv = "$env:USERPROFILE\Documents\Eidos\Tomb Raider - Underworld"
if (Test-Path $sv) { Copy-Item "$sv\*" "$out\saves" -Recurse -Force }
function Hash($f) { (Get-FileHash $f -Algorithm MD5).Hash.ToLower() }
$lines = New-Object System.Collections.Generic.List[string]
Get-ChildItem $g -File -Force | % { $lines.Add("$($_.Name)`t$($_.Length)`t$(Hash $_.FullName)") }
[IO.File]::WriteAllLines("$out\gamedir.tsv", $lines)
$m = New-Object System.Collections.Generic.List[string]
$mods = Join-Path $g 'mods'
Get-ChildItem $mods -Recurse -File -Force | % { $m.Add("$($_.FullName.Substring($mods.Length + 1))`t$($_.Length)`t$(Hash $_.FullName)") }
[IO.File]::WriteAllLines("$out\mods.tsv", $m)
foreach ($pat in 'dgVoodoo*', '*.ini', '*.cfg', '*.conf', 'd3d*.dll', 'ddraw.dll', 'dinput*.dll', 'dsound.dll', 'version.dll', 'winmm.dll', '*hook*', '*modloader*', 'TR8*', 'ErrorHandler*') {
    Get-ChildItem $g -File -Force -Filter $pat -ErrorAction SilentlyContinue | % { Copy-Item $_.FullName "$out\configs\$($_.Name)" -Force }
}
$e = @()
$e += "capture $(Get-Date -Format s)  id=$Id  host=$env:COMPUTERNAME"
$e += "tru.exe " + (Get-Item "$g\tru.exe").Length + " " + (Hash "$g\tru.exe") + " " + (Get-Item "$g\tru.exe").VersionInfo.FileVersion
$e += "mods files: $($m.Count)  gamedir files: $($lines.Count)"
$e += "layout: " + (Get-WinUserLanguageList | % { $_.LanguageTag }) -join ','
$e += "processes: " + ((Get-Process tru, steam -ErrorAction SilentlyContinue | % { $_.ProcessName + ':' + $_.Id }) -join ' ')
$e += "registry TRU:"
foreach ($k in 'HKCU:\Software\Crystal Dynamics', 'HKCU:\Software\Eidos', 'HKLM:\SOFTWARE\WOW6432Node\Crystal Dynamics', 'HKLM:\SOFTWARE\WOW6432Node\Eidos') {
    if (Test-Path $k) { $e += "  $k"; Get-ChildItem $k -Recurse -ErrorAction SilentlyContinue | % { $e += "   $($_.Name)"; try { (Get-ItemProperty $_.PSPath).PSObject.Properties | ? { $_.Name -notmatch '^PS' } | % { $e += "     $($_.Name)=$($_.Value)" } } catch {} } }
}
[IO.File]::WriteAllLines("$out\env.txt", $e)
"ok mods=$($m.Count) gamedir=$($lines.Count) -> $out"
