# dump_once.ps1 - un solo dump completo (sola lettura) del processo tru.exe, come TruLive (tipo 0x1006). Uso (PowerShell 32 bit):
#   %SystemRoot%\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File dump_once.ps1 -Out <cartella> -Tag <nome>
param([string]$Out, [string]$Tag = "m")
Add-Type @"
using System; using System.IO; using System.Runtime.InteropServices;
public static class D1 {
  [DllImport("dbghelp.dll", SetLastError = true)] static extern bool MiniDumpWriteDump(IntPtr h, uint pid, IntPtr f, int type, IntPtr e, IntPtr u, IntPtr c);
  public static string Go(System.Diagnostics.Process p, string path) {
    using (FileStream fs = File.Create(path)) {
      bool ok = MiniDumpWriteDump(p.Handle, (uint)p.Id, fs.SafeFileHandle.DangerousGetHandle(), 0x1006, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero);
      return ok ? "OK" : ("FALLITO " + Marshal.GetLastWin32Error());
    }
  }
}
"@
$p = Get-Process tru -ErrorAction Stop | Select-Object -First 1
New-Item -ItemType Directory -Force $Out | Out-Null
$f = Join-Path $Out ("dump_" + (Get-Date -Format HHmmss) + "_" + $Tag + ".dmp")
$sw = [Diagnostics.Stopwatch]::StartNew()
$r = [D1]::Go($p, $f)
"{0} {1} {2} MB in {3} s (pid {4})" -f $r, $f, [int]((Get-Item $f).Length / 1MB), [int]$sw.Elapsed.TotalSeconds, $p.Id
