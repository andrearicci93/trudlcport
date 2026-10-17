# vm_read_ltg.ps1 - legge (sola lettura) i contatori della guardia light_tex_guard nel tru.exe in esecuzione: 8 dword a VA 0x83DE20
# (magic 'LTG1'=0x3147544C, calls, fix, valid, last_bad_P, last_X, 0, 0). Lanciare con la PowerShell a 32 bit:
#   C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_read_ltg.ps1 [-Out Z:\...\ltg.txt]
param([string]$Out = '')
Add-Type @"
using System; using System.Runtime.InteropServices;
public class RPM { [DllImport("kernel32.dll", SetLastError=true)] public static extern IntPtr OpenProcess(uint a, bool i, uint pid);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, int n, out int r);
  [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr h); }
"@
$p = Get-Process tru -ErrorAction SilentlyContinue
if (-not $p) { $m = 'tru non in esecuzione'; if ($Out) { $m | Set-Content $Out }; $m; exit 1 }
$h = [RPM]::OpenProcess(0x0410, $false, [uint32]$p.Id)
$b = New-Object byte[] 32; $n = 0
$ok = [RPM]::ReadProcessMemory($h, [IntPtr]0x83DE20, $b, 32, [ref]$n)
[RPM]::CloseHandle($h) | Out-Null
$names = 'magic','calls','fix','valid','last_bad_P','last_X','r6','r7'
$lines = @("pid=$($p.Id) ok=$ok read=$n")
if ($ok) { for ($i = 0; $i -lt 8; $i++) { $lines += ('{0}=0x{1:X8} ({1})' -f $names[$i], [BitConverter]::ToUInt32($b, 4 * $i)) } }
if ($Out) { $lines | Set-Content -Encoding ASCII $Out }
$lines
