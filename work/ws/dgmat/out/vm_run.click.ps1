# vm_run.ps1 - RUNNER AUTONOMO (gira DENTRO la VM): pilota + watchdog + classificatore in UN processo.
# Un solo scenario per run; ogni run parte con un processo tru NUOVO. Scrive tutto in Z:\tru-port\work\runs\<RunId>\
# (result.json, status.txt, runner.log, engine.log, a1\..., shots\, save_before\). PASS/FAIL SOLO da marker del log / sonde memoria,
# MAI dagli screenshot. Vedi work/ws/runner/README.md (uso, formati, limiti) e HOOK_STARTUP.md.
#
# Lancio staccato (una riga; il Mac poi legge runs\<RunId>\status.txt / result.json):
#   Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File Z:\tru-port\tools\vm_run.ps1 -Scenario dungeon_direct -RunId r001 -Verify fast'}
#
# IMPORTANTE: i tasti/mouse funzionano SOLO se il runner gira nella sessione interattiva dell'utente (stessa di explorer.exe).
# Il preflight lo controlla e, se non lo e', scrive INFRA senza toccare il gioco (alternativa: vedi README, task pianificato /IT).
#
# Parametri: -Scenario nome|percorso.json  -RunId id  [-Verify fast|full]  [-Baseline B0_raw]  [-Param 'alive_seconds=45;x=1']
#   [-KeepDump] copia i dump in runs\<RunId>\dumps\   [-KeepGame] non chiude tru alla fine   [-StrictBaseline] baseline diversa => INFRA
#   [-PreflightOnly] solo controlli (sessione, baseline, save) senza avviare il gioco   [-NoSaveRestore]   [-NoRetry] niente ritentativo FMOD
#   [-MaxSeconds N] tetto totale (default dallo scenario, 600)
# Compatibile PowerShell 5.1; nessun modulo esterno; nessuna rete; scrive solo in runs\ e (ripristino) nella cartella dei save.
param(
    [Parameter(Mandatory = $true)][string]$Scenario,
    [Parameter(Mandatory = $true)][string]$RunId,
    [ValidateSet('fast', 'full')][string]$Verify = 'fast',
    [string]$Baseline = '',
    [string]$Param = '',
    [switch]$KeepDump,
    [switch]$KeepGame,
    [switch]$StrictBaseline,
    [switch]$PreflightOnly,
    [switch]$NoSaveRestore,
    [switch]$NoRetry,
    [int]$MaxSeconds = 0,
    [string]$Root = 'Z:\tru-port',
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld'
)
$ErrorActionPreference = 'Continue'
$RunnerVersion = '1.0'
Add-Type -AssemblyName System.Windows.Forms, System.Drawing

# ------------------------------------------------------------------ tipi nativi (C# 5)
if (-not ('RunnerNative' -as [type])) {
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;
public static class RunnerNative {
    [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint f, int dx, int dy, uint d, UIntPtr e);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint msg, IntPtr w, IntPtr l);
    [DllImport("user32.dll")] public static extern uint MapVirtualKeyEx(uint code, uint type, IntPtr hkl);
    [DllImport("user32.dll")] public static extern IntPtr GetKeyboardLayout(uint thread);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] static extern bool GetClientRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] static extern bool ClientToScreen(IntPtr h, ref POINT p);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr h, StringBuilder sb, int max);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder sb, int max);
    delegate bool EnumProc(IntPtr h, IntPtr l);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc cb, IntPtr l);
    [StructLayout(LayoutKind.Sequential)] struct RECT { public int L, T, R, B; }
    [StructLayout(LayoutKind.Sequential)] struct POINT { public int X, Y; }

    // [left, top, width, height] dell'area client in coordinate schermo
    public static int[] ClientScreenRect(IntPtr h) {
        RECT r; POINT p = new POINT();
        if (!GetClientRect(h, out r)) { return null; }
        ClientToScreen(h, ref p);
        return new int[] { p.X, p.Y, r.R - r.L, r.B - r.T };
    }
    // VK che il layout della finestra assegna a uno scancode (es. 0x35 = '-' su tastiera italiana)
    public static int LayoutVk(IntPtr hwnd, uint scan) {
        uint pid; uint tid = GetWindowThreadProcessId(hwnd, out pid);
        IntPtr hkl = GetKeyboardLayout(tid);
        return (int)MapVirtualKeyEx(scan, 1, hkl);
    }
    // finestre visibili del processo con classe #32770 (dialog: tipicamente la finestra d'errore del motore): "classe|titolo"
    public static string[] DialogsOf(uint pidWanted) {
        List<string> res = new List<string>();
        EnumProc cb = delegate(IntPtr h, IntPtr l) {
            uint pid; GetWindowThreadProcessId(h, out pid);
            if (pid == pidWanted && IsWindowVisible(h)) {
                StringBuilder c = new StringBuilder(128); GetClassName(h, c, 128);
                if (c.ToString() == "#32770") {
                    StringBuilder t = new StringBuilder(256); GetWindowText(h, t, 256);
                    res.Add(c.ToString() + "|" + t.ToString());
                }
            }
            return true;
        };
        EnumWindows(cb, IntPtr.Zero);
        return res.ToArray();
    }
}
"@
}
[void][RunnerNative]::SetProcessDPIAware()

# sonde memoria (riuso: tipi ProbeNative + New-RaftProbe...). Dot-source SENZA parametri.
$ProbeLibPath = Join-Path $PSScriptRoot 'vm_probe_lib.ps1'
. $ProbeLibPath

# ------------------------------------------------------------------ stato globale
$script:Utf8 = New-Object System.Text.UTF8Encoding($false)
$script:T0 = Get-Date
$script:Sh = New-Object -ComObject WScript.Shell
$script:RunDir = ''; $script:AttemptDir = ''; $script:ResultPath = ''; $script:StatusPath = ''; $script:RunnerLog = ''
$script:Res = $null
$script:Steps = New-Object System.Collections.ArrayList
$script:Shots = New-Object System.Collections.ArrayList
$script:Warnings = New-Object System.Collections.ArrayList
$script:Tru = $null; $script:Hwnd = [IntPtr]::Zero; $script:ProcH = [IntPtr]::Zero
$script:LogFile = ''; $script:Log = ''; $script:LogLen = -1; $script:LogMtime = [datetime]::MinValue
$script:Markers = @()
$script:LastMatchTime = $null; $script:LastMatchT = $null
$script:LaunchTime = Get-Date
$script:LogtailProc = $null
$script:Probe = $null
$script:MenuOpen = $false
$script:CurStep = ''
$script:TMax = 600
$script:Attempt = 0
$script:Deadline = (Get-Date).AddSeconds(600)
$script:LastBeat = [datetime]::MinValue; $script:LastWerCheck = [datetime]::MinValue; $script:LastDlg = [datetime]::MinValue
$script:Dialogs = @()
$script:ScnParams = @{}
$script:Scn = $null
$script:MenuFlagAddr = 0xA02B79      # Input::DisableInput (TR8) = 1 con il menu F8 aperto (sorgente hook src/input/Input.cpp)
$script:CrashTable = @(
    @{ offset = 0x3b92fb; cls = 'FMOD';    outcome = 'INFRA' },
    @{ offset = 0x7b92fb; cls = 'FMOD';    outcome = 'INFRA' },
    @{ offset = 0x1c019f; cls = 'DUNGEON'; outcome = 'FAIL' },
    @{ offset = 0x5c019f; cls = 'DUNGEON'; outcome = 'FAIL' }
)

