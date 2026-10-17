# Restart tru.exe via Steam until it runs, then focus it. Usage: powershell -File vm_launch.ps1
Get-Process tru -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2
$steam = 'C:\Program Files (x86)\Steam\steam.exe'
for ($i = 0; $i -lt 4; $i++) {
    Start-Process $steam -ArgumentList '-applaunch','8140'
    for ($j = 0; $j -lt 12; $j++) {
        Start-Sleep 2
        $p = Get-Process tru -ErrorAction SilentlyContinue | Select -First 1
        if ($p) { break }
    }
    if ($p) { break }
}
if ($p) { Start-Sleep 8; (New-Object -ComObject WScript.Shell).AppActivate($p.Id) | Out-Null; 'tru ' + $p.Id } else { 'tru not started' }
