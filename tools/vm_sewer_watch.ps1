# vm_sewer_watch.ps1 - SOLA LETTURA. Segue il tap (righe probe13 = spawn delle parti UberObject, ecx=componente, arg0=istanza) e, per ogni
# componente la cui istanza ha introID (+0x58) = $Intro, registra ogni $Every s: per parte posizione (x,y,z), nodo (+0x84), transizione (+0x80),
# flag (+0x90), tempo nel nodo (+0x88). PowerShell 32 bit. Richiede l'exe tap probe_attach (probe13 su 0x4d5039).
#   ...\SysWOW64\...\powershell.exe -File Z:\tru-port\tools\vm_sewer_watch.ps1 -Tag B84_attach -Intro 9759
param([string]$Tag = 'sessione', [int]$Intro = 9759, [double]$Every = 0.25, [int]$Seconds = 10800)
$ErrorActionPreference = 'Stop'
$tap = "Z:\tru-port\work\taps\$Tag\tap.tsv"; $out = "Z:\tru-port\work\live\sewer_$Tag.log"
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class SwR {
  [DllImport("kernel32.dll")] public static extern IntPtr OpenProcess(int a, bool b, int pid);
  [DllImport("kernel32.dll")] public static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, int n, out int r);
  public static byte[] Read(IntPtr h, long a, int n){ var b=new byte[n]; int r; ReadProcessMemory(h,(IntPtr)a,b,n,out r); return b; }
  public static uint U(IntPtr h, long a){ return BitConverter.ToUInt32(Read(h,a,4),0); }
  public static float F(IntPtr h, long a){ return BitConverter.ToSingle(Read(h,a,4),0); }
}
'@
$ci = [Globalization.CultureInfo]::InvariantCulture
[Threading.Thread]::CurrentThread.CurrentCulture = $ci
function W($s) { Add-Content -Path $out -Value $s -Encoding ASCII }
W ("start {0:s} tag {1} intro {2}" -f (Get-Date), $Tag, $Intro)
$sw = [Diagnostics.Stopwatch]::StartNew(); $pid0 = 0; $h = [IntPtr]::Zero; $pos = 0; $comps = @{}; $last = @{}
while ($sw.Elapsed.TotalSeconds -lt $Seconds) {
  $p = Get-Process tru -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $p) { Start-Sleep 2; continue }
  if ($p.Id -ne $pid0) { $pid0 = $p.Id; $h = [SwR]::OpenProcess(0x0410, $false, $p.Id); $comps = @{}; W ("processo {0}" -f $p.Id) }
  if (Test-Path $tap) {
    $fs = [IO.File]::Open($tap, 'Open', 'Read', 'ReadWrite'); [void]$fs.Seek($pos, 'Begin')
    $sr = New-Object IO.StreamReader($fs); $txt = $sr.ReadToEnd(); $pos = $fs.Position; $sr.Close()
    foreach ($m in [regex]::Matches($txt, 'probe13 ecx=([0-9a-fA-F]+) edx=\S+ args 0x([0-9a-fA-F]+)')) {
      $c = [Convert]::ToInt64($m.Groups[1].Value, 16); $i = [Convert]::ToInt64($m.Groups[2].Value, 16)
      $iid = [SwR]::U($h, $i + 0x58) -band 0xffff
      if ($iid -eq $Intro -and -not $comps.ContainsKey($c)) { $comps[$c] = $i; W ("{0:HH:mm:ss.fff} trovato componente {1:X} istanza {2:X} intro {3}" -f (Get-Date), $c, $i, $iid) }
    }
  }
  foreach ($c in @($comps.Keys)) { try {
    $parts = [SwR]::U($h, $c + 0x6c); $np = [SwR]::U($h, $c + 0x70)
    if ($np -lt 1 -or $np -gt 8) { W ("{0:HH:mm:ss.fff} comp {1:X} non valido (np {2}), rimosso" -f (Get-Date), $c, $np); $comps.Remove($c); continue }
    $line = '{0:HH:mm:ss.fff} comp {1:X}' -f (Get-Date), $c; $key = ''
    for ($k = 0; $k -lt $np; $k++) {
      $inst = [SwR]::U($h, $parts + 8 * $k); if ($inst -eq 0) { $line += " | p$k null"; continue }
      $x = [SwR]::U($h, $inst + 0x2d0); $u = 0; if ($x -ne 0) { $u = [SwR]::U($h, [SwR]::U($h, $x) + 0x2ec) }
      $xyz = ('{0:F1} {1:F1} {2:F1}' -f [SwR]::F($h, $inst + 0x20), [SwR]::F($h, $inst + 0x24), [SwR]::F($h, $inst + 0x28))
      if ($u -ne 0 -and [SwR]::U($h, $u + 0x60) -eq [uint32]4026606405) {
        $b = $u - 0x10; $nd = [int][SwR]::U($h, $b + 0x84)
        $line += (' | p{0} {1} nodo {2} tr {3:X} f {4:X} t {5:F2}' -f $k, $xyz, $nd, [SwR]::U($h, $b + 0x80), [SwR]::U($h, $b + 0x90), [SwR]::F($h, $b + 0x88))
        $key += "${k}:${nd}:${xyz};"
      } else { $line += " | p$k $xyz (no uber)"; $key += "${k}:${xyz};" }
    }
    W $line
  } catch { W ('ERRORE comp {0:X}: {1}' -f $c, $_.Exception.Message) } }
  Start-Sleep -Milliseconds ([int]($Every * 1000))
}