function Now-Iso { (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss.fff') }
function Elapsed { [math]::Round(((Get-Date) - $script:T0).TotalSeconds, 1) }
function Write-Text([string]$path, [string]$text) { [IO.File]::WriteAllText($path, $text, $script:Utf8) }
function Note([string]$msg) {
    if (-not $script:RunnerLog) { return }
    try { [IO.File]::AppendAllText($script:RunnerLog, ("[{0}] {1}`r`n" -f (Elapsed), $msg), $script:Utf8) } catch { }
}
function Add-Warn([string]$msg) { $null = $script:Warnings.Add($msg); Note ("WARN " + $msg) }
function Md5Of([string]$path) {
    try { return (Get-FileHash -LiteralPath $path -Algorithm MD5 -ErrorAction Stop).Hash.ToLower() } catch { return $null }
}
function Get-Opt($obj, [string]$name, $default) {
    if ($null -ne $obj) {
        if ($obj -is [System.Collections.IDictionary]) {
            if ($obj.Contains($name) -and $null -ne $obj[$name]) { return $obj[$name] }
        } else {
            $pr = $obj.PSObject.Properties[$name]
            if ($pr -and $null -ne $pr.Value) { return $pr.Value }
        }
    }
    return $default
}

# ------------------------------------------------------------------ risultato / heartbeat
function Get-MarkerReport {
    $found = @(); $missing = @(); $benign = @()
    foreach ($m in $script:Markers) {
        if ($m.found) {
            $row = [ordered]@{ name = $m.name; t_s = $m.t; count = $m.count; line = $m.line }
            if ($m.benign) { $benign += , $row } else { $found += , $row }
        } elseif (-not $m.benign) { $missing += $m.name }
    }
    return [ordered]@{ found = @($found); missing = @($missing); benign_found = @($benign) }
}

function Save-Result {
    if (-not $script:Res) { return }
    $script:Res['updated'] = Now-Iso
    $script:Res['duration_s'] = Elapsed
    $script:Res['steps'] = @($script:Steps)
    $script:Res['shots'] = @($script:Shots)
    $script:Res['warnings'] = @($script:Warnings)
    $script:Res['markers'] = Get-MarkerReport
    try {
        $json = ConvertTo-Json -InputObject $script:Res -Depth 10
        $tmp = $script:ResultPath + '.tmp'
        Write-Text $tmp $json
        Move-Item -LiteralPath $tmp -Destination $script:ResultPath -Force -ErrorAction Stop
    } catch {
        try { Write-Text $script:ResultPath (ConvertTo-Json -InputObject $script:Res -Depth 10) } catch { }
    }
}

function Write-Status([string]$state) {
    $up = ''
    if ($script:Tru) { try { $up = [int]((Get-Date) - $script:LaunchTime).TotalSeconds } catch { } }
    $alive = $false
    if ($script:Tru) { try { $script:Tru.Refresh(); $alive = -not $script:Tru.HasExited } catch { } }
    $txt = "time=$(Now-Iso)`r`nstate=$state`r`nrun=$RunId`r`nscenario=$($script:ScnName)`r`nattempt=$($script:Attempt)`r`nstep=$($script:CurStep)`r`nelapsed_s=$(Elapsed)`r`ntru_alive=$alive`r`ntru_uptime_s=$up`r`nlog_chars=$($script:LogLen)`r`nmenu_open=$($script:MenuOpen)`r`nerror_dialog=$(@($script:Dialogs).Count)`r`n"
    try { Write-Text $script:StatusPath $txt } catch { }
}

# ------------------------------------------------------------------ log: lettura, marker
function Update-Markers {
    foreach ($m in $script:Markers) {
        if ($m.found) { continue }
        $mm = $m.rx.Match($script:Log)
        if ($mm.Success) {
            $m.found = $true; $m.t = Elapsed
            $ls = $script:Log.LastIndexOf("`n", [Math]::Max(0, $mm.Index - 1))
            if ($ls -lt 0) { $ls = 0 } else { $ls++ }
            $le = $script:Log.IndexOf("`n", $mm.Index)
            if ($le -lt 0) { $le = $script:Log.Length }
            $line = $script:Log.Substring($ls, [Math]::Min($le - $ls, 300)).TrimEnd("`r")
            $m.line = $line
        }
    }
}

function Read-LogFile {
    $f = $script:LogFile
    if (-not $f) { return }
    try {
        $fi = New-Object System.IO.FileInfo($f)
        if (-not $fi.Exists) { return }
        if ($fi.Length -eq 0) { return }
        if ($fi.LastWriteTimeUtc -eq $script:LogMtime -and $fi.Length -eq $script:LogBytes) { return }
        $fs = New-Object System.IO.FileStream($f, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
        $sr = New-Object System.IO.StreamReader($fs, [Text.Encoding]::UTF8)
        $t = $sr.ReadToEnd(); $sr.Close(); $fs.Close()
        $script:LogMtime = $fi.LastWriteTimeUtc; $script:LogBytes = $fi.Length
        if ($t.Length -ge $script:Log.Length) {          # il log e' solo-append: ignora letture parziali/accorciate
            $changed = ($t.Length -ne $script:Log.Length)
            $script:Log = $t; $script:LogLen = $t.Length
            if ($changed) { Update-Markers }
        }
    } catch { }
}

function Final-MarkerCounts {
    foreach ($m in $script:Markers) {
        try { $m.count = $m.rx.Matches($script:Log).Count } catch { $m.count = 0 }
    }
}

function Init-Markers {
    $defs = @(
        @{ name = 'current_level';   regex = '\*\*\* CURRENT LEVEL = (\S+)'; benign = $false },
        @{ name = 'warping_lara';    regex = 'warping lara to (.+)'; benign = $false },
        @{ name = 'in_water';        regex = 'in water!'; benign = $false },
        @{ name = 'save_successful'; regex = 'Save Successful'; benign = $false },
        @{ name = 'streamgroup';     regex = 'Loading PC-W\\StreamGroups\\(\S+)'; benign = $false },
        @{ name = 'success_adrenaline'; regex = 'SUCCESS adrenaline'; benign = $false },
        @{ name = 'not_switching';   regex = 'Not switching to unit (\S*)'; benign = $false },
        @{ name = 'level_not_found'; regex = 'Level not found'; benign = $true },
        @{ name = 'invalid_combat_reticle'; regex = 'Invalid combat reticle'; benign = $true }
    )
    $extra = @(Get-Opt $script:Scn 'markers' @())
    foreach ($e in $extra) { $defs += @{ name = [string]$e.name; regex = [string]$e.regex; benign = [bool](Get-Opt $e 'benign' $false) } }
    $list = @()
    foreach ($d in $defs) {
        $o = New-Object PSObject -Property @{
            name = $d.name; regex = $d.regex; benign = $d.benign; found = $false; t = $null; count = 0; line = ''
            rx = (New-Object System.Text.RegularExpressions.Regex($d.regex, 'Multiline'))
        }
        $list += $o
    }
    $script:Markers = $list
}

# ------------------------------------------------------------------ Pump: attesa con watchdog
function Check-Alive {
    if (-not $script:Tru) { return }
    $dead = $false
    try { $script:Tru.Refresh(); $dead = $script:Tru.HasExited } catch { $dead = $true }
    if (-not $dead -and ((Get-Date) - $script:LastWerCheck).TotalSeconds -ge 1.5) {
        $script:LastWerCheck = Get-Date
        # WerFault attivo = crash in corso (il processo puo' restare vivo qualche secondo mentre scrive il dump)
        $wf = @(Get-Process WerFault -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -ge $script:LaunchTime })
        if ($wf.Count -gt 0) { Note 'WerFault attivo: crash in corso'; $dead = $true }
    }
    if ($dead) { throw 'TRU_DEAD' }
}

function Pump([int]$ms) {
    $end = (Get-Date).AddMilliseconds($ms)
    do {
        Check-Alive
        if ((Get-Date) -gt $script:Deadline) { throw 'TOTAL_TIMEOUT' }
        Read-LogFile
        if ($script:Probe) { Step-RaftProbe $script:Probe }
        if (((Get-Date) - $script:LastDlg).TotalSeconds -ge 2 -and $script:Tru) {
            $script:LastDlg = Get-Date
            try { $script:Dialogs = @([RunnerNative]::DialogsOf([uint32]$script:Tru.Id)) } catch { }
        }
        if (((Get-Date) - $script:LastBeat).TotalSeconds -ge 3) {
            $script:LastBeat = Get-Date
            Write-Status 'RUNNING'
            Save-Result
        }
        $left = ($end - (Get-Date)).TotalMilliseconds
        if ($left -gt 0) {
            $nap = 100; if ($script:Probe) { $nap = 25 }
            Start-Sleep -Milliseconds ([int][Math]::Min($nap, $left))
        }
    } while ((Get-Date) -lt $end)
}

function Wait-LogMatch([string]$regex, [double]$timeout, [int]$fromPos) {
    $rx = New-Object System.Text.RegularExpressions.Regex($regex, 'Multiline')
    $deadline = (Get-Date).AddSeconds($timeout)
    while ($true) {
        Read-LogFile
        $mm = $rx.Match($script:Log, [Math]::Min($fromPos, $script:Log.Length))
        if ($mm.Success) { $script:LastMatchTime = Get-Date; $script:LastMatchT = Elapsed; return $mm }
        if ((Get-Date) -gt $deadline) { return $null }
        Pump 250
    }
}

# ------------------------------------------------------------------ input
function Get-KeySpec([string]$name) {
    $n = $name.Trim().ToLower()
    $sp = @{
        'enter' = @(0x0D, 0x1C, 0); 'return' = @(0x0D, 0x1C, 0); 'space' = @(0x20, 0x39, 0); 'esc' = @(0x1B, 0x01, 0); 'escape' = @(0x1B, 0x01, 0)
        'tab' = @(0x09, 0x0F, 0); 'backspace' = @(0x08, 0x0E, 0); 'delete' = @(0x2E, 0x53, 1); 'del' = @(0x2E, 0x53, 1)
        'up' = @(0x26, 0x48, 1); 'down' = @(0x28, 0x50, 1); 'left' = @(0x25, 0x4B, 1); 'right' = @(0x27, 0x4D, 1)
        'shift' = @(0x10, 0x2A, 0); 'ctrl' = @(0x11, 0x1D, 0); 'alt' = @(0x12, 0x38, 0)
        'f1' = @(0x70, 0x3B, 0); 'f2' = @(0x71, 0x3C, 0); 'f3' = @(0x72, 0x3D, 0); 'f4' = @(0x73, 0x3E, 0); 'f5' = @(0x74, 0x3F, 0)
        'f6' = @(0x75, 0x40, 0); 'f7' = @(0x76, 0x41, 0); 'f8' = @(0x77, 0x42, 0); 'f9' = @(0x78, 0x43, 0); 'f10' = @(0x79, 0x44, 0)
        'f11' = @(0x7A, 0x57, 0); 'f12' = @(0x7B, 0x58, 0)
    }
    if ($sp.ContainsKey($n)) { return @{ vk = $sp[$n][0]; scan = $sp[$n][1]; ext = $sp[$n][2] } }
    $rowScan = @{ 'q' = 0x10; 'w' = 0x11; 'e' = 0x12; 'r' = 0x13; 't' = 0x14; 'y' = 0x15; 'u' = 0x16; 'i' = 0x17; 'o' = 0x18; 'p' = 0x19
        'a' = 0x1E; 's' = 0x1F; 'd' = 0x20; 'f' = 0x21; 'g' = 0x22; 'h' = 0x23; 'j' = 0x24; 'k' = 0x25; 'l' = 0x26
        'z' = 0x2C; 'x' = 0x2D; 'c' = 0x2E; 'v' = 0x2F; 'b' = 0x30; 'n' = 0x31; 'm' = 0x32 }
    if ($n.Length -eq 1 -and $rowScan.ContainsKey($n)) { return @{ vk = [int][char]$n.ToUpper(); scan = $rowScan[$n]; ext = 0 } }
    if ($n -match '^[0-9]$') {
        $d = [int]$n; $sc = 0x0B; if ($d -ge 1) { $sc = 0x01 + $d }
        return @{ vk = (0x30 + $d); scan = $sc; ext = 0 }
    }
    if ($n -match '^scan:(0x[0-9a-f]+|\d+)$') {
        $sc = [Convert]::ToInt32($Matches[1].Replace('0x', ''), $(if ($Matches[1].StartsWith('0x')) { 16 } else { 10 }))
        $vk = 0
        try { $vk = [RunnerNative]::LayoutVk($script:Hwnd, [uint32]$sc) } catch { }
        return @{ vk = $vk; scan = $sc; ext = 0 }
    }
    throw "INFRA:tasto sconosciuto '$name'"
}

function Key-Down($spec) { $fl = 0; if ($spec.ext) { $fl = 1 }; [RunnerNative]::keybd_event([byte]$spec.vk, [byte]$spec.scan, [uint32]$fl, [UIntPtr]::Zero) }
function Key-Up($spec)   { $fl = 2; if ($spec.ext) { $fl = 3 }; [RunnerNative]::keybd_event([byte]$spec.vk, [byte]$spec.scan, [uint32]$fl, [UIntPtr]::Zero) }

# "ctrl+a", "f8", "enter", "scan:0x35": modificatori premuti in ordine, tasto tenuto hold_ms, rilascio in ordine inverso
function Send-Key([string]$combo, [int]$holdMs = 80) {
    $parts = @($combo.Split('+'))
    $specs = @(); foreach ($p in $parts) { $specs += , (Get-KeySpec $p) }
    for ($i = 0; $i -lt $specs.Count - 1; $i++) { Key-Down $specs[$i]; Start-Sleep -Milliseconds 30 }
    $last = $specs[$specs.Count - 1]
    Key-Down $last; Start-Sleep -Milliseconds $holdMs; Key-Up $last
    for ($i = $specs.Count - 2; $i -ge 0; $i--) { Start-Sleep -Milliseconds 20; Key-Up $specs[$i] }
}

function Focus-Game([bool]$click = $false) {
    $p = $script:Tru
    if (-not $p) { return $false }
    try { $p.Refresh() } catch { }
    $h = $p.MainWindowHandle
    if ($h -eq [IntPtr]::Zero) { return $false }
    $script:Hwnd = $h
    [void][RunnerNative]::ShowWindow($h, 9)
    [void][RunnerNative]::SetForegroundWindow($h)
    try { [void]$script:Sh.AppActivate($p.Id) } catch { }
    Start-Sleep -Milliseconds 200
    $ok = ([RunnerNative]::GetForegroundWindow().ToInt64() -eq $h.ToInt64())
    if (-not $ok -and $click) {
        # come vm_autotest: click sul bordo sinistro per togliere di mezzo Start/Widgets
        $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        [void][RunnerNative]::SetCursorPos([int]($b.Width * 0.06), [int]($b.Height * 0.45))
        [RunnerNative]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 60; [RunnerNative]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
        Start-Sleep -Milliseconds 300
        [void][RunnerNative]::SetForegroundWindow($h)
        $ok = ([RunnerNative]::GetForegroundWindow().ToInt64() -eq $h.ToInt64())
    }
    return $ok
}

function Ensure-Focus {
    if (-not (Focus-Game $false)) {
        if (-not (Focus-Game $true)) { Add-Warn "gioco non in primo piano (step $($script:CurStep))" }
    }
}

# clic in coordinate normalizzate dell'area client (0..1). mode: physical (SetCursorPos+mouse_event) | post (SetCursorPos + WM_LBUTTON* alla finestra)
function Click-Norm([double]$nx, [double]$ny, [string]$mode = 'physical') {
    $r = [RunnerNative]::ClientScreenRect($script:Hwnd)
    if (-not $r) { throw 'INFRA:GetClientRect fallito' }
    $cx = [int]($nx * $r[2]); $cy = [int]($ny * $r[3])
    $sx = $r[0] + $cx; $sy = $r[1] + $cy
    [void][RunnerNative]::SetCursorPos($sx, $sy); Start-Sleep -Milliseconds 150
    [void][RunnerNative]::SetCursorPos($sx + 1, $sy); Start-Sleep -Milliseconds 100
    [void][RunnerNative]::SetCursorPos($sx, $sy); Start-Sleep -Milliseconds 150
    if ($mode -eq 'post') {
        $lp = [IntPtr](($cy -shl 16) -bor ($cx -band 0xFFFF))
        [void][RunnerNative]::PostMessage($script:Hwnd, 0x200, [IntPtr]0, $lp); Start-Sleep -Milliseconds 80
        [void][RunnerNative]::PostMessage($script:Hwnd, 0x201, [IntPtr]1, $lp); Start-Sleep -Milliseconds 100
        [void][RunnerNative]::PostMessage($script:Hwnd, 0x202, [IntPtr]0, $lp)
    } else {
        [RunnerNative]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 100
        [RunnerNative]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
    }
    Start-Sleep -Milliseconds 250
}

# digitazione: type = scancode (layout italiano: '_' = Shift + scan 0x35, '-' = scan 0x35); char = WM_CHAR alla finestra; paste = clipboard + Ctrl+V
function Type-Text([string]$text, [string]$method) {
    if ($method -eq 'paste') {
        $ok = $false
        try { Set-Clipboard -Value $text -ErrorAction Stop; $ok = ((Get-Clipboard -Raw -ErrorAction Stop).Trim() -eq $text) } catch { }
        if (-not $ok) { throw 'INFRA:Set-Clipboard fallito' }
        Send-Key 'ctrl+v' 80
        return
    }
    foreach ($ch in $text.ToCharArray()) {
        if ($method -eq 'char') {
            [void][RunnerNative]::PostMessage($script:Hwnd, 0x102, [IntPtr][int]$ch, [IntPtr]1)
            Start-Sleep -Milliseconds 50
            continue
        }
        $c = [string]$ch
        if ($c -match '^[A-Za-z0-9]$') {
            if ($c -cmatch '^[A-Z]$') { Send-Key ('shift+' + $c.ToLower()) 40 } else { Send-Key $c 40 }
        }
        elseif ($c -eq '_') { Send-Key 'shift+scan:0x35' 40 }
        elseif ($c -eq '-') { Send-Key 'scan:0x35' 40 }
        elseif ($c -eq '.') { Send-Key 'scan:0x34' 40 }
        else { throw "INFRA:carattere non digitabile '$c'" }
        Start-Sleep -Milliseconds 40
    }
}

function Get-MenuFlag {
    if ($script:ProcH -eq [IntPtr]::Zero) { return $null }
    return (Read-ProbeByte $script:ProcH $script:MenuFlagAddr)
}

function Set-Menu([bool]$open, [bool]$verify = $true) {
    # F8 = WM_KEYUP VK_F8 nella WndProc subclassata (hook Menu.cpp:80): tasto tenuto 500 ms, poi verifica sul flag Input::DisableInput
    $flag = $null
    if ($verify) { $flag = Get-MenuFlag }
    $isOpen = $script:MenuOpen
    if ($null -ne $flag) { $isOpen = ($flag -eq 1) }
    if ($isOpen -eq $open) { $script:MenuOpen = $open; return 'gia'' nello stato richiesto' }
    Ensure-Focus
    Send-Key 'f8' 500
    Pump 700
    $flag = $null
    if ($verify) { $flag = Get-MenuFlag }
    $how = 'keybd_event'
    if ($null -ne $flag -and ($flag -eq 1) -ne $open) {
        # fallback: WM_KEYDOWN/WM_KEYUP VK_F8 (scan 0x42) direttamente alla finestra
        [void][RunnerNative]::PostMessage($script:Hwnd, 0x100, [IntPtr]0x77, [IntPtr](0x00420001))
        Start-Sleep -Milliseconds 120
        [void][RunnerNative]::PostMessage($script:Hwnd, 0x101, [IntPtr]0x77, [IntPtr](-1069547519))
        Pump 700
        $flag = Get-MenuFlag; $how = 'PostMessage'
    }
    if ($null -eq $flag) { if ($verify) { Add-Warn 'flag menu (0xA02B79) non leggibile: stato F8 non verificato' }; $script:MenuOpen = $open; return "premuto ($how), non verificato" }
    if (($flag -eq 1) -ne $open) { Add-Warn "flag menu=$flag dopo F8 ($how): indirizzo 0xA02B79 forse errato o F8 senza effetto (usare verify=false se l'indirizzo e' sbagliato)"; $script:MenuOpen = $open; return "NON confermato (flag=$flag)" }
    $script:MenuOpen = $open
    return "ok ($how, flag=$flag)"
}

function Take-Shot([string]$name) {
    try {
        $dir = Join-Path $script:AttemptDir 'shots'
        New-Item -ItemType Directory -Force $dir | Out-Null
        $fn = '{0:000}s_{1}.png' -f [int](((Get-Date) - $script:LaunchTime).TotalSeconds), ($name -replace '[^A-Za-z0-9_.-]', '_')
        $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
        $bmp.Save((Join-Path $dir $fn), [System.Drawing.Imaging.ImageFormat]::Png)
        $g.Dispose(); $bmp.Dispose()
        $null = $script:Shots.Add(("a{0}/shots/{1}" -f $script:Attempt, $fn))
    } catch { Add-Warn "screenshot fallito: $($_.Exception.Message)" }
}

# ------------------------------------------------------------------ azioni degli scenari
function Do-LoadUnit($st) {
    $unit = [string]$st.unit
    $okRx = [string](Get-Opt $st 'expect_regex' ('(?m)(\*\*\* CURRENT LEVEL = ' + [regex]::Escape($unit) + '(?![A-Za-z0-9_]))'))
    $timeout = [double](Get-Opt $st 'timeout_s' 150)
    $quiet = [double](Get-Opt $st 'quiet_s' 20)
    $uf = @(Get-Opt $st 'click_unit' @(0.17, 0.20))
    $bt = @(Get-Opt $st 'click_btn' @(0.16, 0.249))
    $tries = @(Get-Opt $st 'tries' @(
            @{ type = 'type'; mouse = 'physical' }, @{ type = 'char'; mouse = 'post' }, @{ type = 'paste'; mouse = 'physical' }))
    $detail = @()
    $i = 0
    foreach ($t in $tries) {
        $i++
        $tt = [string](Get-Opt $t 'type' 'type'); $mm = [string](Get-Opt $t 'mouse' 'physical')
        $null = Set-Menu $true ([bool](Get-Opt $st 'verify_menu' $true))
        $pos = $script:Log.Length
        Ensure-Focus
        Click-Norm ([double]$uf[0]) ([double]$uf[1]) $mm
        Send-Key 'ctrl+a' 60; Start-Sleep -Milliseconds 100
        Send-Key 'delete' 60; Start-Sleep -Milliseconds 100
        Type-Text $unit $tt
        Start-Sleep -Milliseconds 300
        if ($st.shot_before_click) { Take-Shot ("unit_typed_try{0}" -f $i) }
        Click-Norm ([double]$bt[0]) ([double]$bt[1]) $mm
        $t0 = Get-Date
        $res = 'nessuna riga nuova'
        $rxOk = New-Object System.Text.RegularExpressions.Regex($okRx, 'Multiline')
        $rxNo = New-Object System.Text.RegularExpressions.Regex('Not switching to unit (\S*)', 'Multiline')
        $outcome = 'quiet'
        while ($true) {
            Read-LogFile
            $a = $rxOk.Match($script:Log, [Math]::Min($pos, $script:Log.Length))
            if ($a.Success) { $script:LastMatchTime = Get-Date; $script:LastMatchT = Elapsed; $outcome = 'ok'; break }
            $b = $rxNo.Match($script:Log, [Math]::Min($pos, $script:Log.Length))
            if ($b.Success) { $outcome = 'not_switching'; $res = "il gioco ha letto '" + $b.Groups[1].Value + "'"; break }
            $secs = ((Get-Date) - $t0).TotalSeconds
            if ($secs -gt $timeout) { $outcome = 'timeout'; break }
            if ($script:Log.Length -lt $pos + 40 -and $secs -gt $quiet) { $outcome = 'quiet'; break }
            Pump 250
        }
        $detail += ("try{0}[{1}/{2}]={3} {4}" -f $i, $tt, $mm, $outcome, $res)
        if ($outcome -eq 'ok') { return ($detail -join '; ') }
        if ($outcome -eq 'timeout') { throw ("STEP_TIMEOUT:{0}:{1}" -f $st.id, ($detail -join '; ')) }
    }
    throw ("STEP_FAIL:{0}:Load unit non riuscito: {1}" -f $st.id, ($detail -join '; '))
}

function Do-BootResume($st) {
    $rxLevel = [string](Get-Opt $st 'expect_regex' '\*\*\* CURRENT LEVEL = ')
    $enterFirst = [double](Get-Opt $st 'enter_first_s' 20)
    $enterEvery = [double](Get-Opt $st 'enter_every_s' 8)
    $maxEnters = [int](Get-Opt $st 'max_enters' 6)
    $spaceAt = [double](Get-Opt $st 'space_at_s' 17)
    $timeout = [double](Get-Opt $st 'timeout_s' 180)
    $settle = [double](Get-Opt $st 'settle_s' 8)
    $menuKeys = @(Get-Opt $st 'menu_keys' @())
    $startedAt = $script:LaunchTime
    try { $startedAt = $script:Tru.StartTime } catch { }
    $enters = 0; $space = $false; $first = $true; $logAtEnter = -1
    $t0 = Get-Date
    $rx = New-Object System.Text.RegularExpressions.Regex($rxLevel, 'Multiline')
    while ($true) {
        Read-LogFile
        $mm = $rx.Match($script:Log)
        if ($mm.Success) { $script:LastMatchTime = Get-Date; $script:LastMatchT = Elapsed; break }
        if (((Get-Date) - $t0).TotalSeconds -gt $timeout) { throw ("STEP_TIMEOUT:{0}:nessun CURRENT LEVEL dopo {1} s ({2} Invio)" -f $st.id, $timeout, $enters) }
        $age = ((Get-Date) - $startedAt).TotalSeconds
        if (-not $space -and $age -ge $spaceAt) { Ensure-Focus; Send-Key 'space' 200; $space = $true }
        # dopo il primo Invio, se il log cresce molto il caricamento e' partito: niente altri Invio dentro il livello
        $loading = ($logAtEnter -ge 0 -and $script:Log.Length -gt $logAtEnter + 400)
        if ($enters -lt $maxEnters -and -not $loading -and $age -ge ($enterFirst + $enters * $enterEvery)) {
            if ($first) { $null = Focus-Game $true; $first = $false } else { Ensure-Focus }
            if ($enters -eq 0 -and $menuKeys.Count -gt 0) {
                foreach ($mk in $menuKeys) { Send-Key ([string]$mk.key) ([int](Get-Opt $mk 'hold_ms' 200)); Pump ([int](Get-Opt $mk 'wait_ms' 700)) }
            } else { Send-Key 'enter' 250 }
            if ($enters -eq 0) { $logAtEnter = $script:Log.Length }
            $enters++
        }
        Pump 250
    }
    Pump ([int]($settle * 1000))
    return ("CURRENT LEVEL visto dopo {0} Invio (t={1} s); settle {2} s" -f $enters, $script:LastMatchT, $settle)
}

function Do-Soak($st) {
    $secs = [double]$st.seconds
    $from = [string](Get-Opt $st 'from' 'now')
    $base = Get-Date
    if ($from -eq 'last_match' -and $script:LastMatchTime) { $base = $script:LastMatchTime }
    $until = $base.AddSeconds($secs)
    $shotsAt = @(Get-Opt $st 'shots_at' @())
    $done = @{}
    while ((Get-Date) -lt $until) {
        $el = ((Get-Date) - $base).TotalSeconds
        foreach ($s in $shotsAt) { if ($el -ge [double]$s -and -not $done.ContainsKey([string]$s)) { $done[[string]$s] = $true; Take-Shot ("soak_{0}s" -f $s) } }
        Pump 250
    }
    return ("vivo per {0} s da {1}" -f $secs, $from)
}

function Do-Step($st) {
    $act = [string]$st.action
    switch ($act) {
        'wait' { Pump ([int]([double]$st.seconds * 1000)); return "atteso $($st.seconds) s" }
        'focus' { Ensure-Focus; return 'focus' }
        'key' {
            Ensure-Focus
            $n = [int](Get-Opt $st 'count' 1); $hold = [int](Get-Opt $st 'hold_ms' 80); $gap = [int](Get-Opt $st 'gap_ms' 200)
            for ($i = 0; $i -lt $n; $i++) { Send-Key ([string]$st.key) $hold; if ($i -lt $n - 1) { Pump $gap } }
            return ("tasto {0} x{1} hold {2} ms" -f $st.key, $n, $hold)
        }
        'hold_key' {
            # tiene premuto un tasto (es. W per correre) per N secondi
            Ensure-Focus
            $spec = Get-KeySpec ([string]$st.key)
            Key-Down $spec
            try { Pump ([int]([double]$st.seconds * 1000)) } finally { Key-Up $spec }
            return ("tenuto {0} per {1} s" -f $st.key, $st.seconds)
        }
        'click' {
            # clic in coordinate normalizzate dell'area client (0..1): nx, ny; mode physical|post (default physical)
            Ensure-Focus
            Click-Norm ([double]$st.nx) ([double]$st.ny) ([string](Get-Opt $st 'mode' 'physical'))
            return ("click {0},{1}" -f $st.nx, $st.ny)
        }
        'type' {
            # digita testo nel campo ImGui che ha il focus; method type|char|paste (default type = scancode)
            Ensure-Focus
            Type-Text ([string]$st.text) ([string](Get-Opt $st 'method' 'type'))
            return ("digitato '{0}'" -f $st.text)
        }
        'f8' { return (Set-Menu ([string]$st.state -eq 'open') ([bool](Get-Opt $st 'verify' $true))) }
        'boot_resume' { return (Do-BootResume $st) }
        'load_unit' { return (Do-LoadUnit $st) }
        'expect' {
            $to = [double](Get-Opt $st 'timeout_s' 60)
            $from = 0
            if ([bool](Get-Opt $st 'new_only' $true)) { $from = $script:Log.Length }
            $mm = Wait-LogMatch ([string]$st.regex) $to $from
            if (-not $mm) {
                if ([bool](Get-Opt $st 'optional' $false)) { Add-Warn "expect opzionale non trovato: $($st.regex)"; return 'non trovato (opzionale)' }
                throw ("STEP_TIMEOUT:{0}:marker '{1}' non visto in {2} s" -f $st.id, $st.regex, $to)
            }
            return ("trovato '{0}' a t={1} s" -f ($mm.Value -replace '\s+', ' '), $script:LastMatchT)
        }
        'soak' { return (Do-Soak $st) }
        'shot' { Take-Shot ([string](Get-Opt $st 'name' $st.id)); return 'screenshot (solo diagnostica)' }
        'probe_start' {
            if ([string](Get-Opt $st 'mode' 'raft') -ne 'raft') { throw "INFRA:probe mode sconosciuto" }
            $base = Join-Path $script:AttemptDir ('probe_' + [string](Get-Opt $st 'mode' 'raft'))
            $script:Probe = New-RaftProbe -TruProc $script:Tru -OutBase $base -IntervalMs ([int](Get-Opt $st 'interval_ms' 100))
            return ("sonda raft avviata (base_ok={0})" -f $script:Probe.summary.base_ok)
        }
        'ext_probe' {
            # sonda vera (tools/vm_probe.ps1, PowerShell 32 bit, sola lettura) come processo figlio; attende la fine e riporta le righe di risoluzione
            $sec = [int](Get-Opt $st 'seconds' 25)
            $out = Join-Path $script:AttemptDir ('probe_ext_' + [string]$st.id + '.tsv')
            $ps32 = Join-Path $env:windir 'SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
            $pa = '-NoProfile -ExecutionPolicy Bypass -File "{0}" -Mode raft -Seconds {1} -IntervalMs {2} -RunId {3} -Out "{4}" -ProcId {5}' -f (Join-Path $PSScriptRoot 'vm_probe.ps1'), $sec, ([int](Get-Opt $st 'interval_ms' 100)), $RunId, $out, $script:Tru.Id
            $pp = Start-Process -FilePath $ps32 -ArgumentList $pa -PassThru -WindowStyle Hidden
            $until = (Get-Date).AddSeconds($sec + 25)
            while (-not $pp.HasExited -and (Get-Date) -lt $until) { Pump 500 }
            if (-not $pp.HasExited) { try { $pp.Kill() } catch {}; $script:Res['ext_probe_' + $st.id] = @{ file = $out; exit = 'timeout' }; return ("sonda esterna timeout, file {0}" -f $out) }
            $res = @(); if (Test-Path -LiteralPath $out) { $res = @(Select-String -LiteralPath $out -Pattern 'RESOLVE|RESOLUTION|SLOT|END' -ErrorAction SilentlyContinue | Select-Object -First 12 | ForEach-Object { $_.Line }) }
            $script:Res['ext_probe_' + $st.id] = @{ file = $out; exit = $pp.ExitCode; lines = $res }
            return ("sonda esterna exit {0}, file {1}" -f $pp.ExitCode, $out)
        }
        'probe_stop' {
            $sum = Close-RaftProbe $script:Probe
            $script:Probe = $null
            $script:Res['probe'] = $sum
            return 'sonda chiusa, riepilogo in result.json -> probe'
        }
        'probe_expect' {
            # PASS/FAIL da sonda memoria: ogni condizione e' un campo del riepilogo (vedi README). Nessuna condizione = solo informativa.
            $sum = $script:Res['probe']
            if (-not $sum) { throw "STEP_FAIL:$($st.id):nessun riepilogo sonda" }
            $bad = @()
            foreach ($pr in $st.conditions.PSObject.Properties) {
                $actual = $sum[$pr.Name]
                if ("$actual" -ne "$($pr.Value)") { $bad += ("{0}: atteso {1}, letto {2}" -f $pr.Name, $pr.Value, $actual) }
            }
            if ($bad.Count -gt 0) { throw ("STEP_FAIL:{0}:{1}" -f $st.id, ($bad -join '; ')) }
            return 'condizioni sonda soddisfatte'
        }
        default { throw "INFRA:azione sconosciuta '$act'" }
    }
}

function Run-Steps {
    $n = 0
    foreach ($st in @($script:Scn.steps)) {
        $n++
        $id = [string](Get-Opt $st 'id' ("s{0}" -f $n))
        if (-not $st.PSObject.Properties['id']) { $st | Add-Member -NotePropertyName id -NotePropertyValue $id }
        $script:CurStep = $id
        $row = [ordered]@{ attempt = $script:Attempt; n = $n; id = $id; action = [string]$st.action; t_start_s = Elapsed; ok = $false; detail = '' }
        $null = $script:Steps.Add($row)
        Note ("STEP {0} {1}" -f $id, $st.action)
        Write-Status 'RUNNING'
        try {
            $row.detail = [string](Do-Step $st)
            $row.ok = $true
        } catch {
            $row.detail = $_.Exception.Message
            throw
        } finally {
            $row['t_end_s'] = Elapsed
        }
    }
}

# ------------------------------------------------------------------ crash
function Get-CrashEvent {
    # Application Error (id 1000) relativo a tru.exe dopo l'avvio. Campi dalle Properties (indipendenti dalla lingua):
    # [0]=app [3]=modulo in errore [6]=codice eccezione [7]=offset. Fallback: regex sul messaggio IT/EN.
    for ($i = 0; $i -lt 25; $i++) {
        $evs = @()
        try {
            $evs = @(Get-WinEvent -FilterHashtable @{ LogName = 'Application'; Id = 1000; StartTime = $script:LaunchTime.AddSeconds(-2) } -ErrorAction Stop)
        } catch { }
        foreach ($ev in $evs) {
            $app = ''; try { $app = [string]$ev.Properties[0].Value } catch { }
            if ($app -notmatch '(?i)^tru\.exe$' -and $ev.Message -notmatch '(?i)tru\.exe') { continue }
            $r = [ordered]@{ found = $true; time = $ev.TimeCreated.ToString('yyyy-MM-ddTHH:mm:ss'); module = ''; code = ''; offset_hex = ''; offset = $null }
            try { $r.module = [string]$ev.Properties[3].Value; $r.code = [string]$ev.Properties[6].Value; $r.offset_hex = [string]$ev.Properties[7].Value } catch { }
            if (-not $r.offset_hex) {
                $m = $ev.Message
                if ($m -match '(?:Codice eccezione|Exception code):\s*(0x[0-9a-fA-F]+)') { $r.code = $Matches[1] }
                if ($m -match '(?:Offset errore|Fault offset):\s*(0x[0-9a-fA-F]+)') { $r.offset_hex = $Matches[1] }
                if ($m -match '(?:Nome modulo che ha generato l.errore|Faulting module name):\s*([^,\s]+)') { $r.module = $Matches[1] }
            }
            if ($r.offset_hex) {
                try { $r.offset = [Convert]::ToInt64(($r.offset_hex -replace '^0[xX]', ''), 16) } catch { }
            }
            return $r
        }
        Start-Sleep -Seconds 1
    }
    return [ordered]@{ found = $false; time = ''; module = ''; code = ''; offset_hex = ''; offset = $null }
}

function Classify-Crash($ev) {
    $cls = 'UNKNOWN'; $outcome = 'UNKNOWN'; $reason = ''
    if (-not $ev.found) { return @{ cls = 'NO_EVENT'; outcome = 'UNKNOWN'; reason = 'tru terminato senza evento Application Error (uscita o kill?)' } }
    if ($null -eq $ev.offset) { return @{ cls = 'UNKNOWN'; outcome = 'UNKNOWN'; reason = "offset non leggibile (codice $($ev.code))" } }
    $table = @($script:CrashTable)
    foreach ($e in @(Get-Opt $script:Scn 'crash_classes' @())) {
        $table += @{ offset = [Convert]::ToInt64(([string]$e.offset -replace '^0[xX]', ''), 16); cls = [string]$e.cls; outcome = [string]$e.outcome }
    }
    foreach ($e in $table) {
        if ([int64]$e.offset -eq [int64]$ev.offset) { return @{ cls = $e.cls; outcome = $e.outcome; reason = "crash $($e.cls) offset $($ev.offset_hex)" } }
    }
    return @{ cls = 'UNKNOWN'; outcome = 'UNKNOWN'; reason = "crash classe sconosciuta: codice $($ev.code) offset $($ev.offset_hex) modulo $($ev.module)" }
}

function Collect-Dumps([int]$n) {
    $list = @()
    $dd = 'C:\TRU_dumps'
    if (-not (Test-Path $dd)) { return $list }
    $files = @(Get-ChildItem $dd -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -ge $script:LaunchTime.AddSeconds(-5) } | Sort-Object LastWriteTime)
    foreach ($f in $files) {
        # attendi che la dimensione si stabilizzi (max ~90 s)
        $prev = -1
        for ($k = 0; $k -lt 45; $k++) {
            $f.Refresh()
            if ($f.Length -eq $prev) { break }
            $prev = $f.Length; Start-Sleep -Seconds 2
        }
        $row = [ordered]@{ name = $f.Name; size = $f.Length; md5 = (Md5Of $f.FullName); time = $f.LastWriteTime.ToString('yyyy-MM-ddTHH:mm:ss'); copied = '' }
        if ($KeepDump) {
            try {
                $dst = Join-Path $script:RunDir 'dumps'
                New-Item -ItemType Directory -Force $dst | Out-Null
                $dstFile = Join-Path $dst ("a{0}_{1}" -f $n, $f.Name)
                Copy-Item -LiteralPath $f.FullName -Destination $dstFile -Force
                $row.copied = "dumps/a${n}_$($f.Name)"
            } catch { $row.copied = "ERRORE: $($_.Exception.Message)" }
        }
        $list += , $row
    }
    return $list
}

# ------------------------------------------------------------------ processi
function Stop-Leftovers {
    # tru, logtail e gli altri script che inviano tasti da soli (sweep/autotest) - mai se stessi
    Get-Process tru -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    try {
        $me = $PID
        $cands = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.ProcessId -ne $me -and $_.CommandLine -match 'vm_(logtail|sweep_session|autotest)\.ps1' })
        foreach ($c in $cands) { Note ("kill residuo pid {0}: {1}" -f $c.ProcessId, $c.CommandLine); Stop-Process -Id $c.ProcessId -Force -ErrorAction SilentlyContinue }
    } catch { Add-Warn "pulizia residui: $($_.Exception.Message)" }
    Get-Process WerFault -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    for ($i = 0; $i -lt 15; $i++) { if (-not (Get-Process tru -ErrorAction SilentlyContinue)) { break }; Start-Sleep -Seconds 1 }
    if (Get-Process tru -ErrorAction SilentlyContinue) { throw 'INFRA:tru residuo non terminabile' }
    Start-Sleep -Seconds 3
}

