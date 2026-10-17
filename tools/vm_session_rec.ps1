# vm_session_rec.ps1 - aspetta l'avvio di tru.exe, poi registra TUTTA la sessione: log motore (vm_logtail) + tap (vm_tap_reader).
# Solo lettura sulla memoria del gioco. Lanciare con il PowerShell a 32 bit:
#   C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_session_rec.ps1 -Tag B83_cancello
# Output: work\live\engine_<Tag>.log, work\taps\<Tag>\ (tap.tsv, tap_summary.tsv, status.txt)
param([string]$Tag = 'sessione', [int]$WaitStartSeconds = 3600, [int]$RecordSeconds = 10800,
      [string]$Sites = 'Z:\tru-port\work\ws\tap\probe_ret\sites_patched.tsv', [int]$MaxPerSite = 3000,   # tetto righe per sito (anche sonde): oltre, solo nel riepilogo
      [switch]$ProcDump,   # ProcDump (C:\Tools\procdump) agganciato a tru.exe: dump completo alla prima eccezione NON gestita
      [switch]$Watch418)   # osservatore sola lettura di X+0x418 (tools/vm_watch418.ps1; serve l'exe work/ws/tap/probe_light)
$ErrorActionPreference = 'Stop'
$ps = 'C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
$sw = [Diagnostics.Stopwatch]::StartNew()   # cronometro: immune ai salti dell'orologio della VM
while (-not (Get-Process -Name tru -ErrorAction SilentlyContinue)) {
    if ($sw.Elapsed.TotalSeconds -gt $WaitStartSeconds) { 'tru.exe non avviato entro il tempo' | Write-Host; exit 6 }
    Start-Sleep -Seconds 3
}
if ($ProcDump) {
    $tp = Get-Process -Name tru | Select-Object -First 1
    $pd = Start-Process 'C:\Tools\procdump\procdump.exe' -PassThru -WindowStyle Hidden -RedirectStandardOutput "Z:\tru-port\work\live\procdump_$Tag.log" -ArgumentList @('-accepteula','-ma','-e',$tp.Id,"C:\CrashDumps\$($Tag)_crash.dmp")
    "procdump PID $($pd.Id) su tru PID $($tp.Id) -> C:\CrashDumps\$($Tag)_crash.dmp" | Write-Host
}
Start-Sleep -Seconds 20   # il tap e il log del motore esistono solo dopo l'init
$a = Start-Process $ps -PassThru -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File','Z:\tru-port\tools\vm_logtail.ps1','-Out',"Z:\tru-port\work\live\engine_$Tag.log",'-Seconds',$RecordSeconds)
$b = Start-Process $ps -PassThru -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File','Z:\tru-port\tools\vm_tap_reader.ps1','-RunId',$Tag,'-Seconds',$RecordSeconds,'-MaxPerSite',$MaxPerSite,'-Sites',$Sites)
if ($Watch418) {
    $wp = Start-Process $ps -PassThru -WindowStyle Hidden -RedirectStandardOutput "Z:\tru-port\work\live\watch418_$Tag.out.txt" -RedirectStandardError "Z:\tru-port\work\live\watch418_$Tag.err.txt" -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File','Z:\tru-port\tools\vm_watch418.ps1','-Tap',"Z:\tru-port\work\taps\$Tag\tap.tsv",'-Out',"Z:\tru-port\work\live\watch418_$Tag.tsv",'-Seconds',$RecordSeconds,'-MaxDumps',2,'-DumpPrefix',"C:\CrashDumps\$($Tag)_w418")
    "watch418 PID $($wp.Id)" | Write-Host
}
"registrazione avviata $(Get-Date -Format s): logtail PID $($a.Id), tap PID $($b.Id)" | Write-Host
Wait-Process -Id $a.Id, $b.Id -ErrorAction SilentlyContinue
