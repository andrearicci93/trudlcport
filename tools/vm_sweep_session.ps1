# Un SOLO job per tutto lo sweep F8: watchdog + logtail + "clipboard feeder" + canale comandi (lascia libero il secondo slot vmpal_exec).
# Fa:
#  1. avvia tru.exe via Steam (come vm_autotest.ps1) oppure, con -NoLaunch, si aggancia al tru gia' in esecuzione;
#  2. ogni -Interval s scansiona la memoria di tru.exe (stesso metodo di vm_logtail.ps1) e scrive il log in
#     Z:\tru-port\work\live\sweep_s<S>.log (un file per sessione; reset a ogni nuovo PID/riavvio: niente piu' blocco sul log lungo precedente);
#  3. rileva la morte di tru: evento WER (eccezione/offset/modulo) + dump in C:\TRU_dumps -> work\autotest\sweep_s<S>\result.txt (UTF-8) e crash.dmp;
#  4. osserva Z:\tru-port\work\sweep\next_name.txt: quando cambia (contenuto o mtime) mette il nome negli appunti e scrive next_name.ack;
#  5. osserva Z:\tru-port\work\sweep\cmd.txt (prima riga): restart | stop | enter | space | f8 | esc | focus  -> scrive cmd.ack;
#  6. riscrive ogni ~2 s Z:\tru-port\work\sweep\status.txt (heartbeat leggibile dal Mac).
# DEVE girare con PowerShell a 32 bit (SysWOW64), altrimenti non legge la memoria del tru.exe a 32 bit:
#   vmpal_exec command=C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe
#     args=[-NoProfile,-ExecutionPolicy,Bypass,-File,Z:\tru-port\tools\vm_sweep_session.ps1,-Session,1,-Seconds,14400] timeoutSeconds=14420
# Parametri: -Session N (numero sessione iniziale), -Interval s (scan log, default 2), -Seconds (durata massima del job),
#            -NoLaunch (non avviare il gioco, agganciarsi), -NoAutoEnter (niente Enter automatici a 20 s e 30 s dall'avvio).
param(
    [int]$Session = 1,
    [int]$Interval = 2,
    [int]$Seconds = 14400,
    [switch]$NoLaunch,
    [switch]$NoAutoEnter
)
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName System.Windows.Forms, System.Drawing

$Root     = 'Z:\tru-port'
$SweepDir = "$Root\work\sweep"
$LiveDir  = "$Root\work\live"
$NameFile = "$SweepDir\next_name.txt"
$NameAck  = "$SweepDir\next_name.ack"
$CmdFile  = "$SweepDir\cmd.txt"
$CmdAck   = "$SweepDir\cmd.ack"
$Status   = "$SweepDir\status.txt"
$DumpDir  = 'C:\TRU_dumps'
$Utf8     = New-Object System.Text.UTF8Encoding($false)