function Launch-Tru {
    $steam = 'C:\Program Files (x86)\Steam\steam.exe'
    if (-not (Test-Path $steam)) { throw 'INFRA:steam.exe non trovato' }
    $script:LaunchTime = Get-Date
    $p = $null
    for ($i = 0; $i -lt 3 -and -not $p; $i++) {
        Start-Process -FilePath $steam -ArgumentList '-applaunch', '8140' | Out-Null
        for ($j = 0; $j -lt 20 -and -not $p; $j++) { Start-Sleep -Seconds 2; $p = Get-Process tru -ErrorAction SilentlyContinue | Select-Object -First 1 }
    }
    if (-not $p) { throw 'INFRA:tru non avviato da Steam (-applaunch 8140)' }
    $script:Tru = $p
    $script:ProcH = Open-ProbeHandle -ProcId $p.Id
    # finestra
    $hw = [IntPtr]::Zero
    for ($j = 0; $j -lt 60; $j++) {
        $p.Refresh()
        if ($p.HasExited) { throw 'TRU_DEAD' }
        $hw = $p.MainWindowHandle
        if ($hw -ne [IntPtr]::Zero) { break }
        Start-Sleep -Seconds 1
    }
    if ($hw -eq [IntPtr]::Zero) { throw 'INFRA:finestra di tru non comparsa in 60 s' }
    $script:Hwnd = $hw
    Start-Sleep -Seconds 3
    $null = Focus-Game $true
    Note ("tru pid {0} hwnd 0x{1:x}" -f $p.Id, $hw.ToInt64())
}

