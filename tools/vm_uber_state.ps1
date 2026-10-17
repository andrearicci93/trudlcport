# vm_uber_state.ps1 - SOLA LETTURA: stato delle parti UberObject di un componente (nodo corrente, transizione, flag) e
# posizione delle istanze parte. PowerShell 32 bit. Uso: vm_uber_state.ps1 -Comp 0x185510c0 [-Loop 0] [-Every 0.5]
param([string]$Comp, [int]$Loop = 0, [double]$Every = 0.5)
$ErrorActionPreference = 'Stop'
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class UbR {
  [DllImport("kernel32.dll")] public static extern IntPtr OpenProcess(int a, bool b, int pid);
  [DllImport("kernel32.dll")] public static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, int n, out int r);
  public static byte[] Read(IntPtr h, long a, int n){ var b=new byte[n]; int r; ReadProcessMemory(h,(IntPtr)a,b,n,out r); return b; }
  public static uint U(IntPtr h, long a){ return BitConverter.ToUInt32(Read(h,a,4),0); }
  public static float F(IntPtr h, long a){ return BitConverter.ToSingle(Read(h,a,4),0); }
}
'@
$pr = Get-Process tru | Select-Object -First 1
$h = [UbR]::OpenProcess(0x0410, $false, $pr.Id)
$c = [Convert]::ToInt64($Comp, 16)
$n = 0
do {
  $parts = [UbR]::U($h, $c + 0x6c); $np = [UbR]::U($h, $c + 0x70)
  $line = ('{0:HH:mm:ss.fff} comp {1:X} parti {2}' -f (Get-Date), $c, $np)
  for ($i = 0; $i -lt $np; $i++) {
    $inst = [UbR]::U($h, $parts + 8 * $i)
    if ($inst -eq 0) { $line += " | p$i null"; continue }
    $x = [UbR]::U($h, $inst + 0x2d0); $u = 0
    if ($x -ne 0) { $u = [UbR]::U($h, [UbR]::U($h, $x) + 0x2ec) }
    $pos = '{0:F1},{1:F1},{2:F1}' -f [UbR]::F($h, $inst + 0x20), [UbR]::F($h, $inst + 0x24), [UbR]::F($h, $inst + 0x28)
    if ($u -ne 0 -and [UbR]::U($h, $u + 0x60) -eq [uint32]4026606405) {
      $b = $u - 0x10
      $line += (' | p{0} inst {1:X} pos {2} nodo {3} trans {4:X} f90 {5:X} t88 {6:F2}' -f $i, $inst, $pos, [int][UbR]::U($h, $b + 0x84), [UbR]::U($h, $b + 0x80), [UbR]::U($h, $b + 0x90), [UbR]::F($h, $b + 0x88))
    } else { $line += (' | p{0} inst {1:X} pos {2} (no uber)' -f $i, $inst, $pos) }
  }
  $line
  $n++
  if ($Loop -gt 0) { Start-Sleep -Milliseconds ([int]($Every * 1000)) }
} while ($n -lt $Loop)
