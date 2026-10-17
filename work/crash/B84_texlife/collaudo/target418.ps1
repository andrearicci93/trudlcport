# Bersaglio di collaudo per vm_watch418.ps1: blocco con valori noti, cambi temporizzati. Solo nella propria memoria.
$m = [Runtime.InteropServices.Marshal]::AllocHGlobal(0x2000)
$b = [int64]$m
function W($off, $v) { [Runtime.InteropServices.Marshal]::WriteInt32([IntPtr]($b + $off), [int]$v) }
W 0 0x8494ec; W 0x418 0x11111111; W 0xc54 0x11111111; W 0xc50 1
Set-Content $env:TEMP\target418.txt ('{0:x8}' -f $b)
Start-Sleep 4; W 0x418 0x22222222
Start-Sleep 31; W 0 0x848c3c
Start-Sleep 3