function Start-Logtail {
    $ps32 = 'C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
    if (-not (Test-Path $ps32)) { $ps32 = (Get-Command powershell.exe).Source; Add-Warn 'SysWOW64 powershell non trovata: logtail potrebbe non leggere tru' }
    $lt = Join-Path $PSScriptRoot 'vm_logtail.ps1'
    $secs = [int]([Math]::Max(120, ($script:Deadline - (Get-Date)).TotalSeconds + 60))
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', ('"' + $lt + '"'), '-Out', ('"' + $script:LogFile + '"'), '-Seconds', "$secs", '-Interval', '2')
    $script:LogtailProc = Start-Process -FilePath $ps32 -ArgumentList $a -WindowStyle Hidden -PassThru
    Note ("logtail pid {0} -> {1}" -f $script:LogtailProc.Id, $script:LogFile)
}

# ------------------------------------------------------------------ baseline / save
function Verify-Baseline([string]$baselineId, [string]$mode, $critGlobs) {
    $bdir = Join-Path (Join-Path $Root 'work\baseline') $baselineId
    $r = [ordered]@{ baseline = $baselineId; mode = $mode; manifest = ''; ok = $null; checked = 0; critical_count = 0; missing = @(); size_mismatch = @(); md5_mismatch = @(); extra_count = $null; note = '' }
    $mf = Join-Path $bdir 'manifest'
    if (-not (Test-Path -LiteralPath $mf)) { $mf = Join-Path $bdir 'manifest.tsv' }
    if (-not (Test-Path -LiteralPath $mf)) { $mf = Join-Path $bdir 'mods.tsv'; $r.note = 'manifest assente: uso mods.tsv (nessuna colonna critical: solo da scenario)' }
    if (-not (Test-Path -LiteralPath $mf)) { $r.ok = $false; $r.note = "nessun manifest in $bdir"; return $r }
    $r.manifest = $mf
    $mods = Join-Path $GameDir 'mods'
    $entries = @()
    foreach ($ln in [IO.File]::ReadAllLines($mf)) {
        if (-not $ln.Trim() -or $ln.StartsWith('#')) { continue }
        $c = $ln.Split("`t")
        if ($c.Count -lt 3) { continue }
        $sz = 0L
        if (-not [int64]::TryParse($c[1], [ref]$sz)) { continue }       # salta eventuale intestazione
        $crit = $false
        $relN = $c[0].Replace('/', '\')                                   # manifest in stile posix: normalizza come i percorsi Windows
        $critCol = if ($c.Count -ge 6) { 4 } else { 3 }                    # manifest baseline_build: relpath,size,md5,origin,critical,exception
        if ($c.Count -gt $critCol -and $c[$critCol].Trim().ToLower() -in @('1', 'critical', 'true', 'yes', 'y', 'c')) { $crit = $true }
        foreach ($g in @($critGlobs)) { if ($g -and ($relN -like [string]$g)) { $crit = $true } }
        $entries += , @{ rel = $relN; size = $sz; md5 = $c[2].Trim().ToLower(); crit = $crit }
    }
    $r.critical_count = @($entries | Where-Object { $_.crit }).Count
    # mappa dei file presenti (nome relativo minuscolo -> dimensione): controllo di esistenza/dimensione su tutto, a costo quasi nullo
    $have = @{}
    foreach ($f in @(Get-ChildItem -LiteralPath $mods -Recurse -File -Force -ErrorAction SilentlyContinue)) { $have[$f.FullName.Substring($mods.Length + 1).ToLower()] = $f.Length }
    $known = @{}; foreach ($e in $entries) { $known[$e.rel.ToLower()] = $true }
    $extra = 0; foreach ($k in $have.Keys) { if (-not $known.ContainsKey($k)) { $extra++ } }
    $r.extra_count = $extra
    $miss = @(); $szm = @(); $md = @()
    $nChecked = 0
    foreach ($e in $entries) {
        $k = $e.rel.ToLower()
        if (-not $have.ContainsKey($k)) { $miss += $e.rel; continue }
        if ($have[$k] -ne $e.size) { $szm += $e.rel; continue }
        if ($mode -eq 'full' -or $e.crit) {
            $h = Md5Of (Join-Path $mods $e.rel)
            $nChecked++
            if ($h -ne $e.md5) { $md += $e.rel }
            if (($nChecked % 25) -eq 0) { Write-Status 'PREFLIGHT'; Note "verifica md5: $nChecked" }
        }
    }
    $r.checked = $nChecked
    $r.missing = @($miss | Select-Object -First 50); $r.size_mismatch = @($szm | Select-Object -First 50); $r.md5_mismatch = @($md | Select-Object -First 50)
    $r['missing_total'] = $miss.Count; $r['size_mismatch_total'] = $szm.Count; $r['md5_mismatch_total'] = $md.Count
    if ($mode -eq 'fast' -and $r.critical_count -eq 0) { $r.note = ($r.note + ' ATTENZIONE: nessun file critical: md5 non verificato (solo esistenza+dimensione).').Trim() }
    $r.ok = ($miss.Count -eq 0 -and $szm.Count -eq 0 -and $md.Count -eq 0 -and ($mode -eq 'full' -or $r.critical_count -gt 0))
    if ($mode -eq 'full' -and $extra -gt 0) { $r.note = ($r.note + " $extra file in mods\ non presenti nel manifest (info).").Trim() }
    return $r
}

function Get-SaveDir {
    $d = Join-Path $env:USERPROFILE 'Documents\Eidos\Tomb Raider - Underworld'
    if (-not (Test-Path -LiteralPath $d)) {
        $docs = [Environment]::GetFolderPath('MyDocuments')
        $d2 = Join-Path $docs 'Eidos\Tomb Raider - Underworld'
        if (Test-Path -LiteralPath $d2) { return $d2 }
    }
    return $d
}

function Save-List([string]$dir) {
    $l = @()
    if (Test-Path -LiteralPath $dir) {
        foreach ($f in @(Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue | Sort-Object Name)) {
            $l += , ([ordered]@{ name = $f.Name; size = $f.Length; md5 = (Md5Of $f.FullName); mtime = $f.LastWriteTime.ToString('yyyy-MM-ddTHH:mm:ss') })
        }
    }
    return $l
}

function Resolve-SaveSet {
    $sv = Get-Opt $script:Scn 'saves' $null
    if (-not $sv) { return $null }
    $set = [string](Get-Opt $sv 'set' '')
    $dir = Join-Path (Join-Path (Join-Path $Root 'work\baseline') 'saves') $set
    if ($set -and (Test-Path -LiteralPath $dir) -and @(Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue).Count -gt 0) { return @{ dir = $dir; src = "baseline\saves\$set" } }
    if ([bool](Get-Opt $sv 'fallback_baseline' $false)) {
        $fb = Join-Path (Join-Path (Join-Path $Root 'work\baseline') $script:BaselineId) 'saves'
        if (Test-Path -LiteralPath $fb) { Add-Warn "set di save '$set' assente: uso il fallback $fb"; return @{ dir = $fb; src = "baseline\$($script:BaselineId)\saves (fallback)" } }
    }
    throw "INFRA:set di save '$set' non trovato in $dir (e nessun fallback)"
}

function Restore-Saves {
    $sv = Get-Opt $script:Scn 'saves' $null
    if (-not $sv) { return }
    $set = Resolve-SaveSet
    $dst = Get-SaveDir
    New-Item -ItemType Directory -Force $dst | Out-Null
    $copied = @()
    foreach ($f in @(Get-ChildItem -LiteralPath $set.dir -File)) {
        Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $dst $f.Name) -Force
        $copied += $f.Name
    }
    # copie con altro nome (es. Savegame 1 -> Autosave) cosi' Resume carica quel contenuto qualunque file scelga
    $also = Get-Opt $sv 'also_as' $null
    if ($also) {
        foreach ($pr in $also.PSObject.Properties) {
            $srcF = Join-Path $dst $pr.Name
            if (Test-Path -LiteralPath $srcF) { Copy-Item -LiteralPath $srcF -Destination (Join-Path $dst ([string]$pr.Value)) -Force; $copied += ("{0} -> {1}" -f $pr.Name, $pr.Value) }
            else { Add-Warn "also_as: $($pr.Name) assente" }
        }
    }
    # i set di save della baseline sono di sola lettura (baseline immutabile): il gioco deve poter riscrivere i suoi file
    foreach ($rf in @(Get-ChildItem -LiteralPath $dst -File -ErrorAction SilentlyContinue)) { if ($rf.IsReadOnly) { $rf.IsReadOnly = $false } }
    # 'touch': aggiorna la data cosi' e' il piu' recente
    foreach ($t in @(Get-Opt $sv 'touch' @())) {
        $tf = Join-Path $dst ([string]$t)
        if (Test-Path -LiteralPath $tf) { (Get-Item -LiteralPath $tf).LastWriteTime = Get-Date }
    }
    $script:Res.save['restored_from'] = $set.src
    $script:Res.save['restored_files'] = @($copied)
    $script:Res.save['after_restore'] = @(Save-List $dst)
    Note ("save ripristinati da {0}: {1}" -f $set.src, ($copied -join ', '))
}

