# vm_probe_lib.ps1 - sonde di memoria SOLA LETTURA su tru.exe (PowerShell 5.1, nessun modulo, nessuna rete).
# Due usi:
#   1) dot-source da vm_run.ps1:   . "$PSScriptRoot\vm_probe_lib.ps1"   (nessun parametro: definisce solo funzioni/tipi)
#      -> New-RaftProbe / Step-RaftProbe / Get-RaftProbeSummary / Close-RaftProbe; vm_run chiama Step ad ogni giro di Pump.
#   2) stand-alone (si aggancia al tru gia' in esecuzione, scrive un log tsv + riepilogo json):
#      C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_probe_lib.ps1 -Mode raft -ProbeOut Z:\tru-port\work\runs\X\probe_raft -ProbeSeconds 30 -ProbeInterval 100
#
# STATO: modo 'raft' = SEGNAPOSTO costruito sulla specifica work/ws/chainshot/INSTRUMENT_SPEC.md (sez. 4, punti 1,2,3,5;
#        il punto 4 'appartenenza liste' NON e' implementato). Tutti gli offset sono quelli della spec (certezza B/C):
#        NON verificati in VM. Se la verifica di base (MZ a 0x400000) o i magic della sezione falliscono, la sonda lo scrive
#        nel riepilogo e prosegue senza fallire. Nessuna scrittura nella memoria del gioco.
param(
    [string]$Mode = '',
    [string]$ProbeOut = '',
    [int]$ProbeSeconds = 30,
    [int]$ProbeInterval = 100
)

if (-not ('ProbeNative' -as [type])) {
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;
public static class ProbeNative {
    [DllImport("kernel32.dll")] public static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
    [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr h);
    [DllImport("kernel32.dll")] static extern bool ReadProcessMemory(IntPtr h, IntPtr addr, byte[] buf, int n, out int read);
    static IntPtr Ptr(long a) {
        if (IntPtr.Size == 4) { return new IntPtr(unchecked((int)(uint)a)); }
        return new IntPtr(a);
    }
    public static byte[] Bytes(IntPtr h, long addr, int n) {
        byte[] b = new byte[n]; int r;
        if (!ReadProcessMemory(h, Ptr(addr), b, n, out r) || r != n) { throw new InvalidOperationException("read fail 0x" + addr.ToString("x")); }
        return b;
    }
    public static long U32(IntPtr h, long addr) { return (long)BitConverter.ToUInt32(Bytes(h, addr, 4), 0); }
    public static int I32(IntPtr h, long addr) { return BitConverter.ToInt32(Bytes(h, addr, 4), 0); }
    public static float F32(IntPtr h, long addr) { return BitConverter.ToSingle(Bytes(h, addr, 4), 0); }
    public static int U8(IntPtr h, long addr) { return (int)Bytes(h, addr, 1)[0]; }
    public static string Ascii(IntPtr h, long addr, int max) {
        byte[] b = Bytes(h, addr, max); int z = Array.IndexOf(b, (byte)0);
        if (z < 0) { z = max; }
        return Encoding.ASCII.GetString(b, 0, z);
    }
    // Lista globale di istanze (head letto da headAddr; next a +0x08; def a +0x10; Object.uniqueID a def+0x14).
    // Ritorna coppie piatte [inst0, uid0, inst1, uid1, ...]; uid = -1 se non leggibile. Massimo 'max' istanze.
    public static long[] Instances(IntPtr h, long headAddr, int max) {
        List<long> res = new List<long>();
        long p = U32(h, headAddr); int n = 0;
        while (p != 0 && n < max) {
            long uid = -1;
            try { long def = U32(h, p + 0x10); if (def != 0) { uid = U32(h, def + 0x14); } } catch (Exception) { }
            res.Add(p); res.Add(uid); n++;
            try { p = U32(h, p + 0x08); } catch (Exception) { break; }
        }
        return res.ToArray();
    }
}
"@
}

# ---- costanti dalla spec (decimali: PowerShell legge 0xf0012345 come Int32 negativo)
$script:PB_ADDR_LARA      = 0xe7f094
$script:PB_ADDR_MGR       = 0xfadfac
$script:PB_ADDR_WPNPTR    = 0xfadb58
$script:PB_ADDR_INSTHEAD  = 0xd98d54
$script:PB_MAGIC70        = 4026606405   # 0xf0012345
$script:PB_MAGIC60        = 4272233246   # 0xfea51b1e
$script:PB_UID_RAFT       = 844          # Object.uniqueID del raft (B: da verificare)
$script:PB_UID_BULLET     = 59           # pr_handgunbullet (B: da verificare)

function Open-ProbeHandle {
    param([int]$ProcId)
    return [ProbeNative]::OpenProcess([uint32]0x0410, $false, [uint32]$ProcId)
}

