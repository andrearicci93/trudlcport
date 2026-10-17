# auto_ring_test.ps1 - test AUTOMATICO (nessun utente) dell'anello della zattera, PowerShell 32 bit (SysWOW64).
# 1) legge dalla memoria di tru.exe i record tag 0x404 (portata personalizzata) degli anelli in lista 1 (istanza +0x104, poi genitore +0x4c);
# 2) porta Lara (scrittura di [Lara]+0x20..0x28 a ~60 Hz) a distanze/azimut dati dall'anello 9755 e registra gli istanti: l'indice di sotto-lista degli
#    anelli si legge poi dal TSV della sonda 'lists' (vm_probe) con work/ws/progress/analyze_ring_test.py.
# Scrive SOLO la posizione di Lara (3 float), poi la ripristina. Log: work\runs\<RunId>\ringtest.log
param(
  [string]$RunId = 'x',
  [int]$HoldMs = 4500,
  [double[]]$Dists = @(1500, 2500, 3500, 4800, 5400, 5900, 6200, 6600),
  [double[]]$AzDeg = @(84, 20, 160, 250),     # 84 gradi ~ direzione da cui arriva la zattera (da anello verso (+0.134,+0.991))
  [double]$ZLara = -14265.7,
  [double[]]$Ring = @(-268.2, 5086.7, -13711.9)
)
$ErrorActionPreference = 'Stop'
$cs = @'
using System; using System.Runtime.InteropServices;
public static class RN {
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr OpenProcess(uint a, bool i, uint pid);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, IntPtr n, out IntPtr g);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool WriteProcessMemory(IntPtr h, IntPtr a, byte[] b, IntPtr n, out IntPtr g);
  [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
  public static IntPtr Open(uint pid) { return OpenProcess(0x0010 | 0x0020 | 0x0400 | 0x0008, false, pid); }
  public static byte[] Rd(IntPtr h, uint va, int n) { byte[] b = new byte[n]; IntPtr g; if (!ReadProcessMemory(h, new IntPtr(unchecked((int)va)), b, new IntPtr(n), out g) || g.ToInt64() != n) return null; return b; }
  public static bool Wr(IntPtr h, uint va, byte[] b) { IntPtr g; return WriteProcessMemory(h, new IntPtr(unchecked((int)va)), b, new IntPtr(b.Length), out g) && g.ToInt64() == b.Length; }
  public static void Close(IntPtr h) { CloseHandle(h); }
}
'@
Add-Type -TypeDefinition $cs
$dir = "Z:\tru-port\work\runs\$RunId"; New-Item -ItemType Directory -Force $dir | Out-Null
$log = "$dir\ringtest.log"
function Say([string]$m) { $l = ('{0:HH:mm:ss.fff} {1}' -f (Get-Date), $m); Add-Content -LiteralPath $log -Value $l }
function U32($h, [uint32]$a) { $b = [RN]::Rd($h, $a, 4); if ($null -eq $b) { return [uint32]0 }; [BitConverter]::ToUInt32($b, 0) }
function F32($h, [uint32]$a) { $b = [RN]::Rd($h, $a, 4); if ($null -eq $b) { return [single]::NaN }; [BitConverter]::ToSingle($b, 0) }