# ------------------------------------------------------------------ parametri scenario
function Expand-Params($o) {
    if ($o -is [string]) {
        if ($o -match '^\$\{(\w+)\}$') {
            $v = $script:ScnParams[$Matches[1]]
            if ($null -eq $v) { throw "INFRA:parametro scenario '$($Matches[1])' senza valore" }
            return $v
        }
        return [regex]::Replace($o, '\$\{(\w+)\}', { param($m) [string]$script:ScnParams[$m.Groups[1].Value] })
    }
    if ($o -is [System.Management.Automation.PSCustomObject]) {
        foreach ($pr in @($o.PSObject.Properties)) { $o.($pr.Name) = (Expand-Params $pr.Value) }
        return $o
    }
    if ($o -is [System.Array]) {
        $out = @(); foreach ($x in $o) { $out += , (Expand-Params $x) }
        return , $out
    }
    return $o
}

function Parse-Params([string]$s) {
    $h = @{}
    foreach ($kv in @($s -split '[;,]')) {
        if (-not $kv.Trim()) { continue }
        $i = $kv.IndexOf('=')
        if ($i -lt 1) { continue }
        $k = $kv.Substring(0, $i).Trim(); $v = $kv.Substring($i + 1).Trim()
        $d = 0.0
        if ($v -match '^-?\d+$') { $h[$k] = [int]$v } elseif ([double]::TryParse($v, [Globalization.NumberStyles]::Float, [Globalization.CultureInfo]::InvariantCulture, [ref]$d)) { $h[$k] = $d } else { $h[$k] = $v }
    }
    return $h
}