function Read-ProbeByte {
    # ritorna il byte o $null se non leggibile (non lancia)
    param($Handle, [long]$Addr)
    try { return [ProbeNative]::U8($Handle, $Addr) } catch { return $null }
}

function New-RaftProbe {
    param($TruProc, [string]$OutBase = '', [int]$IntervalMs = 100)
    $h = Open-ProbeHandle -ProcId $TruProc.Id
    $p = [ordered]@{
        handle = $h; interval = $IntervalMs; out = $OutBase; t0 = Get-Date; last = [datetime]::MinValue
        lastFull = [datetime]::MinValue; sig = @{}; lines = New-Object System.Collections.ArrayList
        summary = [ordered]@{
            mode = 'raft'; placeholder = $true; handle_ok = ($h -ne [IntPtr]::Zero); base_ok = $false
            polls = 0; read_errors = 0; raft_count_max = 0; sec_ok_max = 0; bullets_max = 0; bullet_events = 0
            lara_ptr = $null; mgr_ptr = $null; wpn_ptr = $null; latch_seen = $false; latch_first_ms = $null
            desc52 = @(); desc2c = @(); life_min = $null; life_max = $null; node_names = @(); node_idx_changes = @()
            note = 'segnaposto: offset dalla spec chainshot, non verificati in VM'
        }
        seenIdx = @{}; prevBullets = 0
    }
    if ($h -ne [IntPtr]::Zero) {
        try {
            $mz = [ProbeNative]::Bytes($h, 0x400000, 2)
            $p.summary.base_ok = ($mz[0] -eq 0x4D -and $mz[1] -eq 0x5A)
        } catch { $p.summary.base_ok = $false }
    }
    return $p
}

function Add-ProbeLine {
    param($P, [string]$Kind, [string]$Text)
    $ms = [int]((Get-Date) - $P.t0).TotalMilliseconds
    $null = $P.lines.Add(("{0}`t{1}`t{2}" -f $ms, $Kind, $Text))
}

