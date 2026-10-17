# vm_stackdump.ps1 - SOLA LETTURA. Per ogni thread di tru.exe: Eip/Esp/Ebp (GetThreadContext, PowerShell 32 bit) e le parole dello stack
# (fino a 0x6000 byte) che cadono in tru.exe (0x401000..0x840000). Output TSV: thread, eip, esp, indirizzo stack, valore.
# -RawBytes N (default 0): per i primi N byte di ogni stack scrive TUTTE le parole (riga con suffisso RAW), anche i puntatori heap.
param([string]$Out = 'Z:\tru-port\work\crash\stack_live.tsv', [int]$RawBytes = 0)
$ErrorActionPreference = 'Stop'
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class SD {
  [DllImport("kernel32.dll")] public static extern IntPtr OpenProcess(int a, bool b, int pid);
  [DllImport("kernel32.dll")] public static extern IntPtr OpenThread(int a, bool b, int tid);
  [DllImport("kernel32.dll")] public static extern int SuspendThread(IntPtr h);
  [DllImport("kernel32.dll")] public static extern int ResumeThread(IntPtr h);
  [DllImport("kernel32.dll")] public static extern bool GetThreadContext(IntPtr h, byte[] ctx);
  [DllImport("kernel32.dll")] public static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, int n, out int r);
  public static byte[] Read(IntPtr h, long a, int n){ var b=new byte[n]; int r; if(!ReadProcessMemory(h,(IntPtr)a,b,n,out r)) return null; return b; }
}
'@
$p = Get-Process tru | Select-Object -First 1
$hp = [SD]::OpenProcess(0x0410, $false, $p.Id)
$lines = New-Object System.Collections.Generic.List[string]
foreach ($t in $p.Threads) {
  $ht = [SD]::OpenThread(0x0002 -bor 0x0008 -bor 0x0040, $false, $t.Id)   # SUSPEND_RESUME | GET_CONTEXT | QUERY_INFORMATION
  if ($ht -eq [IntPtr]::Zero) { continue }
  $ctx = New-Object byte[] 716; [BitConverter]::GetBytes([uint32]0x10007).CopyTo($ctx, 0)   # CONTEXT_i386 | CONTROL | INTEGER | SEGMENTS
  [void][SD]::SuspendThread($ht); $ok = [SD]::GetThreadContext($ht, $ctx); [void][SD]::ResumeThread($ht)
  if (-not $ok) { continue }
  $eip = [BitConverter]::ToUInt32($ctx, 0xb8); $esp = [BitConverter]::ToUInt32($ctx, 0xc4); $ebp = [BitConverter]::ToUInt32($ctx, 0xb4)
  $lines.Add((("T{0}`t{1:x8}`t{2:x8}`t{3:x8}`tCTX") -f $t.Id, $eip, $esp, $ebp))
  for ($a = [int64]$esp; $a -lt [int64]$esp + 0x6000; $a += $n) {
    $n = 0x1000 - ($a % 0x1000)   # letture allineate alla pagina: un blocco che sconfina oltre la cima dello stack falliva per intero
    $b = [SD]::Read($hp, $a, $n); if ($b -eq $null) { break }
    for ($i = 0; $i -lt $n; $i += 4) {
      $v = [BitConverter]::ToUInt32($b, $i)
      if (($a + $i) -lt ([int64]$esp + $RawBytes)) { $lines.Add((("T{0}`t{1:x8}`t{2:x8}`tRAW") -f $t.Id, ($a + $i), $v)) }
      elseif ($v -ge 0x401000 -and $v -lt 0x840000) { $lines.Add((("T{0}`t{1:x8}`t{2:x8}") -f $t.Id, ($a + $i), $v)) }
    }
  }
}
[IO.File]::WriteAllLines($Out, $lines)
"righe $($lines.Count) thread $($p.Threads.Count)"