# ------------------------------------------------------------------ un tentativo
function Run-Attempt([int]$n) {
    $a = [ordered]@{ n = $n; outcome = 'RUNNING'; reason = ''; started = Now-Iso; retry = $false; crash = $null; dumps = @(); probe = $null; error_dialog = @(); duration_s = $null }
    $script:Attempt = $n
    $script:Deadline = (Get-Date).AddSeconds($script:TMax)
    $script:AttemptDir = Join-Path $script:RunDir ("a{0}" -f $n)
    New-Item -ItemType Directory -Force (Join-Path $script:AttemptDir 'shots') | Out-Null
    $script:LogFile = Join-Path $script:AttemptDir 'engine.log'
    $script:Log = ''; $script:LogLen = 0; $script:LogBytes = -1; $script:LogMtime = [datetime]::MinValue
    $script:LastMatchTime = $null; $script:LastMatchT = $null; $script:Dialogs = @(); $script:Probe = $null; $script:MenuOpen = $false
    Init-Markers
    $tA = Get-Date
    $truAlive = $false
    try {
        Stop-Leftovers
        if (-not $NoSaveRestore) { Restore-Saves }
        Launch-Tru
        Start-Logtail
        Run-Steps
        # --- verdetto da marker
        Pump 500
        $req = @(Get-Opt $script:Scn 'require_markers' @())
        $notFound = @()
        foreach ($rq in $req) {
            $m = $script:Markers | Where-Object { $_.name -eq [string]$rq } | Select-Object -First 1
            if (-not $m -or -not $m.found) { $notFound += [string]$rq }
        }
        $dlgs = @($script:Dialogs)
        if ($notFound.Count -gt 0) { $a.outcome = 'FAIL'; $a.reason = 'marker richiesti mancanti: ' + ($notFound -join ', ') }
        elseif ($dlgs.Count -gt 0 -and -not [bool](Get-Opt $script:Scn 'ignore_dialogs' $false)) { $a.outcome = 'UNKNOWN'; $a.reason = 'scenario completato ma finestra di dialogo (#32770, errore motore?) aperta: ' + ($dlgs -join ' / ') }
        else { $a.outcome = 'PASS'; $a.reason = [string](Get-Opt $script:Scn 'pass_text' 'tutti i passi completati senza crash') }
    } catch {
        $msg = $_.Exception.Message
        Note ("eccezione: " + $msg)
        if ($msg -eq 'TRU_DEAD') {
            $ev = Get-CrashEvent
            $cl = Classify-Crash $ev
            $a.crash = [ordered]@{ event = $ev; class = $cl.cls }
            $a.outcome = $cl.outcome; $a.reason = $cl.reason + " (durante il passo '$($script:CurStep)')"
            if ($cl.cls -eq 'FMOD' -and $n -eq 1 -and -not $NoRetry) { $a.retry = $true }
        }
        elseif ($msg -eq 'TOTAL_TIMEOUT') { $a.outcome = 'TIMEOUT'; $a.reason = "tetto totale di tempo superato durante il passo '$($script:CurStep)'" }
        elseif ($msg -like 'STEP_TIMEOUT:*') { $a.outcome = 'TIMEOUT'; $a.reason = $msg.Substring(13) }
        elseif ($msg -like 'STEP_FAIL:*') {
            $a.outcome = 'FAIL'; $a.reason = $msg.Substring(10)
        }
        elseif ($msg -like 'INFRA:*') { $a.outcome = 'INFRA'; $a.reason = $msg.Substring(6) }
        else { $a.outcome = 'INFRA'; $a.reason = "errore del runner: $msg @ $($_.InvocationInfo.ScriptLineNumber)" }
    }
    finally {
        # --- teardown: screenshot finale, ultimo log, sonda, processi
        try {
            if ($script:Tru) { $script:Tru.Refresh(); $truAlive = -not $script:Tru.HasExited }
            if ($truAlive) {
                $a.error_dialog = @($script:Dialogs)
                Take-Shot 'final'
                Start-Sleep -Milliseconds 2500       # lascia a logtail un ultimo giro (intervallo 2 s)
                Read-LogFile
            }
            if ($script:Probe) { $a.probe = Close-RaftProbe $script:Probe; $script:Probe = $null }
            elseif ($script:Res['probe']) { $a.probe = $script:Res['probe'] }
            Final-MarkerCounts
            Save-Result
        } catch { Note ("teardown: " + $_.Exception.Message) }
        if ($a.crash) { $a.dumps = @(Collect-Dumps $n) }
        try { if ($script:LogtailProc -and -not $script:LogtailProc.HasExited) { Stop-Process -Id $script:LogtailProc.Id -Force -ErrorAction SilentlyContinue } } catch { }
        $isFinal = (-not $a.retry)
        if ($script:Tru -and -not ($KeepGame -and $isFinal)) { Get-Process tru -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue }
        Get-Process WerFault -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        if ($script:ProcH -ne [IntPtr]::Zero) { [void][ProbeNative]::CloseHandle($script:ProcH); $script:ProcH = [IntPtr]::Zero }
        $a.duration_s = [math]::Round(((Get-Date) - $tA).TotalSeconds, 1)
        $a['markers'] = Get-MarkerReport
        $a['log_chars'] = $script:LogLen
        $script:Tru = $null
    }
    return $a
}