foreach ($d in @($SweepDir, $LiveDir)) { New-Item -ItemType Directory -Force $d | Out-Null }

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
        if (m.State == 0x1000 && (m.Protect == 0x04 || m.Protect == 0x40) && m.Type == 0x20000) {
          for (long off = 0; off < size; off += buf.Length - 64) {
            int want = (int)Math.Min(buf.Length, size - off), got;
            if (!ReadProcessMemory(h, (IntPtr)(addr + off), buf, want, out got) || got < Pat.Length) continue;
            for (int i = 0; i <= got - Pat.Length; i++) {
              if (buf[i] != Pat[0]) continue; int k = 1; while (k < Pat.Length && buf[i + k] == Pat[k]) k++;
              if (k != Pat.Length) continue;
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
public class W {
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, UIntPtr e);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  [DllImport("user32.dll")] public static extern uint MapVirtualKey(uint code, uint type);
}
"@
[W]::SetProcessDPIAware() | Out-Null
$sh = New-Object -ComObject WScript.Shell

# ---------------------------------------------------------------- helper
function Now { (Get-Date).ToString('yyyy-MM-dd HH:mm:ss') }

function SafeWrite($path, $text) {
    try { [IO.File]::WriteAllText($path, $text, $Utf8); return $true } catch { return $false }
}

function SafeRead($path) {
    for ($i = 0; $i -lt 3; $i++) {
        try { return [IO.File]::ReadAllText($path) } catch { Start-Sleep -Milliseconds 100 }
    }
    return $null
}

function Get-Tru { Get-Process tru -ErrorAction SilentlyContinue | Select-Object -First 1 }

function Focus-Game([bool]$click) {
    $p = Get-Tru
    if (-not $p) { return $null }
    try { [W]::ShowWindow($p.MainWindowHandle, 9) | Out-Null; [W]::SetForegroundWindow($p.MainWindowHandle) | Out-Null } catch {}
    try { $sh.AppActivate($p.Id) | Out-Null } catch {}
    if ($click) {
        $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        [W]::SetCursorPos([int]($b.Width * 0.06), [int]($b.Height * 0.45)) | Out-Null
        [W]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero); [W]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
    }
    Start-Sleep -Milliseconds 300
    return $p
}

# tasto tenuto 200 ms (il gioco legge l'input a polling: SendKeys e' troppo breve)
function Press-Key([int]$vk) {
    $scan = [byte]([W]::MapVirtualKey([uint32]$vk, 0))
    [W]::keybd_event([byte]$vk, $scan, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 200
    [W]::keybd_event([byte]$vk, $scan, 2, [UIntPtr]::Zero)
}

function Set-Clip([string]$name) {
    # ritorna 'ok' | 'ok-fallback' | 'fail:<motivo>'
    if ($name -notmatch '^[A-Za-z0-9_.\-]{1,100}$') { return 'fail:nome non valido' }
    try {
        Set-Clipboard -Value $name -ErrorAction Stop
        $back = (Get-Clipboard -Raw -ErrorAction Stop)
        if ($back -and $back.Trim() -eq $name) { return 'ok' }
    } catch { }
    try {
        & cmd.exe /c "<nul set /p=$name| clip" | Out-Null
        $back = (Get-Clipboard -Raw -ErrorAction Stop)
        if ($back -and $back.Trim() -eq $name) { return 'ok-fallback' }
        return 'fail:readback diverso'
    } catch { return "fail:$($_.Exception.Message)" }
}

function Launch-Game {
    Get-Process tru -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep 2
    $steam = 'C:\Program Files (x86)\Steam\steam.exe'
    $p = $null
    for ($i = 0; $i -lt 4 -and -not $p; $i++) {
        Start-Process $steam -ArgumentList '-applaunch', '8140'
        for ($j = 0; $j -lt 12 -and -not $p; $j++) { Start-Sleep 2; $p = Get-Tru }
    }
    return $p
}

function Get-CrashInfo($since) {
    # attende fino a ~12 s l'evento WER e il dump; ritorna oggetto con testo
    $evt = $null; $dump = $null
    for ($i = 0; $i -lt 12; $i++) {
        $ev = Get-WinEvent -FilterHashtable @{LogName = 'Application'; StartTime = $since.AddSeconds(-5)} -ErrorAction SilentlyContinue |
              Where-Object { $_.ProviderName -match 'Application Error' -and $_.Message -match 'tru\.exe' } | Select-Object -First 1
        if ($ev) { $evt = $ev }
        $d = Get-ChildItem $DumpDir -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -ge $since.AddSeconds(-5) } | Sort-Object LastWriteTime | Select-Object -Last 1
        if ($d) { $dump = $d }
        if ($evt) { break }
        Start-Sleep 1
    }
    $r = @{ Event = 'no Application Error event'; Module = '-'; Dump = $null }
    if ($evt) {
        $m = $evt.Message
        $code = '?'; $off = '?'; $mod = '?'
        if ($m -match '(?:Codice eccezione|Exception code):\s*(0x[0-9a-fA-F]+)') { $code = $Matches[1] }
        if ($m -match '(?:Offset errore|Fault offset):\s*(0x[0-9a-fA-F]+)') { $off = $Matches[1] }
        if ($m -match '(?:Nome modulo[^:]*|Faulting module name):\s*([^,\s]+)') { $mod = $Matches[1] }
        $r.Event = "exception $code offset $off"; $r.Module = $mod
    }
    if ($dump) { Start-Sleep 2; $r.Dump = $dump.FullName }
    return $r
}

# ---------------------------------------------------------------- stato
$S = $Session
$state = 'INIT'          # INIT | RUNNING | DEAD | STOPPED
$curPid = 0
$pStart = $null
$last = 0
$logPath = ''
$autoDir = ''
$startedAt = $null
$enterSent = 0
$crashes = 0
$lastCmd = '-'
$lastName = '-'
$lastClip = '-'
$lastNote = ''
$lastScan = [datetime]::MinValue
$lastBeat = [datetime]::MinValue

function Begin-Session($proc) {
    # azzera tutto cio' che dipende dalla sessione
    $script:curPid = $proc.Id
    try { $script:pStart = $proc.StartTime } catch { $script:pStart = Get-Date }
    $script:last = 0
    $script:logPath = "$LiveDir\sweep_s$($script:S).log"
    $script:autoDir = "$Root\work\autotest\sweep_s$($script:S)"
    New-Item -ItemType Directory -Force $script:autoDir | Out-Null
    Remove-Item "$($script:autoDir)\*" -Force -ErrorAction SilentlyContinue
    Remove-Item $script:logPath -Force -ErrorAction SilentlyContinue
    $script:startedAt = Get-Date
    $script:enterSent = 0
    $script:state = 'RUNNING'
    $script:lastNote = "session $($script:S) started pid $($proc.Id)"
}

function Handle-Death {
    $info = Get-CrashInfo $pStart
    $res = if ($info.Event -eq 'no Application Error event') { 'EXITED (nessun evento WER: uscita senza crash o kill)' } else { 'CRASHED' }
    $el = [int]((Get-Date) - $startedAt).TotalSeconds
    $text = "RESULT: $res`r`nEVENT: $($info.Event)`r`nMODULE: $($info.Module)`r`nSESSION: $S`r`nUPTIME_S: $el`r`nLOGBYTES: $last`r`nWHEN: $(Now)`r`n"
    if ($info.Dump) { try { Copy-Item $info.Dump "$autoDir\crash.dmp" -Force; $text += "DUMP: crash.dmp`r`n" } catch { $text += "DUMP: copy failed`r`n" } }
    SafeWrite "$autoDir\result.txt" $text | Out-Null
    if ($info.Event -ne 'no Application Error event') { $script:crashes++ }
    $script:state = 'DEAD'
    $script:lastNote = "tru morto: $res / $($info.Event)"
}

function Do-Restart {
    $script:S++
    $p = Launch-Game
    if (-not $p) {
        $script:state = 'DEAD'; $script:lastNote = "restart: tru non avviato (session $($script:S))"
        $script:autoDir = "$Root\work\autotest\sweep_s$($script:S)"; New-Item -ItemType Directory -Force $script:autoDir | Out-Null
        SafeWrite "$($script:autoDir)\result.txt" "RESULT: tru did not start`r`nSESSION: $($script:S)`r`n" | Out-Null
        return
    }
    Begin-Session $p
}

# ---------------------------------------------------------------- avvio
if (-not (Test-Path "$Root\tools")) { SafeWrite $Status "ERROR: $Root non raggiungibile ($(Now))`r`n" | Out-Null; exit 1 }
if ([IntPtr]::Size -ne 4) { SafeWrite $Status "ERROR: PowerShell a 64 bit; usare C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe ($(Now))`r`n" | Out-Null; exit 1 }

# ignora i file comando gia' presenti (vecchi): considerarli gia' "visti"
$seenName = ''; $seenCmd = ''
if (Test-Path $NameFile) { $fi = Get-Item $NameFile; $seenName = "$($fi.LastWriteTimeUtc.Ticks)|$($fi.Length)" }
if (Test-Path $CmdFile)  { $fi = Get-Item $CmdFile;  $seenCmd  = "$($fi.LastWriteTimeUtc.Ticks)|$($fi.Length)" }

if ($NoLaunch) {
    $p = Get-Tru
    if ($p) { Begin-Session $p } else { $state = 'DEAD'; $lastNote = 'NoLaunch: tru non in esecuzione' }
} else {
    $p = Launch-Game
    if ($p) { Begin-Session $p } else {
        $autoDir = "$Root\work\autotest\sweep_s$S"; New-Item -ItemType Directory -Force $autoDir | Out-Null
        SafeWrite "$autoDir\result.txt" "RESULT: tru did not start`r`nSESSION: $S`r`n" | Out-Null
        $state = 'DEAD'; $lastNote = 'tru non avviato'
    }
}

# ---------------------------------------------------------------- ciclo principale (tick 0,5 s)
$t0 = Get-Date
while (((Get-Date) - $t0).TotalSeconds -lt $Seconds -and $state -ne 'STOPPED') {

    # --- 1) nome da mettere negli appunti
    if (Test-Path $NameFile) {
        $fi = Get-Item $NameFile
        $sig = "$($fi.LastWriteTimeUtc.Ticks)|$($fi.Length)"
        if ($sig -ne $seenName) {
            Start-Sleep -Milliseconds 150          # lascia finire la scrittura
            $txt = SafeRead $NameFile
            if ($txt -ne $null) {
                $fi = Get-Item $NameFile; $seenName = "$($fi.LastWriteTimeUtc.Ticks)|$($fi.Length)"
                $nm = ($txt -split "`r?`n")[0].Trim([char]0xFEFF).Trim()
                $r = Set-Clip $nm
                $lastName = $nm; $lastClip = $r
                SafeWrite $NameAck "$nm|$r|$(Now)`r`n" | Out-Null
            }
        }
    }

    # --- 2) comandi
    if (Test-Path $CmdFile) {
        $fi = Get-Item $CmdFile
        $sig = "$($fi.LastWriteTimeUtc.Ticks)|$($fi.Length)"
        if ($sig -ne $seenCmd) {
            Start-Sleep -Milliseconds 150
            $txt = SafeRead $CmdFile
            if ($txt -ne $null) {
                $fi = Get-Item $CmdFile; $seenCmd = "$($fi.LastWriteTimeUtc.Ticks)|$($fi.Length)"
                $cmd = (($txt -split "`r?`n")[0].Trim([char]0xFEFF).Trim()).ToLower()
                $lastCmd = $cmd; $res = 'done'
                switch ($cmd) {
                    'restart' { Do-Restart }
                    'stop'    { $state = 'STOPPED' }
                    'enter'   { if (Focus-Game $false) { Press-Key 0x0D } else { $res = 'no tru' } }
                    'space'   { if (Focus-Game $false) { Press-Key 0x20 } else { $res = 'no tru' } }
                    'f8'      { if (Focus-Game $false) { Press-Key 0x77 } else { $res = 'no tru' } }
                    'esc'     { if (Focus-Game $false) { Press-Key 0x1B } else { $res = 'no tru' } }
                    'focus'   { if (-not (Focus-Game $false)) { $res = 'no tru' } }
                    default   { $res = 'comando sconosciuto' }
                }
                SafeWrite $CmdAck "$cmd|$res|$(Now)`r`n" | Out-Null
            }
        }
    }

    # --- 3) sessione: vita, auto-enter, scan log
    if ($state -eq 'RUNNING') {
        $p = Get-Tru
        if (-not $p) {
            Handle-Death
        } else {
            if ($p.Id -ne $curPid) {
                # tru riavviato da fuori (non da noi): nuova sessione, log nuovo, nessun residuo del precedente
                $S++; Begin-Session $p
            }
            $el = ((Get-Date) - $startedAt).TotalSeconds
            if (-not $NoAutoEnter -and $enterSent -lt 2 -and $el -lt 60) {
                if ($enterSent -eq 0 -and $el -ge 20) { $null = Focus-Game $true; Press-Key 0x0D; $enterSent = 1; $lastNote = "auto-enter 1 a t=$([int]$el)" }
                elseif ($enterSent -eq 1 -and $el -ge 30) { $null = Focus-Game $true; Press-Key 0x0D; $enterSent = 2; $lastNote = "auto-enter 2 a t=$([int]$el)" }
            }
            if (((Get-Date) - $lastScan).TotalSeconds -ge $Interval) {
                $logTxt = [LT]::Scan($p.Id)       # NB: PowerShell non distingue maiuscole: mai usare $s ($S = sessione)
                $lastScan = Get-Date
                if ($logTxt -and $logTxt.Length -gt 0 -and $logTxt.Length -ge $last) {
                    if ($logTxt.Length -gt $last) { [IO.File]::WriteAllText($logPath, $logTxt, $Utf8) }
                    $last = $logTxt.Length
                }
            }
        }
    }

    # --- 4) heartbeat
    if (((Get-Date) - $lastBeat).TotalSeconds -ge 2) {
        $p = Get-Tru
        $alive = [bool]$p; $resp = '-'
        if ($p) { try { $resp = $p.Responding } catch { } }
        $up = if ($startedAt) { [int]((Get-Date) - $startedAt).TotalSeconds } else { 0 }
        $txt = "time=$(Now)`r`nstate=$state`r`nsession=$S`r`npid=$curPid`r`nalive=$alive`r`nresponding=$resp`r`nuptime_s=$up`r`nlog=$logPath`r`nlog_bytes=$last`r`ncrashes=$crashes`r`nlast_name=$lastName`r`nlast_clip=$lastClip`r`nlast_cmd=$lastCmd`r`nnote=$lastNote`r`n"
        SafeWrite $Status $txt | Out-Null
        $lastBeat = Get-Date
    }

    Start-Sleep -Milliseconds 500
}

$state = if ($state -eq 'STOPPED') { 'STOPPED' } else { 'TIMEOUT' }
SafeWrite $Status "time=$(Now)`r`nstate=$state`r`nsession=$S`r`nnote=job terminato`r`n" | Out-Null
