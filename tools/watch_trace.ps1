# watch_trace.ps1 - registratore passivo (SOLA LETTURA) della posizione di Lara ogni -IntervalMs, per qualunque sessione di tru.exe (anche piu' avvii).
# Scrive Z:\tru-port\work\live\lara_trace.log: riga = ora, uptime processo, ptr Lara ([0xe7f094]), posizione (+0x20..0x28) o NOLARA; segna ogni cambio di ptr Lara (rinascita/ricarica).
# Uso (32 bit): C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\watch_trace.ps1 [-Seconds 3600] [-IntervalMs 500] [-Out file]
param([int]$Seconds = 3600, [int]$IntervalMs = 500, [string]$Out = 'Z:\tru-port\work\live\lara_trace.log')
$cs = @'
using System; using System.Runtime.InteropServices;
public static class WT {
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr OpenProcess(uint a, bool i, uint pid);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, IntPtr n, out IntPtr g);
  [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
  public static IntPtr Open(uint pid) { return OpenProcess(0x0010 | 0x0400, false, pid); }
  public static byte[] Rd(IntPtr h, uint va, int n) { byte[] b = new byte[n]; IntPtr g; if (!ReadProcessMemory(h, new IntPtr(unchecked((int)va)), b, new IntPtr(n), out g) || g.ToInt64() != n) return null; return b; }
  public static void Close(IntPtr h) { CloseHandle(h); }
}
'@
Add-Type -TypeDefinition $cs
New-Item -ItemType Directory -Force (Split-Path $Out) | Out-Null
$t0 = Get-Date; $h = [IntPtr]::Zero; $curPid = 0; $lastPtr = [uint32]4294967295
function W([string]$m) { Add-Content -LiteralPath $Out -Value ('{0:HH:mm:ss.fff} {1}' -f (Get-Date), $m) }
W 'WATCH_START'
while (((Get-Date) - $t0).TotalSeconds -lt $Seconds) {
  $p = Get-Process -Name tru -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -eq $p) { if ($h -ne [IntPtr]::Zero) { [WT]::Close($h); $h = [IntPtr]::Zero; W 'TRU_TERMINATO'; $curPid = 0; $lastPtr = [uint32]4294967295 }; Start-Sleep -Milliseconds 700; continue }
  if ($p.Id -ne $curPid) { if ($h -ne [IntPtr]::Zero) { [WT]::Close($h) }; $h = [WT]::Open([uint32]$p.Id); $curPid = $p.Id; W ('TRU_AVVIATO pid=' + $p.Id) }
  $b = [WT]::Rd($h, 0xe7f094, 4)
  if ($null -eq $b) { W 'LETTURA_FALLITA'; Start-Sleep -Milliseconds $IntervalMs; continue }
  $ptr = [BitConverter]::ToUInt32($b, 0)
  if ($ptr -ne $lastPtr) { W ('LARA_PTR_CAMBIATO {0:X} -> {1:X}' -f $lastPtr, $ptr); $lastPtr = $ptr }
  if ($ptr -eq 0) { W 'NOLARA' }
  else {
    $q = [WT]::Rd($h, $ptr + 0x20, 12)
    if ($null -ne $q) { W ('LARA {0:F1} {1:F1} {2:F1}' -f [BitConverter]::ToSingle($q, 0), [BitConverter]::ToSingle($q, 4), [BitConverter]::ToSingle($q, 8)) }
  }
  Start-Sleep -Milliseconds $IntervalMs
}
W 'WATCH_FINE'
