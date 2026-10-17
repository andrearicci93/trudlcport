# Full dump of the running 32-bit tru.exe via 32-bit PowerShell + dbghelp (run with C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe)
param([string]$Out = 'C:\TRU_dumps\live.dmp')
Add-Type @"
using System; using System.Runtime.InteropServices;
public class DD { [DllImport("dbghelp.dll", SetLastError=true)] public static extern bool MiniDumpWriteDump(IntPtr h, uint pid, IntPtr f, int type, IntPtr e, IntPtr u, IntPtr c); }
"@
$p = Get-Process tru
$fs = [System.IO.File]::Create($Out)
# 0x2 = MiniDumpWithFullMemory | 0x4 handle data | 0x1000 thread info
$ok = [DD]::MiniDumpWriteDump($p.Handle, $p.Id, $fs.SafeFileHandle.DangerousGetHandle(), 0x1006, [IntPtr]::Zero, [IntPtr]::Zero, [IntPtr]::Zero)
$fs.Close()
"ok=$ok err=" + [Runtime.InteropServices.Marshal]::GetLastWin32Error() + " size=" + (Get-Item $Out).Length
