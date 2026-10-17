# Live tail of the TRU engine log WITHOUT the F8 menu: scans the memory of the running 32-bit tru.exe for the hook's log
# buffer (ImGuiTextBuffer; starts with "cdc::JobChainImplWithThreads::StartSystem") and writes its newest/longest copy to a file
# every few seconds (also while the engine error dialog is up). Run with the 32-bit PowerShell (SysWOW64) so pointers are 32-bit:
#   C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_logtail.ps1 [-Out Z:\tru-port\work\live\engine.log] [-Seconds 900] [-Interval 3]
# Read-only on the game process (PROCESS_VM_READ|QUERY); changes nothing.
param([string]$Out = 'Z:\tru-port\work\live\engine.log', [int]$Seconds = 900, [int]$Interval = 3)
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Text; using System.Collections.Generic;
public class LT {
  [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(uint a, bool i, uint pid);
  [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
  [DllImport("kernel32.dll")] static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, int n, out int r);
  [StructLayout(LayoutKind.Sequential)] struct MBI { public IntPtr Base, AllocBase; public uint AllocProt; public IntPtr Size; public uint State, Protect, Type; }
  [DllImport("kernel32.dll")] static extern int VirtualQueryEx(IntPtr h, IntPtr a, out MBI m, int len);
  static byte[] Pat = Encoding.ASCII.GetBytes("cdc::JobChainImplWithThreads::StartSystem");
  public static string Scan(int pid) {
    IntPtr h = OpenProcess(0x0410, false, (uint)pid); if (h == IntPtr.Zero) return null;
    string best = null; long addr = 0x10000; byte[] buf = new byte[1 << 20];
    try {
      while (addr < 0x7FFF0000) {
        MBI m; if (VirtualQueryEx(h, (IntPtr)addr, out m, Marshal.SizeOf(typeof(MBI))) == 0) break;
        long size = (long)m.Size;
        if (m.State == 0x1000 && (m.Protect == 0x04 || m.Protect == 0x40) && m.Type == 0x20000) {   // committed, RW, private
          for (long off = 0; off < size; off += buf.Length - 64) {
            int want = (int)Math.Min(buf.Length, size - off), got;
            if (!ReadProcessMemory(h, (IntPtr)(addr + off), buf, want, out got) || got < Pat.Length) continue;
            for (int i = 0; i <= got - Pat.Length; i++) {
              if (buf[i] != Pat[0]) continue; int k = 1; while (k < Pat.Length && buf[i + k] == Pat[k]) k++;
              if (k != Pat.Length) continue;
              // read the NUL-terminated string starting here (up to 16 MB)
              List<byte> sb = new List<byte>(); long p = addr + off + i; byte[] one = new byte[65536];
              while (sb.Count < (16 << 20)) { int r; if (!ReadProcessMemory(h, (IntPtr)p, one, one.Length, out r) || r == 0) break;
                int z = Array.IndexOf(one, (byte)0, 0, r); if (z >= 0) { for (int j = 0; j < z; j++) sb.Add(one[j]); break; }
                for (int j = 0; j < r; j++) sb.Add(one[j]); p += r; }
              string s = Encoding.GetEncoding(1252).GetString(sb.ToArray());
              if (best == null || s.Length > best.Length) best = s;
            }
          }
        }
        addr += size; if (size == 0) break;
      }
    } finally { CloseHandle(h); }
    return best;
  }
}
"@
New-Item -ItemType Directory -Force (Split-Path $Out) | Out-Null
$t0 = Get-Date; $last = 0
$swc = [Diagnostics.Stopwatch]::StartNew()   # cronometro: immune ai salti dell'orologio della VM
while ($swc.Elapsed.TotalSeconds -lt $Seconds) {
  $p = Get-Process tru -ErrorAction SilentlyContinue | Select -First 1
  if ($p) {
    $s = [LT]::Scan($p.Id)
    if ($s -and $s.Length -ge $last) { [IO.File]::WriteAllText($Out, $s, [Text.Encoding]::UTF8); $last = $s.Length }
  }
  Start-Sleep $Interval
}