# --- attesa processo e sonda
$p = $null; $t0 = Get-Date
while (((Get-Date) - $t0).TotalSeconds -lt 240) { $p = Get-Process -Name tru -ErrorAction SilentlyContinue | Select-Object -First 1; if ($p) { break }; Start-Sleep 2 }
if (-not $p) { Say 'NO_PROCESS'; exit 2 }
$tsv = $null
while (((Get-Date) - $t0).TotalSeconds -lt 300) {
  $f = Get-ChildItem -Path "$dir\a*\probe_ext_ext_lists.tsv" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
  if ($f -and ((Get-Content -LiteralPath $f.FullName -ErrorAction SilentlyContinue | Select-String -SimpleMatch '# SNAPSHOT').Count -ge 8)) { $tsv = $f.FullName; break }
  Start-Sleep 3
}
if (-not $tsv) { Say 'NO_PROBE_TSV'; exit 3 }
Say ("START pid={0} tsv={1}" -f $p.Id, $tsv)
$h = [RN]::Open([uint32]$p.Id)
try {
  try {
  # --- 1) record 0x404 degli anelli (ultima istantanea della lista 1)
  $lines = Get-Content -LiteralPath $tsv
  $last = ($lines | Select-String -SimpleMatch '# SNAPSHOT' | Select-Object -Last 1).LineNumber
  $seen = @{}
  for ($i = $last; $i -lt $lines.Count; $i++) {
    $c = $lines[$i] -split "`t"
    if ($c.Count -ge 20 -and $c[0] -eq '1' -and $c[7] -like '0x*') {
      $inst = [Convert]::ToUInt32($c[7].Substring(2), 16); $uid = $c[19]; if ($uid -eq '-1') { $uid = $c[11] }
      if ($seen.ContainsKey($inst)) { continue }; $seen[$inst] = 1
      $ptr = U32 $h ($inst + 0x104); $par = U32 $h ($inst + 0x4c); $src = 'inst'
      if ($ptr -eq 0 -and $par -ne 0) { $ptr = U32 $h ($par + 0x104); $src = 'parent' }
      if ($ptr -ne 0) {
        $tag = U32 $h $ptr; $fl = [RN]::Rd($h, $ptr + 4, 4); $a = F32 $h ($ptr + 8); $b2 = F32 $h ($ptr + 12)
        $fls = (($fl | ForEach-Object { $_.ToString('X2') }) -join '')
        Say ('RECORD par_uid={0} inst={1:X} {2} +0x104={3:X} tag={4:X} flagbytes={5} f8={6:F1} fc={7:F1}' -f $uid, $inst, $src, $ptr, $tag, $fls, $a, $b2)
      } else { Say ('RECORD par_uid={0} inst={1:X} nessun record (+0x104 nullo, parent {2:X})' -f $uid, $inst, $par) }
    }
  }
  # --- 2) posizione di Lara e prove di distanza
  $lara = U32 $h 0xe7f094
  if ($lara -eq 0) { Say 'LARA nullo'; exit 4 }
  $orig = [RN]::Rd($h, $lara + 0x20, 12)
  Say ('LARA ptr={0:X} pos={1:F1},{2:F1},{3:F1}' -f $lara, [BitConverter]::ToSingle($orig, 0), [BitConverter]::ToSingle($orig, 4), [BitConverter]::ToSingle($orig, 8))
  foreach ($az in $AzDeg) {
    foreach ($d in $Dists) {
      $x = $Ring[0] + $d * [Math]::Cos($az * [Math]::PI / 180); $y = $Ring[1] + $d * [Math]::Sin($az * [Math]::PI / 180)
      $buf = New-Object byte[] 12
      [BitConverter]::GetBytes([single]$x).CopyTo($buf, 0); [BitConverter]::GetBytes([single]$y).CopyTo($buf, 4); [BitConverter]::GetBytes([single]$ZLara).CopyTo($buf, 8)
      Say ('HOLD_START az={0} d={1} pos={2:F1},{3:F1},{4:F1}' -f $az, $d, $x, $y, $ZLara)
      $e = Get-Date
      while (((Get-Date) - $e).TotalMilliseconds -lt $HoldMs) {
        if ($null -eq (Get-Process -Id $p.Id -ErrorAction SilentlyContinue)) { Say 'tru terminato'; exit 5 }
        [void][RN]::Wr($h, $lara + 0x20, $buf); Start-Sleep -Milliseconds 15
      }
      Say ('HOLD_END az={0} d={1}' -f $az, $d)
    }
  }
  [void][RN]::Wr($h, $lara + 0x20, $orig); Say 'RESTORED'
  } catch { Say ('ERRORE: ' + $_.Exception.Message + ' @ ' + $_.InvocationInfo.ScriptLineNumber); exit 9 }
} finally { [RN]::Close($h) }
Say 'DONE'