# ================================================================== MAIN
$script:ScnName = $Scenario
if ($RunId -notmatch '^[A-Za-z0-9_.\-]{1,80}$') { Write-Output 'RunId non valido (ammessi A-Z a-z 0-9 _ . -)'; exit 2 }
$runsRoot = Join-Path (Join-Path $Root 'work') 'runs'
New-Item -ItemType Directory -Force $runsRoot | Out-Null
$script:RunDir = Join-Path $runsRoot $RunId
if (Test-Path -LiteralPath $script:RunDir) {
    Write-Text (Join-Path $runsRoot ("{0}.refused.txt" -f $RunId)) ("rifiutato {0}: la cartella del run esiste gia' ({1})`r`n" -f (Now-Iso), $script:RunDir)
    Write-Output 'run esistente: usare un RunId nuovo'
    exit 2
}
New-Item -ItemType Directory -Force $script:RunDir | Out-Null
$script:ResultPath = Join-Path $script:RunDir 'result.json'
$script:StatusPath = Join-Path $script:RunDir 'status.txt'
$script:RunnerLog = Join-Path $script:RunDir 'runner.log'
$lockPath = Join-Path $runsRoot '.lock'
$script:BaselineId = $Baseline

$myScript = $MyInvocation.MyCommand.Path
$script:Res = [ordered]@{
    schema = 1; runner_version = $RunnerVersion; scenario = $Scenario; runId = $RunId; baselineId = $null; verify = $Verify
    outcome = 'RUNNING'; reason = ''; started = Now-Iso; updated = Now-Iso; ended = $null; duration_s = 0
    runner = [ordered]@{ script = $myScript; script_md5 = (Md5Of $myScript); ps_version = $PSVersionTable.PSVersion.ToString(); bitness = ([IntPtr]::Size * 8); pid = $PID; host = $env:COMPUTERNAME; command_line = [Environment]::CommandLine }
    session = [ordered]@{}
    baseline = $null
    tru_exe = [ordered]@{ path = (Join-Path $GameDir 'tru.exe'); size = $null; md5 = $null }
    save = [ordered]@{ dir = ''; before = @(); after = @(); restored_from = ''; restored_files = @() }
    attempts = @(); crash = $null; dumps = @(); probe = $null; log_tail = @()
    steps = @(); shots = @(); warnings = @(); markers = $null
}

