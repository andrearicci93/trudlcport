# Forces an access violation inside the running 32-bit tru.exe so WER LocalDumps writes a full dump (all thread stacks) to C:\TRU_dumps. Run with SysWOW64 powershell.
Add-Type @"
using System; using System.Runtime.InteropServices;
public class FC { [DllImport("kernel32.dll")] public static extern IntPtr OpenProcess(uint a, bool i, uint pid);
 [DllImport("kernel32.dll")] public static extern IntPtr CreateRemoteThread(IntPtr h, IntPtr sa, uint ss, IntPtr start, IntPtr p, uint fl, out uint tid); }
"@
$p = Get-Process tru
$h = [FC]::OpenProcess(0x1FFFFF, $false, [uint32]$p.Id)
$tid = 0
$t = [FC]::CreateRemoteThread($h, [IntPtr]::Zero, 0, [IntPtr]4, [IntPtr]::Zero, 0, [ref]$tid)
"thread=$t tid=$tid"
