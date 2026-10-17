# vm_script_state.ps1 - fotografia dei MEMBRI (dati istanza) degli script DLC in esecuzione. Solo lettura (OpenProcess 0x0410 + ReadProcessMemory).
# Trova in memoria la radice del tipo script (pattern byte da work\ws\shader4\script_state_patterns.json: +0..+0xc e +0x1c..+0x20), poi gli
# oggetti script (ScriptObject: +8 = puntatore al tipo, +0xC = puntatore ai dati dei membri), e salva i byte dei dati.
#   C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_script_state.ps1 -Label prima
# Output: work\live\script_state_<Label>.json  (da leggere con work\ws\shader4\script_state_read.py)
param([string]$Label = 'snap', [string]$Patterns = 'Z:\tru-port\work\ws\shader4\script_state_patterns.json',
      [string]$OutDir = 'Z:\tru-port\work\live')
$ErrorActionPreference = 'Stop'
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Collections.Generic;
public class SS {
  [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(uint a, bool i, uint pid);
  [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
  [DllImport("kernel32.dll")] static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, int n, out int r);
  [StructLayout(LayoutKind.Sequential)] struct MBI { public IntPtr Base, AllocBase; public uint AllocProt; public IntPtr Size; public uint State, Protect, Type; }
  [DllImport("kernel32.dll")] static extern int VirtualQueryEx(IntPtr h, IntPtr a, out MBI m, int len);
  public IntPtr H;
  public SS(int pid) { H = OpenProcess(0x0410, false, (uint)pid); if (H == IntPtr.Zero) throw new Exception("OpenProcess fallita"); }
  public void Close() { CloseHandle(H); }
  bool Readable(MBI m) { return m.State == 0x1000 && (m.Protect & 0x100) == 0 && (m.Protect & 0x01) == 0 && m.Protect != 0; }
  public byte[] Read(long a, int n) { byte[] b = new byte[n]; int got; if (!ReadProcessMemory(H, (IntPtr)a, b, n, out got) || got < n) return null; return b; }
  // indirizzi dove compare 'a' (8 byte) a X e 'b' a X+boff (X allineato a 4)
  public List<long> FindType(byte[] a, byte[] b, int boff) {
    List<long> res = new List<long>(); long addr = 0x10000; byte[] buf = new byte[1 << 20];
    while (addr < 0xFFFF0000L) {
      MBI m; if (VirtualQueryEx(H, (IntPtr)addr, out m, Marshal.SizeOf(typeof(MBI))) == 0) break;
      long size = (long)m.Size; if (size == 0) break;
      if (Readable(m)) for (long off = 0; off < size; off += buf.Length - 64) {
        int want = (int)Math.Min(buf.Length, size - off), got;
        if (!ReadProcessMemory(H, (IntPtr)(addr + off), buf, want, out got) || got < 64) continue;
        for (int i = 0; i + boff + b.Length <= got; i += 4) {
          if (buf[i] != a[0]) continue; bool ok = true;
          for (int k = 1; k < a.Length && ok; k++) if (buf[i + k] != a[k]) ok = false;
          for (int k = 0; k < b.Length && ok; k++) if (buf[i + boff + k] != b[k]) ok = false;
          if (ok) res.Add(addr + off + i);
        }
      }
      addr += size;
    }
    return res;
  }
  // indirizzi di dword uguali a 'target' (allineati a 4)
  public List<long> FindDword(uint target) {
    List<long> res = new List<long>(); long addr = 0x10000; byte[] buf = new byte[1 << 20];
    while (addr < 0xFFFF0000L) {
      MBI m; if (VirtualQueryEx(H, (IntPtr)addr, out m, Marshal.SizeOf(typeof(MBI))) == 0) break;
      long size = (long)m.Size; if (size == 0) break;
      if (Readable(m)) for (long off = 0; off < size; off += buf.Length - 64) {
        int want = (int)Math.Min(buf.Length, size - off), got;
        if (!ReadProcessMemory(H, (IntPtr)(addr + off), buf, want, out got) || got < 4) continue;
        for (int i = 0; i + 4 <= got; i += 4) if (BitConverter.ToUInt32(buf, i) == target) res.Add(addr + off + i);
      }
      addr += size;
    }
    return res;
  }
}
"@
$pat = Get-Content $Patterns -Raw | ConvertFrom-Json
$proc = Get-Process -Name tru -ErrorAction Stop | Select-Object -First 1
$ss = New-Object SS($proc.Id)
function HexToBytes([string]$h) { $b = New-Object byte[] ($h.Length / 2); for ($i = 0; $i -lt $b.Length; $i++) { $b[$i] = [Convert]::ToByte($h.Substring(2 * $i, 2), 16) }; return $b }
$result = [ordered]@{ label = $Label; pid = $proc.Id; time = (Get-Date -Format s); scripts = @() }
try {
  foreach ($prop in $pat.PSObject.Properties) {
    $sid = $prop.Name; $p = $prop.Value
    $types = $ss.FindType((HexToBytes $p.a), (HexToBytes $p.b), 0x1c)
    $entry = [ordered]@{ script = [int]$sid; size = $p.size; types = @() }
    foreach ($t in $types) {
      $objs = @()
      foreach ($ref in $ss.FindDword([uint32]$t)) {
        $o = $ref - 8; $hdr = $ss.Read($o, 0x1c); if ($hdr -eq $null) { continue }
        $inst = [BitConverter]::ToUInt32($hdr, 0xC); if ($inst -lt 0x10000) { continue }
        $data = $ss.Read($inst, [int]$p.size); if ($data -eq $null) { continue }
        $objs += [ordered]@{ obj = $o; inst = $inst; hex = ([BitConverter]::ToString($data) -replace '-', '') }
      }
      $entry.types += [ordered]@{ type = $t; objects = $objs }
    }
    $result.scripts += $entry
    "script $sid : tipi trovati $($types.Count), oggetti $(($entry.types | ForEach-Object { $_.objects.Count } | Measure-Object -Sum).Sum)" | Write-Host
  }
} finally { $ss.Close() }
New-Item -ItemType Directory -Force $OutDir | Out-Null
$f = Join-Path $OutDir "script_state_$Label.json"
$result | ConvertTo-Json -Depth 8 | Set-Content -Encoding ASCII $f
"salvato $f" | Write-Host