try {
    # --- lock
    if (Test-Path -LiteralPath $lockPath) {
        $old = ''; try { $old = [IO.File]::ReadAllText($lockPath) } catch { }
        $oldPid = 0
        if ($old -match 'pid=(\d+)') { $oldPid = [int]$Matches[1] }
        $alive = $false
        if ($oldPid -gt 0) { $alive = [bool](Get-Process -Id $oldPid -ErrorAction SilentlyContinue) }
        if ($alive) { throw "INFRA:un altro run e' attivo (lock: $old)" }
        Note "lock vecchio ignorato: $old"
    }
    Write-Text $lockPath ("run={0} pid={1} started={2}`r`n" -f $RunId, $PID, (Now-Iso))
    Write-Status 'PREFLIGHT'

    # --- scenario
    $scnPath = $Scenario
    if (-not (Test-Path -LiteralPath $scnPath)) { $scnPath = Join-Path (Join-Path $PSScriptRoot 'runner_scenarios') ($Scenario + '.json') }
    if (-not (Test-Path -LiteralPath $scnPath)) { throw "INFRA:scenario '$Scenario' non trovato ($scnPath)" }
    $raw = [IO.File]::ReadAllText($scnPath, [Text.Encoding]::UTF8)
    $scn = $raw | ConvertFrom-Json
    # parametri: default dallo scenario poi override da -Param
    $script:ScnParams = @{}
    $dp = Get-Opt $scn 'params' $null
    if ($dp) { foreach ($pr in $dp.PSObject.Properties) { $script:ScnParams[$pr.Name] = $pr.Value } }
    foreach ($kv in (Parse-Params $Param).GetEnumerator()) { $script:ScnParams[$kv.Key] = $kv.Value }
    $script:Scn = Expand-Params $scn
    $script:ScnName = [string](Get-Opt $script:Scn 'name' $Scenario)
    $script:Res.scenario = $script:ScnName
    $script:Res['scenario_file'] = $scnPath
    $script:Res['scenario_md5'] = (Md5Of $scnPath)
    $script:Res['params'] = $script:ScnParams
    if (-not $script:BaselineId) { $script:BaselineId = [string](Get-Opt $script:Scn 'baseline' 'B0_raw') }
    $script:Res.baselineId = $script:BaselineId
    $tmax = $MaxSeconds
    if ($tmax -le 0) { $tmo = Get-Opt $script:Scn 'timeouts' $null; $tmax = [int](Get-Opt $tmo 'total_s' 600) }
    $script:TMax = $tmax
    $script:Deadline = (Get-Date).AddSeconds($tmax)
    $script:Res['max_seconds'] = $tmax
    Note ("scenario {0} ({1}) baseline {2} verify {3} max {4} s" -f $script:ScnName, $scnPath, $script:BaselineId, $Verify, $tmax)

    # --- preflight: sessione
    $mySession = [Diagnostics.Process]::GetCurrentProcess().SessionId
    $expl = @(Get-Process explorer -ErrorAction SilentlyContinue | ForEach-Object { $_.SessionId } | Sort-Object -Unique)
    $interactive = ($mySession -ne 0 -and ($expl -contains $mySession))
    $script:Res.session = [ordered]@{ runner_session = $mySession; explorer_sessions = @($expl); interactive = $interactive; user = "$env:USERDOMAIN\$env:USERNAME" }
    if (-not $interactive -and -not $PreflightOnly) { throw "INFRA:il runner non gira nella sessione interattiva (sessione $mySession, explorer in [$($expl -join ',')]): tasti/mouse/focus non funzionerebbero. Vedi README (task pianificato /IT)." }
    if (-not $interactive) { Add-Warn 'sessione non interattiva (PreflightOnly: continuo)' }
    if ([IntPtr]::Size -ne 4) { Add-Warn 'PowerShell a 64 bit: ok per input/sonde, ma preferire SysWOW64 (vedi README)' }

    # --- preflight: exe, baseline
    $exe = Join-Path $GameDir 'tru.exe'
    if (-not (Test-Path -LiteralPath $exe)) { throw 'INFRA:tru.exe non trovato' }
    $script:Res.tru_exe.size = (Get-Item -LiteralPath $exe).Length
    $script:Res.tru_exe.md5 = (Md5Of $exe)
    $crit = @(Get-Opt $script:Scn 'critical' @())
    $vmode = $Verify
    $sv = Get-Opt $script:Scn 'verify' $null
    $bl = Verify-Baseline $script:BaselineId $vmode $crit
    $script:Res.baseline = $bl
    Note ("baseline ok={0} checked={1} missing={2} size_mm={3} md5_mm={4} note={5}" -f $bl.ok, $bl.checked, $bl['missing_total'], $bl['size_mismatch_total'], $bl['md5_mismatch_total'], $bl.note)
    if ($bl.ok -ne $true) { Add-Warn 'baseline NON verificata/diversa: i risultati di questo run vanno presi con cautela' }
    if ($StrictBaseline -and $bl.ok -ne $true) { throw 'INFRA:baseline diversa dal manifest (-StrictBaseline)' }

    # --- save prima
    $sdir = Get-SaveDir
    $script:Res.save.dir = $sdir
    $script:Res.save.before = @(Save-List $sdir)
    if (Test-Path -LiteralPath $sdir) {
        $sb = Join-Path $script:RunDir 'save_before'
        New-Item -ItemType Directory -Force $sb | Out-Null
        foreach ($f in @(Get-ChildItem -LiteralPath $sdir -File -ErrorAction SilentlyContinue)) { Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $sb $f.Name) -Force }
    }
    if (-not $NoSaveRestore -and (Get-Opt $script:Scn 'saves' $null)) { $null = Resolve-SaveSet }      # fallisce subito (INFRA) se il set manca
    Save-Result

    if ($PreflightOnly) {
        $script:Res.outcome = 'PREFLIGHT_OK'; $script:Res.reason = 'solo preflight (nessun avvio del gioco)'
    } else {
        $atts = @()
        $final = $null
        for ($n = 1; $n -le 2; $n++) {
            $ra = @(Run-Attempt $n)
            $a = $ra[$ra.Count - 1]
            $atts += , $a
            $script:Res.attempts = @($atts)
            $final = $a
            Save-Result
            if (-not $a.retry) { break }
            Note 'ritentativo (FMOD): attendo 10 s e riparto con tru nuovo'
            Start-Sleep -Seconds 10
        }
        $script:Res.outcome = $final.outcome
        $script:Res.reason = $final.reason
        $script:Res.crash = $final.crash
        $script:Res.dumps = @($final.dumps)
        if ($final.probe) { $script:Res.probe = $final.probe }
        if ($atts.Count -gt 1) { $script:Res['retried'] = $true; $script:Res.reason = $script:Res.reason + " [dopo ritentativo; tentativo 1: $($atts[0].outcome): $($atts[0].reason)]" }
        # coda del log + copia del log del tentativo finale al primo livello
        $lf = Join-Path (Join-Path $script:RunDir ("a{0}" -f $final.n)) 'engine.log'
        if (Test-Path -LiteralPath $lf) {
            try {
                Copy-Item -LiteralPath $lf -Destination (Join-Path $script:RunDir 'engine.log') -Force
                $lines = @([IO.File]::ReadAllLines($lf, [Text.Encoding]::UTF8))
                $tail = @($lines | Select-Object -Last 200)
                Write-Text (Join-Path $script:RunDir 'log_tail.txt') (($tail -join "`r`n") + "`r`n")
                $script:Res.log_tail = @($lines | Select-Object -Last 40)
            } catch { Add-Warn "coda log: $($_.Exception.Message)" }
        } else { Add-Warn 'engine.log assente (logtail non ha scritto nulla)' }
        $script:Res.save.after = @(Save-List $sdir)
    }
}
catch {
    $m = $_.Exception.Message
    $script:Res.outcome = 'INFRA'
    $script:Res.reason = $(if ($m -like 'INFRA:*') { $m.Substring(6) } else { "errore del runner: $m @ riga $($_.InvocationInfo.ScriptLineNumber)" })
    Note ("FATAL " + $script:Res.reason)
    try { if (-not $KeepGame -and $script:Attempt -gt 0) { Get-Process tru -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue } } catch { }
}
finally {
    $script:Res.ended = Now-Iso
    Save-Result
    Write-Status ('DONE ' + $script:Res.outcome)
    try {
        $cur = ''; if (Test-Path -LiteralPath $lockPath) { $cur = [IO.File]::ReadAllText($lockPath) }
        if ($cur -match "pid=$PID\b") { Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue }
    } catch { }
}
Write-Output ("{0} {1}" -f $script:Res.outcome, $script:Res.reason)