function Step-RaftProbe {
    # un giro di sondaggio; rispetta l'intervallo; non lancia mai
    param($P)
    if (-not $P -or $P.handle -eq [IntPtr]::Zero) { return }
    $now = Get-Date
    if (($now - $P.last).TotalMilliseconds -lt $P.interval) { return }
    $P.last = $now
    $h = $P.handle; $s = $P.summary
    $s.polls++
    if (-not $s.base_ok) { return }     # layout diverso (rebase): non leggere a caso
    try {
        $s.lara_ptr = [ProbeNative]::U32($h, $script:PB_ADDR_LARA)
        $s.mgr_ptr = [ProbeNative]::U32($h, $script:PB_ADDR_MGR)
        $wp = [ProbeNative]::U32($h, $script:PB_ADDR_WPNPTR)
        $w = 0
        if ($wp -ne 0) { $w = [ProbeNative]::U32($h, $wp + 0x504) }
        if ($w -ne 0) {
            $latch = [ProbeNative]::U32($h, $w + 0x1fc)
            if (($latch -band 0x1000000) -ne 0 -and -not $s.latch_seen) {
                $s.latch_seen = $true; $s.latch_first_ms = [int]((Get-Date) - $P.t0).TotalMilliseconds
                Add-ProbeLine $P 'latch' ("W=0x{0:x} [W+0x1fc]=0x{1:x}" -f $w, $latch)
            }
        }
        $pairs = [ProbeNative]::Instances($h, $script:PB_ADDR_INSTHEAD, 5000)
        $nb = 0; $rafts = @()
        for ($i = 0; $i -lt $pairs.Length; $i += 2) {
            if ($pairs[$i + 1] -eq $script:PB_UID_RAFT) { $rafts += $pairs[$i] }
            elseif ($pairs[$i + 1] -eq $script:PB_UID_BULLET) { $nb++ }
        }
        if ($rafts.Count -gt $s.raft_count_max) { $s.raft_count_max = $rafts.Count }
        if ($nb -gt $s.bullets_max) { $s.bullets_max = $nb }
        if ($nb -gt $P.prevBullets) { $s.bullet_events++; Add-ProbeLine $P 'bullet' ("count {0} -> {1}" -f $P.prevBullets, $nb) }
        $P.prevBullets = $nb
        $secOk = 0
        foreach ($inst in $rafts) {
            try {
                $a = [ProbeNative]::U32($h, $inst + 0x2d0)
                $b = [ProbeNative]::U32($h, $a)
                $c = [ProbeNative]::U32($h, $b + 0x2ec)
                $sec = $c - 0x10
                $m70 = [ProbeNative]::U32($h, $sec + 0x70); $m60 = [ProbeNative]::U32($h, $sec + 0x60)
                if ($m70 -ne $script:PB_MAGIC70 -or $m60 -ne $script:PB_MAGIC60) { continue }
                $secOk++
                $desc = [ProbeNative]::U32($h, $sec + 0x78)
                $d52 = [ProbeNative]::U8($h, $desc + 0x52); $d2c = [ProbeNative]::U8($h, $desc + 0x2c)
                $f80 = [ProbeNative]::U32($h, $sec + 0x80); $idx = [ProbeNative]::I32($h, $sec + 0x84)
                $f8c = [ProbeNative]::U32($h, $sec + 0x8c); $f90 = [ProbeNative]::U32($h, $sec + 0x90)
                $fd0 = [ProbeNative]::U32($h, $sec + 0xd0); $life = [ProbeNative]::F32($h, $sec + 0xdc)
                $name = ''
                if ($idx -ge 0 -and $idx -lt 64) {
                    $nodes = [ProbeNative]::U32($h, $desc + 8)
                    $np = [ProbeNative]::U32($h, $nodes + 28 * $idx + 8)
                    if ($np -ne 0) { $name = [ProbeNative]::Ascii($h, $np, 32) }
                }
                if ($s.desc52 -notcontains $d52) { $s.desc52 = @($s.desc52) + $d52 }
                if ($s.desc2c -notcontains $d2c) { $s.desc2c = @($s.desc2c) + $d2c }
                if ($name -and ($s.node_names -notcontains $name)) { $s.node_names = @($s.node_names) + $name }
                if ($null -eq $s.life_min -or $life -lt $s.life_min) { $s.life_min = $life }
                if ($null -eq $s.life_max -or $life -gt $s.life_max) { $s.life_max = $life }
                $key = '{0:x}' -f $inst
                $sig = "{0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}" -f $d52, $f80, $idx, $f8c, $f90, $fd0, $life, $name
                if ($P.sig[$key] -ne $sig) {
                    if ($P.seenIdx.ContainsKey($key) -and $P.seenIdx[$key] -ne $idx) {
                        $s.node_idx_changes = @($s.node_idx_changes) + ("inst 0x{0} idx {1}->{2} ({3})" -f $key, $P.seenIdx[$key], $idx, $name)
                    }
                    $P.seenIdx[$key] = $idx
                    $P.sig[$key] = $sig
                    Add-ProbeLine $P 'raft' ("inst=0x{0} sec=0x{1:x} desc=0x{2:x} d52={3} d2c={4} s80=0x{5:x} idx={6} name={7} s8c=0x{8:x} s90=0x{9:x} sd0=0x{10:x} life={11}" -f $key, $sec, $desc, $d52, $d2c, $f80, $idx, $name, $f8c, $f90, $fd0, $life)
                }
            } catch { $s.read_errors++ }
        }
        if ($secOk -gt $s.sec_ok_max) { $s.sec_ok_max = $secOk }
        if (((Get-Date) - $P.lastFull).TotalSeconds -ge 1) {
            $P.lastFull = Get-Date
            Add-ProbeLine $P 'tick' ("rafts={0} sec_ok={1} bullets={2}" -f $rafts.Count, $secOk, $nb)
        }
    } catch { $s.read_errors++ }
}

function Get-RaftProbeSummary {
    param($P)
    if (-not $P) { return $null }
    return $P.summary
}

function Close-RaftProbe {
    # scrive <OutBase>.tsv e <OutBase>.json (se OutBase) e chiude l'handle; ritorna il riepilogo
    param($P)
    if (-not $P) { return $null }
    if ($P.out) {
        try {
            $utf8 = New-Object System.Text.UTF8Encoding($false)
            [IO.File]::WriteAllText($P.out + '.tsv', (($P.lines | ForEach-Object { $_ }) -join "`r`n"), $utf8)
            [IO.File]::WriteAllText($P.out + '.json', (ConvertTo-Json -InputObject $P.summary -Depth 6), $utf8)
        } catch { }
    }
    if ($P.handle -ne [IntPtr]::Zero) { [void][ProbeNative]::CloseHandle($P.handle) }
    return $P.summary
}

# ---- modo stand-alone
if ($Mode -eq 'raft') {
    $tru = Get-Process tru -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $tru) { Write-Output 'tru non in esecuzione'; return }
    $outBase = $ProbeOut
    if (-not $outBase) { $outBase = Join-Path (Get-Location).Path 'probe_raft' }
    $probe = New-RaftProbe -TruProc $tru -OutBase $outBase -IntervalMs $ProbeInterval
    $until = (Get-Date).AddSeconds($ProbeSeconds)
    while ((Get-Date) -lt $until) {
        Step-RaftProbe $probe
        Start-Sleep -Milliseconds 20
        $tru.Refresh()
        if ($tru.HasExited) { break }
    }
    $sum = Close-RaftProbe $probe
    Write-Output (ConvertTo-Json -InputObject $sum -Depth 6)
}
elseif ($Mode) {
    Write-Output ("Mode sconosciuto: {0} (supportato: raft)" -f $Mode)
}
