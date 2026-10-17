# Fully automatic load test inside the VM (no VMPal key injection): start tru.exe, skip attract movies (Space), press Resume (Enter),
# take screenshots every 15 s into Z:\tru-port\work\autotest\<label>\, detect crash, copy dump, write result.txt.
# usage: powershell -ExecutionPolicy Bypass -File vm_autotest.ps1 -Label name [-Seconds 200]
param([string]$Label = 'test', [int]$Seconds = 200, [switch]$NoKeys)
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$out = "Z:\tru-port\work\autotest\$Label"; New-Item -ItemType Directory -Force $out | Out-Null
Remove-Item "$out\*" -Force -ErrorAction SilentlyContinue
Add-Type @"
using System; using System.Runtime.InteropServices;
public class W {
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, UIntPtr e);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
 [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
"@
[W]::SetProcessDPIAware() | Out-Null
$sh = New-Object -ComObject WScript.Shell
function Shot($name) {
    try {
        $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
        $g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
        $bmp.Save("$out\$name.png", [System.Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()
    } catch { "shot failed: $_" | Out-File "$out\shot_errors.txt" -Append }
}
function Focus {
    $p = Get-Process tru -ErrorAction SilentlyContinue | Select -First 1
    if ($p) {
        try { [W]::ShowWindow($p.MainWindowHandle, 9) | Out-Null; [W]::SetForegroundWindow($p.MainWindowHandle) | Out-Null } catch {}
        $sh.AppActivate($p.Id) | Out-Null
        $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        [W]::SetCursorPos([int]($b.Width * 0.06), [int]($b.Height * 0.45)) | Out-Null
        [W]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero); [W]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
        Start-Sleep -Milliseconds 300
    }
    return $p
}
Get-Process tru -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2
$steam = 'C:\Program Files (x86)\Steam\steam.exe'
$t0 = Get-Date; $p = $null
for ($i = 0; $i -lt 4 -and -not $p; $i++) {
    Start-Process $steam -ArgumentList '-applaunch', '8140'
    for ($j = 0; $j -lt 12 -and -not $p; $j++) { Start-Sleep 2; $p = Get-Process tru -ErrorAction SilentlyContinue | Select -First 1 }
}
if (-not $p) { 'RESULT: tru did not start' | Out-File "$out\result.txt"; exit }
$startedAt = Get-Date
$log = @()
$resumeSent = 0
$n = 0
while (((Get-Date) - $startedAt).TotalSeconds -lt $Seconds) {
    Start-Sleep 5
    $el = [int]((Get-Date) - $startedAt).TotalSeconds
    $alive = Get-Process tru -ErrorAction SilentlyContinue
    if (-not $alive) { $log += "t=$el tru EXITED"; break }
    if ($el -lt 26 -or -not $NoKeys) { $null = Focus }
    # menu is ready at ~16 s and attract mode starts after ~30 s idle: Enter at ~20 s and ~30 s starts Resume Game
    if (-not $NoKeys -and $el -ge 20 -and $resumeSent -lt 1) { [System.Windows.Forms.SendKeys]::SendWait('{ENTER}'); $resumeSent++; $log += "t=$el enter"; Start-Sleep 2 }
    if (-not $NoKeys -and $el -ge 30 -and $resumeSent -lt 2) { [System.Windows.Forms.SendKeys]::SendWait('{ENTER}'); $resumeSent++; $log += "t=$el enter2"; Start-Sleep 2 }
    if ($el % 15 -lt 5) { Shot ('shot_{0:000}' -f $el) }
}
$alive = Get-Process tru -ErrorAction SilentlyContinue
Shot 'final'
$res = if ($alive) { 'ALIVE at end (check screenshots: in-level HUD = LOADED; menu/movie = not loaded)' } else { 'EXITED/CRASHED' }
$ev = Get-WinEvent -FilterHashtable @{LogName = 'Application'; StartTime = $startedAt.AddSeconds(-5)} -ErrorAction SilentlyContinue | ? { $_.ProviderName -match 'Application Error' } | Select -First 1
$evt = if ($ev) { ($ev.Message -replace '\s+', ' ') -replace '^.*Codice eccezione: (0x[0-9a-f]+).*Offset errore: (0x[0-9a-f]+).*$', 'exception $1 offset $2' } else { 'no Application Error event' }
if ($ev) { $d = Get-ChildItem C:\TRU_dumps -ErrorAction SilentlyContinue | Sort LastWriteTime | Select -Last 1; if ($d) { Copy-Item $d.FullName "$out\crash.dmp" -Force } }
("RESULT: $res`r`nEVENT: $evt`r`n" + ($log -join "`r`n")) | Out-File "$out\result.txt"
