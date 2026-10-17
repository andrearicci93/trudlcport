# Giro 6: attende un crash di tru.exe (comparsa di WerFault.exe o fine anomala) e scatta un dump COMPLETO del processo ancora vivo (read-only),
# poi salva anche l'ultimo engine.log (vm_logtail va lanciato a parte). Eseguire con SysWOW64 PowerShell.
param([string]$OutDir = 'Z:\tru-port\work\crash\B89_live', [int]$Seconds = 5400)
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
Add-Type @"
using System; using System.Runtime.InteropServices;
public class DD2 { [DllImport("dbghelp.dll", SetLastError=true)] public static extern bool MiniDumpWriteDump(IntPtr h, uint pid, IntPtr f, int type, IntPtr e, IntPtr u, IntPtr c); }
"@
$end = (Get-Date).AddSeconds($Seconds); $done = $false
"watch start " + (Get-Date -Format s) | Out-File "$OutDir\watch.txt"
while ((Get-Date) -lt $end -and -not $done) {
  Start-Sleep -Milliseconds 500
  $w = Get-Process WerFault -ErrorAction SilentlyContinue
  $t = Get-Process tru -ErrorAction SilentlyContinue
  if ($w -and $t) {
    Start-Sleep -Seconds 2
    $p = Get-Process tru -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $p) { continue }
    $f = "$OutDir\B89_live.dmp"; $fs = [System.IO.File]::Create($f)
    $ok = [DD2]::MiniDumpWriteDump($p.Handle, $p.Id, $fs.SafeFileHandle.DangerousGetHandle(), 0x1006, [IntPtr]::Zero, [IntPtr]::Zero, [IntPtr]::Zero)
    $fs.Close(); "dump ok=$ok size=" + (Get-Item $f).Length + " at " + (Get-Date -Format s) | Out-File "$OutDir\watch.txt" -Append
    $done = $true
  }
}
"watch end " + (Get-Date -Format s) | Out-File "$OutDir\watch.txt" -Append
