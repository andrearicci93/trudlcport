# vm_probe.ps1 - standalone read-only probe of the running 32-bit tru.exe (raft_bridge chain-shot diagnosis). See work/ws/probe/README.md.
#   C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_probe.ps1 -Mode raft -Seconds 120 [-RunId r1] [-Out file.tsv] [-IntervalMs 100]
# Writes nothing into the game process (OpenProcess 0x0410 + ReadProcessMemory only). Logic lives in vm_probe_raft_lib.ps1 (same folder).
param(
  [ValidateSet('raft', 'lists')][string]$Mode = 'raft',
  [string]$Out,
  [string]$RunId,
  [int]$Seconds = 60,
  [int]$IntervalMs = 100,
  [int]$HeartbeatSec = 5,
  [int]$WaitProcess = 20,
  [int]$ProcId = 0
)
. (Join-Path $PSScriptRoot 'vm_probe_raft_lib.ps1')
$rc = @(Invoke-TruProbe -Mode $Mode -Out $Out -RunId $RunId -Seconds $Seconds -IntervalMs $IntervalMs -HeartbeatSec $HeartbeatSec -WaitProcess $WaitProcess -ProcId $ProcId)
exit [int]$rc[-1]
