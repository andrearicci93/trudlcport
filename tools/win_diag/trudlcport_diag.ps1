# trudlcport_diag.ps1 - diagnostica Windows del port TRU DLC (Beneath the Ashes / Lara's Shadow).
# Modi (usare DIAG.bat, che avvia il PowerShell a 32 bit come il gioco):
#   Offline      gioco chiuso: sistema, GPU/driver, backend Direct3D 9, exe, integrita' dei file installati, impostazioni, crash passati
#   Live         gioco aperto: SOLA LETTURA della memoria del gioco (fps reali, ricerca/aggancio della vena, patch in memoria,
#                moduli grafici caricati), screenshot e dump su tasto, dump automatico se il gioco crasha
#   Backend      prova A/B: sostituisce il d3d9.dll (dgVoodoo come in VM / nativo) con backup e ripristino
#   CrashDumps   attiva/disattiva i dump automatici di Windows per tru.exe (richiede amministratore)
#   Zip          ricostruisce trudlcport_diag_result.zip
# Offline e Live non modificano il gioco ne' il registro. Tutto il materiale va in .\trudlcport_diag_out e nello zip trudlcport_diag_result.zip.
param(
    [ValidateSet('Offline', 'Live', 'Backend', 'CrashDumps', 'Zip')][string]$Mode = 'Offline',
    [string]$Game = '',
    [string]$Out = '',
    [string]$Action = '',               # Backend: dgvoodoo | dgvoodoo60 | native | restore    CrashDumps: on | off
    [int]$MarkVk = 0xBB,                # tasto "+" (VK_OEM_PLUS, tastiera italiana) = marcatore; i tasti F sono usati dal ModLoader
    [int]$DumpVk = 0xBA,                # tasto "e grave" (VK_OEM_1, tastiera italiana) = dump armato (parte dopo 6 s)
    [ValidateSet('Full', 'Mini', 'None')][string]$DumpMode = 'Full',
    [int]$IdleExitSec = 20,             # Live: fine automatica N secondi dopo la chiusura del gioco
    [switch]$NoPrompt,                  # Live: nessuna domanda finale, nessuno zip (uso con LIVE.bat)
    [switch]$SkipHash,                  # Offline: confronta solo le dimensioni (veloce) invece degli MD5
    [switch]$SkipDxdiag
)
$ErrorActionPreference = 'Continue'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
if (-not $Out) { $Out = Join-Path $Here 'trudlcport_diag_out' }
try { New-Item -ItemType Directory -Force $Out | Out-Null; $probe = Join-Path $Out '.w'; [IO.File]::WriteAllText($probe, 'x'); Remove-Item $probe -Force }
catch { $Out = Join-Path ([Environment]::GetFolderPath('Desktop')) 'trudlcport_diag_out'; New-Item -ItemType Directory -Force $Out | Out-Null }
$ZipPath = Join-Path (Split-Path -Parent $Out) 'trudlcport_diag_result.zip'
$script:Rep = Join-Path $Out ('REPORT_{0}_{1}.txt' -f $Mode.ToLower(), $Stamp)
$script:Find = New-Object System.Collections.Generic.List[string]
$script:Facts = New-Object System.Collections.Generic.List[string]
$Utf8 = New-Object System.Text.UTF8Encoding($true)

function W([string]$s = '') { Write-Host $s; try { [IO.File]::AppendAllText($script:Rep, $s + "`r`n", $Utf8) } catch { } }
function Hdr([string]$t) { W ''; W ('=== ' + $t + ' ==='); }
function Flag([string]$sev, [string]$msg) { $script:Find.Add(('[{0}] {1}' -f $sev, $msg)); W ('  >>> [{0}] {1}' -f $sev, $msg) }
function Fact([string]$s) { $script:Facts.Add($s) }
function Sec([string]$name, [scriptblock]$sb) { Hdr $name; try { & $sb } catch { W ('  ERRORE nella sezione: ' + $_.Exception.Message + '  [riga ' + $_.InvocationInfo.ScriptLineNumber + ']') } }
function Md5Of([string]$p) {
    $m = [Security.Cryptography.MD5]::Create()
    $fs = New-Object IO.FileStream($p, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite, 1048576)
    try { ([BitConverter]::ToString($m.ComputeHash($fs))).Replace('-', '').ToLower() } finally { $fs.Close(); $m.Dispose() }
}
function RegVal($path, $name) { try { (Get-ItemProperty -Path $path -Name $name -ErrorAction Stop).$name } catch { $null } }

# ---------------------------------------------------------------- cartella del gioco
function Find-Game {
    if ($Game -and (Test-Path (Join-Path $Game 'tru.exe'))) { return $Game.TrimEnd('\') }
    if (Test-Path (Join-Path $Here 'tru.exe')) { return $Here }
    $cands = New-Object System.Collections.Generic.List[string]
    try { $p = Get-Process tru -ErrorAction SilentlyContinue | Select-Object -First 1; if ($p -and $p.Path) { $cands.Add((Split-Path -Parent $p.Path)) } } catch { }
    $steam = @()
    foreach ($k in 'HKCU:\Software\Valve\Steam', 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam', 'HKLM:\SOFTWARE\Valve\Steam') {
        foreach ($n in 'SteamPath', 'InstallPath') { $v = RegVal $k $n; if ($v) { $steam += ($v -replace '/', '\') } }
    }
    foreach ($s in ($steam | Select-Object -Unique)) {
        $cands.Add((Join-Path $s 'steamapps\common\Tomb Raider Underworld'))
        $vdf = Join-Path $s 'steamapps\libraryfolders.vdf'
        if (Test-Path $vdf) { foreach ($m in [regex]::Matches((Get-Content $vdf -Raw), '"path"\s+"([^"]+)"')) { $cands.Add((Join-Path ($m.Groups[1].Value -replace '\\\\', '\') 'steamapps\common\Tomb Raider Underworld')) } }
    }
    $cands.Add('C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld')
    foreach ($c in $cands) { if ($c -and (Test-Path (Join-Path $c 'tru.exe'))) { return $c } }
    return $null
}

# ---------------------------------------------------------------- PE
function Read-Pe([string]$p) {
    $b = [IO.File]::ReadAllBytes($p)
    $pe = [BitConverter]::ToInt32($b, 0x3c); $n = [BitConverter]::ToUInt16($b, $pe + 6); $opt = [BitConverter]::ToUInt16($b, $pe + 20)
    $base = [BitConverter]::ToUInt32($b, $pe + 24 + 28); $so = $pe + 24 + $opt; $secs = @()
    for ($i = 0; $i -lt $n; $i++) {
        $o = $so + 40 * $i
        $secs += [pscustomobject]@{ Name = ([Text.Encoding]::ASCII.GetString($b, $o, 8)).TrimEnd([char]0); Va = [BitConverter]::ToUInt32($b, $o + 12) + $base; Vs = [BitConverter]::ToUInt32($b, $o + 8); Raw = [BitConverter]::ToUInt32($b, $o + 20); Rs = [BitConverter]::ToUInt32($b, $o + 16) }
    }
    [pscustomobject]@{ Bytes = $b; Base = $base; Secs = $secs }
}
function Pe-Bytes($pe, [uint32]$va, [int]$n) {
    foreach ($s in $pe.Secs) { if ($va -ge $s.Va -and $va -lt ($s.Va + [Math]::Max($s.Vs, $s.Rs))) { $o = [int]($s.Raw + $va - $s.Va); if ($o + $n -le $pe.Bytes.Length) { return $pe.Bytes[$o..($o + $n - 1)] } } }
    return $null
}
function Hex($a) { if ($a -eq $null) { return $null } ([BitConverter]::ToString([byte[]]$a)).Replace('-', '').ToLower() }

# exe noti: md5 -> descrizione
$KnownExe = @{
    '2b7ee74c37394be208195efd0952cd5f' = 'exe PATCHATO del port (release B269/B270: wall-run, FX ombra, guardie)'
    'b36da327a320eab8b5c8464b27685840' = 'exe ORIGINALE Steam v1.1 (impacchettato): il port NON e'' attivo'
    '56d1ce2dffa62f16354063da2df44d5a' = 'exe originale unpacked con Steamless (non ancora patchato)'
}
# firme attese nell'exe di release (VA, byte attesi, descrizione)
$ExeMarkers = @(
    @{ Va = 0x441fb0; Hex = 'e94beedf00'; Name = 'hook @0x441fb0 (guardia native-script 0)' },
    @{ Va = 0x1240f80; Hex = '8d83a7fdffff83f8070f85012053ff'; Name = 'cave attach vena (caso 608) @0x1240f80' }
)

# ================================================================ OFFLINE
function Do-Offline {
    W ('trudlcport_diag OFFLINE  ' + (Get-Date -Format 's') + '  host=' + $env:COMPUTERNAME + '  utente=' + $env:USERNAME)
    W ('PowerShell ' + $PSVersionTable.PSVersion + ' a ' + ([IntPtr]::Size * 8) + ' bit')

    Sec 'SISTEMA E GPU' {
        $os = Get-CimInstance Win32_OperatingSystem; $cs = Get-CimInstance Win32_ComputerSystem
        W ('Windows: {0} build {1} {2}' -f $os.Caption, $os.BuildNumber, $os.OSArchitecture)
        W ('PC: {0} {1}   RAM {2:N1} GB' -f $cs.Manufacturer, $cs.Model, ($cs.TotalPhysicalMemory / 1GB))
        foreach ($c in (Get-CimInstance Win32_Processor)) { W ('CPU: {0}  ({1} core, {2} thread)' -f $c.Name.Trim(), $c.NumberOfCores, $c.NumberOfLogicalProcessors) }
        $gpus = @(Get-CimInstance Win32_VideoController)
        foreach ($g in $gpus) {
            W ('GPU: {0}  driver {1} ({2})  VRAM(WMI, max 4 GB) {3:N1} GB  {4}x{5} @ {6} Hz  stato {7}' -f $g.Name, $g.DriverVersion, ($(if ($g.DriverDate) { $g.DriverDate.ToString('yyyy-MM-dd') } else { '?' })), ($g.AdapterRAM / 1GB), $g.CurrentHorizontalResolution, $g.CurrentVerticalResolution, $g.CurrentRefreshRate, $g.Status)
            Fact ('GPU ' + $g.Name + ' drv ' + $g.DriverVersion)
            if ($g.CurrentRefreshRate -gt 62) { Flag 'i' ('Schermo a {0} Hz: senza blocco a 60 fps il gioco gira fino a {0} fps (fisica e wall-run si rompono sopra 60).' -f $g.CurrentRefreshRate) }
        }
        if ($gpus.Count -gt 1) { Flag 'i' ('Piu'' GPU presenti ({0}): verifica quale usa tru.exe (Impostazioni > Schermo > Grafica).' -f ($gpus | ForEach-Object { $_.Name } | Out-String).Trim().Replace("`r`n", ' / ')) }
        $hags = RegVal 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers' 'HwSchMode'
        W ('Pianificazione GPU con accelerazione hardware (HAGS): ' + $(if ($hags -eq 2) { 'ATTIVA' } elseif ($hags -eq 1) { 'disattiva' } else { 'n/d' }))
        $gm = RegVal 'HKCU:\Software\Microsoft\GameBar' 'AutoGameModeEnabled'; W ('Modalita'' Gioco: ' + $(if ($gm -eq 1) { 'attiva' } elseif ($gm -eq 0) { 'disattiva' } else { 'n/d' }))
        try { W ('Piano energetico: ' + ((powercfg /getactivescheme) -join ' ')) } catch { }
        $dxv = RegVal 'HKLM:\SOFTWARE\Microsoft\DirectX' 'Version'; W ('DirectX (registro): ' + $dxv)
        foreach ($e in (Get-ChildItem Env: | Where-Object { $_.Name -match '^(DXVK|__GL|MESA|D3D|WINE)' })) { W ('Variabile ambiente: {0}={1}' -f $e.Name, $e.Value); Flag 'i' ('Variabile d''ambiente grafica ' + $e.Name) }
        # monitor
        try { Add-Type -AssemblyName System.Windows.Forms; foreach ($s in [Windows.Forms.Screen]::AllScreens) { W ('Monitor: {0}  {1}x{2}{3}' -f $s.DeviceName, $s.Bounds.Width, $s.Bounds.Height, $(if ($s.Primary) { ' (principale)' } else { '' })) } } catch { }
    }

    Sec 'PROCESSI CHE INFLUISCONO SUGLI FPS / OVERLAY' {
        $names = 'RTSS', 'RTSSHooksLoader64', 'RTSSHooksLoader', 'MSIAfterburner', 'GameOverlayUI', 'steamwebhelper', 'Discord', 'obs64', 'obs32', 'nvcontainer', 'NVIDIA Overlay', 'NVIDIA Share', 'RadeonSoftware', 'AMDRSServ', 'cncmd', 'LosslessScaling', 'SpecialK64', 'SpecialK32', 'GeForceNOW', 'Lightshot', 'Overwolf', 'tru'
        $ps = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $names -contains $_.ProcessName })
        if ($ps.Count -eq 0) { W 'nessuno dei processi noti e'' in esecuzione' }
        foreach ($p in $ps) { W ('  {0} (pid {1})' -f $p.ProcessName, $p.Id) }
        if ($ps | Where-Object { $_.ProcessName -eq 'tru' }) { Flag 'i' 'tru.exe e'' in esecuzione: per un check offline completo chiudi il gioco.' }
        if ($ps | Where-Object { $_.ProcessName -match 'RTSS|Afterburner' }) { W '  (RTSS/Afterburner presenti: possono limitare gli fps, o iniettare overlay nel gioco)' }
    }

    $g = Find-Game
    if (-not $g) { Hdr 'CARTELLA DEL GIOCO'; Flag '!' 'Cartella del gioco non trovata: rilancia indicandola (DIAG.bat chiede il percorso).'; return }
    $exe = Join-Path $g 'tru.exe'

    Sec 'GIOCO: CARTELLA, EXE, BACKEND DIRECT3D 9' {
        W ('Cartella: ' + $g)
        $fi = Get-Item $exe
        $em = Md5Of $exe
        W ('tru.exe: {0} byte, MD5 {1}, modificato {2}' -f $fi.Length, $em, $fi.LastWriteTime.ToString('s'))
        Fact ('tru.exe md5 ' + $em)
        if ($KnownExe.ContainsKey($em)) { W ('  riconosciuto: ' + $KnownExe[$em]) }
        if ($em -eq '2b7ee74c37394be208195efd0952cd5f') { W '  OK: e'' l''exe patchato della release.' }
        elseif ($em -eq 'b36da327a320eab8b5c8464b27685840' -or $em -eq '56d1ce2dffa62f16354063da2df44d5a') { Flag '!' 'tru.exe e'' quello ORIGINALE, non quello patchato del port: wall-run e fix non possono funzionare. Cause: installer lanciato con --no-exe, oppure Steam ha verificato/riscaricato il gioco. RIMEDIO: DIAG.bat > 3 (applica solo la patch dell''exe).' }
        else { Flag '!' ('tru.exe ha un MD5 sconosciuto (' + $em + '): non e'' l''exe della release B270.') }
        try {
            $pe = Read-Pe $exe
            W ('Sezioni PE: ' + (($pe.Secs | ForEach-Object { $_.Name }) -join ' '))
            $has = @($pe.Secs | ForEach-Object { $_.Name })
            foreach ($need in '.tuload', '.tuext', '.tufx', '.tufin') { if ($has -notcontains $need) { Flag '!' ('Manca la sezione ' + $need + ' dell''exe del port.') } }
            foreach ($mk in $ExeMarkers) {
                $got = Hex (Pe-Bytes $pe ([uint32]$mk.Va) ($mk.Hex.Length / 2))
                if ($got -eq $mk.Hex) { W ('  firma OK   : ' + $mk.Name) } else { W ('  firma ASSENTE: ' + $mk.Name + '  (trovato ' + $got + ')'); if ($em -eq '2b7ee74c37394be208195efd0952cd5f') { Flag '!' ('Firma ' + $mk.Name + ' non corrisponde pur con MD5 atteso: lettura PE da verificare.') } }
            }
        } catch { W ('  PE non leggibile: ' + $_.Exception.Message) }
        foreach ($n in 'tru.exe.steam_original', 'tru.exe.unpacked.exe', 'trudlcport_install.json') { $q = Join-Path $g $n; if (Test-Path $q) { $f = Get-Item $q; W ('  presente: {0} ({1} byte, {2})' -f $n, $f.Length, $f.LastWriteTime.ToString('s')) } else { W ('  assente : ' + $n) } }
        $up = Join-Path $g 'tru.exe.unpacked.exe'
        if (Test-Path $up) { $um = Md5Of $up; W ('  tru.exe.unpacked.exe MD5 ' + $um); if ($um -ne '56d1ce2dffa62f16354063da2df44d5a') { Flag 'i' 'tru.exe.unpacked.exe ha MD5 diverso dall''atteso (56d1ce2d...): Steamless eseguito senza --realign. Il fix (DIAG.bat > 3) lo rifa da solo.' } }

        Hdr 'File nella cartella del gioco che possono sostituire/alterare Direct3D 9'
        $watch = 'd3d9.dll', 'd3d8.dll', 'd3d11.dll', 'd3d12.dll', 'dxgi.dll', 'ddraw.dll', 'dinput.dll', 'dinput8.dll', 'winmm.dll', 'version.dll', 'dsound.dll', 'opengl32.dll', 'xinput1_3.dll', 'xinput9_1_0.dll', 'binkw32.dll', 'ModLoader.asi', 'dgVoodoo.conf', 'dxvk.conf', 'dxwrapper.ini', 'dxwrapper.dll', 'ReShade.ini', 'ReShade32.dll', 'SpecialK32.dll'
        $wrapper = 'nessuno: il gioco usa il Direct3D 9 di Windows (nativo)'
        foreach ($n in $watch) {
            $q = Join-Path $g $n
            if (Test-Path $q) {
                $f = Get-Item $q; $vi = $f.VersionInfo
                W ('  {0,-18} {1,9} byte  {2}  ver {3}  [{4} | {5}]' -f $n, $f.Length, $f.LastWriteTime.ToString('yyyy-MM-dd'), $vi.FileVersion, $vi.ProductName, $vi.FileDescription)
                if ($n -eq 'd3d9.dll') {
                    $d = ($vi.ProductName + ' ' + $vi.FileDescription + ' ' + $vi.CompanyName)
                    if ($d -match 'DXVK') { $wrapper = 'DXVK (' + $vi.FileVersion + ')' } elseif ($d -match 'dgVoodoo') { $wrapper = 'dgVoodoo2 (' + $vi.FileVersion + ')' } elseif ($d -match 'dxwrapper') { $wrapper = 'dxwrapper' } else { $wrapper = 'd3d9.dll SCONOSCIUTO nella cartella del gioco: ' + $d }
                }
            }
        }
        W ('=> BACKEND D3D9 in uso (dalla cartella): ' + $wrapper)
        Fact ('backend d3d9: ' + $wrapper)
        if ($wrapper -like 'nessuno*') { Flag 'i' 'Backend = Direct3D 9 NATIVO di Windows. In VM si usava dgVoodoo2 (-> D3D11): differenze di shader/texture/costanti tra i due sono la causa piu'' probabile dei difetti solo-grafici (pantaloni). Prova A/B con DIAG.bat > 4.' }
        elseif ($wrapper -like 'dgVoodoo*') { Flag 'i' 'Backend = dgVoodoo2 (come in VM).' }
        foreach ($cf in 'dgVoodoo.conf', 'dxvk.conf') { $q = Join-Path $g $cf; if (Test-Path $q) { W ('--- ' + $cf + ' (righe attive rilevanti)'); Get-Content $q | Where-Object { $_ -match '^\s*(OutputAPI|FPSLimit|FullScreenMode|ScalingMode|Adapters|DesktopResolution|dxvk\.|d3d9\.)' } | ForEach-Object { W ('    ' + $_.Trim()) } } }
        $asi = @(Get-ChildItem $g -Filter *.asi -ErrorAction SilentlyContinue); foreach ($a in $asi) { W ('  ASI: ' + $a.Name) }
        if (-not (Test-Path (Join-Path $g 'ModLoader.asi')) -or -not (Test-Path (Join-Path $g 'binkw32.dll'))) { Flag '!' 'ModLoader.asi o binkw32.dll mancanti nella cartella del gioco: le mod/DLC potrebbero non essere caricate.' }
        $cr = Get-ChildItem (Join-Path $g 'movies') -Filter 'credits_DLC*.bik' -ErrorAction SilentlyContinue; W ('Filmati credits: ' + $(if ($cr) { ($cr | ForEach-Object { $_.Name }) -join ', ' } else { 'nessuno' }))

        # Steam
        $acf = $null; $sa = Split-Path -Parent (Split-Path -Parent $g)
        $cand = Join-Path $sa 'appmanifest_8140.acf'; if (Test-Path $cand) { $acf = $cand }
        if ($acf) {
            $t = Get-Content $acf -Raw; W '--- Steam appmanifest_8140.acf'
            foreach ($k in 'buildid', 'LastUpdated', 'StateFlags', 'AutoUpdateBehavior', 'BetaKey', 'SizeOnDisk', 'LastOwner') { $m = [regex]::Match($t, '"' + $k + '"\s+"([^"]*)"'); if ($m.Success) { $v = $m.Groups[1].Value; if ($k -eq 'LastUpdated') { try { $v = $v + ' = ' + ([DateTimeOffset]::FromUnixTimeSeconds([long]$v).LocalDateTime.ToString('s')) } catch { } }; W ('    {0} = {1}' -f $k, $v) } }
            $m = [regex]::Match($t, '"LastUpdated"\s+"(\d+)"')
            if ($m.Success) { try { $lu = [DateTimeOffset]::FromUnixTimeSeconds([long]$m.Groups[1].Value).LocalDateTime; if ($lu -gt $fi.LastWriteTime.AddMinutes(1) -and $em -ne '2b7ee74c37394be208195efd0952cd5f') { Flag 'i' ('Steam ha aggiornato/verificato il gioco il ' + $lu.ToString('s') + ' (dopo la data di tru.exe): se l''exe e'' tornato originale puo'' essere stato lui.') } } catch { } }
        }
    }

    Sec 'INSTALLAZIONE DEL PORT: INTEGRITA'' DEI FILE (mods\)' {
        $mods = Join-Path $g 'mods'
        if (-not (Test-Path $mods)) { Flag '!' 'Manca la cartella mods\ nel gioco.'; return }
        $recP = Join-Path $g 'trudlcport_install.json'; $rec = $null
        if (Test-Path $recP) { try { $rec = Get-Content $recP -Raw | ConvertFrom-Json } catch { W ('  registro installazione illeggibile: ' + $_.Exception.Message) } }
        $exp = @{}; $expSize = @{}; $expDlc = @{}
        $tsv = Join-Path $Here 'expected_B270_acqua.tsv'
        if (Test-Path $tsv) { foreach ($l in (Get-Content $tsv)) { if ($l.StartsWith('#') -or -not $l.Trim()) { continue }; $f = $l.Split("`t"); $exp[$f[0].ToLower()] = $f[1]; $expSize[$f[0].ToLower()] = [long]$f[2]; $expDlc[$f[0].ToLower()] = $f[3] } }
        W ('Riferimento incorporato: B270_acqua, ' + $exp.Count + ' file')
        $recFiles = @{}
        if ($rec) {
            W ('Registro installazione: build {0}, data {1}, {2} file, backup mods: {3}, backup exe: {4}' -f $rec.build, $rec.time, @($rec.files.PSObject.Properties).Count, $rec.mods_backup, $rec.exe_backup)
            Fact ('install build ' + $rec.build)
            foreach ($p in $rec.files.PSObject.Properties) { $recFiles[$p.Name.ToLower()] = $p.Value }
            if ($rec.build -ne 'B270_acqua') { Flag 'i' ('Build installata = ' + $rec.build + ' (il riferimento incorporato e'' B270_acqua: i confronti col riferimento valgono solo per i file uguali).') }
        } else { Flag '!' 'Nessun registro trudlcport_install.json: installazione non fatta con install_dlc.py, o cartella sbagliata.' }
        # confronto registro <-> riferimento
        if ($rec -and $exp.Count) {
            $diff = 0; $miss = 0; foreach ($k in $exp.Keys) { if (-not $recFiles.ContainsKey($k)) { $miss++ } elseif ($recFiles[$k] -ne $exp[$k]) { $diff++ } }
            W ('Registro vs riferimento B270_acqua: {0} file con MD5 diverso, {1} mancanti nel registro' -f $diff, $miss)
            if ($diff -gt 0 -or $miss -gt 0) { Flag '!' ('L''installazione NON e'' la build B270_acqua di riferimento (' + $diff + ' diversi, ' + $miss + ' mancanti): i dati non sono quelli provati in VM.') }
        }
        $ref = if ($recFiles.Count) { $recFiles } else { $exp }
        $refName = if ($recFiles.Count) { 'registro' } else { 'riferimento B270' }
        $bad = New-Object System.Collections.Generic.List[string]; $okc = 0; $i = 0; $tot = $ref.Count
        $t0 = Get-Date
        foreach ($k in ($ref.Keys | Sort-Object)) {
            $i++
            $p = Join-Path $mods ($k -replace '/', '\')
            if (-not (Test-Path $p)) { $bad.Add('mancante: ' + $k); continue }
            if ($SkipHash) { $sz = (Get-Item $p).Length; if ($expSize.ContainsKey($k) -and $sz -ne $expSize[$k]) { $bad.Add('dimensione diversa: ' + $k) } else { $okc++ } }
            else { if ((Md5Of $p) -ne $ref[$k]) { $bad.Add('modificato: ' + $k) } else { $okc++ } }
            if ($i % 40 -eq 0) { Write-Host ('  controllo file {0}/{1} ...' -f $i, $tot) }
        }
        W ('Verifica vs {0}: {1} OK, {2} problemi su {3} file ({4:N0} s){5}' -f $refName, $okc, $bad.Count, $tot, ((Get-Date) - $t0).TotalSeconds, $(if ($SkipHash) { '  [solo dimensioni]' } else { '' }))
        Fact ('file mods ok ' + $okc + '/' + $tot + ' problemi ' + $bad.Count)
        $bad | Select-Object -First 60 | ForEach-Object { W ('   ' + $_) }
        if ($bad.Count -gt 60) { W ('   ... altri ' + ($bad.Count - 60)) }
        if ($bad.Count -gt 0) { Flag '!' ('Installazione danneggiata/diversa: ' + $bad.Count + ' file. Rilancia install_dlc.py (--verify, poi reinstalla).') } else { W '  Tutti i file installati coincidono: i DATI sono quelli di riferimento.'; Flag 'i' 'Dati installati identici al riferimento: i difetti NON vengono dai file, ma da exe/ambiente/backend grafico/fps.' }
        # file extra in mods\
        $extra = @(Get-ChildItem $mods -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName.Substring($mods.Length + 1).Replace('\', '/').ToLower() } | Where-Object { -not $ref.ContainsKey($_) })
        W ('File in mods\ che NON fanno parte dell''installazione: ' + $extra.Count)
        $extra | Select-Object -First 25 | ForEach-Object { W ('   + ' + $_) }
        if ($extra.Count -gt 0) { Flag 'i' ('Ci sono ' + $extra.Count + ' file extra in mods\ (altre mod?): possono cambiare il comportamento.') }
        # file dei costumi / doppelganger (pantaloni) e del wall-run
        W '--- file chiave (costume doppelganger, giocatore):'
        foreach ($n in 'dlc_doppel_costume_a.drm', 'lara_doppelganger.drm', 'doppelganger.drm', 'doppelganger_casual.drm', 'dlc2_costumes.drm', 'dlc2_costumes_map.drm', 'player_tru_dlc2_extension.drm', 'co_dlc_lara.drm', 'dlc_dispatcher.drm') {
            $p = Join-Path $mods $n
            if (Test-Path $p) { $h = if ($SkipHash) { '(non calcolato)' } else { Md5Of $p }; $st = if ($exp.ContainsKey($n) -and -not $SkipHash) { if ($exp[$n] -eq $h) { 'ok' } else { 'DIVERSO dal riferimento' } } else { '' }; W ('   {0,-34} {1}  {2}' -f $n, $h, $st) } else { W ('   {0,-34} ASSENTE' -f $n) }
        }
        $bk = @(Get-ChildItem $g -Directory -Filter 'mods_backup_*' -ErrorAction SilentlyContinue); if ($bk.Count) { W ('Cartelle di backup mods precedenti: ' + (($bk | ForEach-Object { $_.Name }) -join ', ')) }
    }

    Sec 'IMPOSTAZIONI DEL GIOCO (registro) E SALVATAGGI' {
        foreach ($k in 'HKCU:\Software\Crystal Dynamics', 'HKCU:\Software\Eidos', 'HKLM:\SOFTWARE\WOW6432Node\Crystal Dynamics', 'HKLM:\SOFTWARE\WOW6432Node\Eidos') {
            if (Test-Path $k) {
                W ($k)
                Get-ChildItem $k -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
                    W ('  ' + $_.Name)
                    try { (Get-ItemProperty $_.PSPath).PSObject.Properties | Where-Object { $_.Name -notmatch '^PS' } | ForEach-Object { $v = $_.Value; if ($v -is [byte[]]) { $v = 'bin(' + $v.Length + ')' }; W ('     {0} = {1}' -f $_.Name, $v) } } catch { }
                }
            }
        }
        $vs = $null; foreach ($k in 'HKCU:\Software\Crystal Dynamics\Tomb Raider: Underworld', 'HKCU:\Software\Eidos\Tomb Raider: Underworld') { if (Test-Path $k) { Get-ChildItem $k -Recurse -ErrorAction SilentlyContinue | ForEach-Object { try { $p = Get-ItemProperty $_.PSPath; if ($p.PSObject.Properties.Name -contains 'EnableVSync') { $vs = $p.EnableVSync } } catch { } } } }
        if ($vs -ne $null) { W ('EnableVSync = ' + $vs); if ($vs -eq 0) { Flag 'i' 'EnableVSync=0 nel registro del gioco: nessun blocco degli fps dal gioco.' } }
        $ud = Join-Path (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $g))) 'userdata'
        if (Test-Path $ud) { Get-ChildItem $ud -Directory | ForEach-Object { $r = Join-Path $_.FullName '8140\remote'; if (Test-Path $r) { W ('Salvataggi Steam cloud ' + $r); Get-ChildItem $r -File -ErrorAction SilentlyContinue | Select-Object -First 30 | ForEach-Object { W ('   {0} {1} byte {2}' -f $_.Name, $_.Length, $_.LastWriteTime.ToString('s')) } } } }
        if (Test-Path $ud) { $shots = @(Get-ChildItem (Join-Path $ud '*\760\remote\8140\screenshots') -File -Filter *.jpg -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 4); foreach ($sh in $shots) { try { Copy-Item $sh.FullName (Join-Path $Out ('steam_shot_' + $sh.Name)) -Force; W ('Screenshot Steam copiato: ' + $sh.Name) } catch { } } }
        $per = RegVal 'HKCU:\Software\Microsoft\DirectX\UserGpuPreferences' $exe; if ($per) { W ('Preferenza GPU per tru.exe: ' + $per) }
        foreach ($lk in 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers', 'HKLM:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers') { $v = RegVal $lk $exe; if ($v) { W ('Compatibilita'' per tru.exe (' + $lk.Substring(0, 4) + '): ' + $v); Flag 'i' ('Modalita'' di compatibilita'' impostata su tru.exe: ' + $v) } }
    }

    Sec 'CRASH E ERRORI RECENTI (ultimi 30 giorni)' {
        $since = (Get-Date).AddDays(-30)
        try {
            $ev = @(Get-WinEvent -FilterHashtable @{ LogName = 'Application'; StartTime = $since; Id = 1000, 1001, 1002 } -ErrorAction SilentlyContinue | Where-Object { ($_.Id -ne 1001 -and $_.Properties.Count -gt 0 -and [string]$_.Properties[0].Value -match 'tru\.exe') -or ($_.Id -eq 1001 -and $_.Message -match 'tru\.exe|LiveKernelEvent') })
            W ('Eventi Application Error/WER per tru.exe: ' + $ev.Count)
            $grp = @{}
            foreach ($e in $ev) {
                if ($e.Id -eq 1000 -and $e.Properties.Count -ge 8) {
                    # indici standard dell'evento 1000 (indipendenti dalla lingua): 3 modulo, 6 codice eccezione, 7 offset
                    $key = ('{0} | {1} | offset {2}' -f $e.Properties[3].Value, $e.Properties[6].Value, $e.Properties[7].Value)
                    if ($grp.ContainsKey($key)) { $grp[$key]++ } else { $grp[$key] = 1 }
                }
            }
            foreach ($k in $grp.Keys) { W ('   {0}x  {1}' -f $grp[$k], $k) }
            if ($grp.Count) { Flag '!' ('Crash di tru.exe registrati da Windows: ' + (($grp.Keys | ForEach-Object { $_ }) -join ' ;; ')) }
            $ev | Select-Object -First 8 | ForEach-Object { W ('--- {0} id {1}' -f $_.TimeCreated.ToString('s'), $_.Id); W (($_.Message -split "`r?`n" | Select-Object -First 14) -join "`r`n") }
        } catch { W ('  lettura Application non riuscita: ' + $_.Exception.Message) }
        try {
            $gev = @()
            foreach ($pn in 'Display', 'nvlddmkm', 'amdkmdag', 'amdwddmg', 'igfx', 'Microsoft-Windows-WHEA-Logger') {
                try { $gev += @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; StartTime = $since; ProviderName = $pn } -MaxEvents 15 -ErrorAction Stop) } catch { }
            }
            $gev = @($gev | Sort-Object TimeCreated -Descending | Select-Object -First 25)
            W ('Eventi di sistema legati alla GPU (TDR/reset driver): ' + $gev.Count)
            foreach ($e in $gev) { W ('   {0}  {1} id {2}: {3}' -f $e.TimeCreated.ToString('s'), $e.ProviderName, $e.Id, (($e.Message -split "`r?`n")[0])) }
            if (@($gev | Where-Object { $_.ProviderName -match 'Display|nvlddmkm|amdkmdag|igfx' }).Count) { Flag '!' 'Il driver video e'' stato resettato (TDR) di recente: rimanda anche il test Direct3D 9 nativo (opzione 3).' }
        } catch { W ('  lettura System non riuscita: ' + $_.Exception.Message) }
        $dd = @(); foreach ($d in 'C:\TRU_dumps', 'C:\TRU_dumps\wer', (Join-Path $env:LOCALAPPDATA 'CrashDumps'), (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\WER\ReportArchive')) { if (Test-Path $d) { $dd += Get-ChildItem $d -Recurse -File -Include '*.dmp', '*.wer' -ErrorAction SilentlyContinue } }
        $dd = @($dd | Where-Object { $_.Name -match 'tru' -or $_.DirectoryName -match 'TRU_dumps|tru' } | Sort-Object LastWriteTime -Descending)
        W ('Dump/report di crash di tru.exe trovati: ' + $dd.Count)
        $dd | Select-Object -First 10 | ForEach-Object { W ('   {0}  {1:N0} MB  {2}' -f $_.LastWriteTime.ToString('s'), ($_.Length / 1MB), $_.FullName) }
        $copied = 0
        foreach ($d in ($dd | Where-Object { $_.Extension -eq '.dmp' -and $_.Length -lt 400MB } | Select-Object -First 2)) { try { Copy-Item $d.FullName (Join-Path $Out ('crash_' + $d.Name)) -Force; $copied++ } catch { } }
        if ($copied) { W ('   (copiati nella cartella di output: ' + $copied + ')') }
        $ld = RegVal 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\tru.exe' 'DumpFolder'; W ('Dump automatici di Windows per tru.exe: ' + $(if ($ld) { 'ATTIVI in ' + $ld } else { 'non attivi (DIAG.bat > 5 per attivarli)' }))
        $log = Get-ChildItem $g -Recurse -Include 'engine.log', 'ErrorHandler*.txt', '*.log' -ErrorAction SilentlyContinue | Where-Object { $_.Length -lt 20MB } | Select-Object -First 8
        foreach ($l in $log) { W ('log nel gioco: ' + $l.FullName + ' ' + $l.Length); try { Copy-Item $l.FullName (Join-Path $Out ('gamelog_' + $l.Name)) -Force } catch { } }
    }

    if (-not $SkipDxdiag) {
        Sec 'DXDIAG (Direct3D, driver, livelli di funzionalita'')' {
            $f = Join-Path $Out 'dxdiag.txt'; Remove-Item $f -ErrorAction SilentlyContinue
            try {
                $p = Start-Process dxdiag -ArgumentList '/whql:off', '/t', ('"' + $f + '"') -PassThru
                if (-not $p.WaitForExit(120000)) { try { Stop-Process -Id $p.Id -ErrorAction SilentlyContinue } catch { } }
            } catch { W ('  dxdiag non riuscito: ' + $_.Exception.Message) }
            if (Test-Path $f) {
                $t = Get-Content $f
                $t | Where-Object { $_ -match 'DirectX Version|Card name:|Chip type:|Driver Version:|Driver Date|DDI Version|Feature Levels|Driver Model|Display Memory|Current Mode|Monitor Name|Native Mode|Hardware-Accelerated|DxDiag Version|Not Found|Problem Code|ProblemCode' } | Select-Object -First 40 | ForEach-Object { W ('  ' + $_.Trim()) }
                W '  (dxdiag.txt completo nella cartella di output)'
            } else { W '  dxdiag.txt non creato' }
        }
    }
}

# ================================================================ BACKEND A/B
function Do-Backend {
    $g = Find-Game; if (-not $g) { W 'Cartella del gioco non trovata.'; return }
    $state = Join-Path $g 'trudlcport_backend_swap.json'
    $src = Join-Path $Here 'backends\dgvoodoo_vm'
    function SaveState($s) { $s | ConvertTo-Json | Set-Content $state -Encoding UTF8 }
    if ($Action -eq 'restore') {
        if (-not (Test-Path $state)) { W 'Nessuna sostituzione da ripristinare.'; return }
        $s = Get-Content $state -Raw | ConvertFrom-Json
        foreach ($f in @($s.copied)) { $p = Join-Path $g $f; if (Test-Path $p) { Remove-Item $p -Force; W ('rimosso ' + $f) } }
        foreach ($f in @($s.backed)) { $b = Join-Path $g ($f + '.diag_bak'); if (Test-Path $b) { Move-Item $b (Join-Path $g $f) -Force; W ('ripristinato ' + $f) } }
        Remove-Item $state -Force; W 'Backend ripristinato com''era prima.'; return
    }
    if (Test-Path $state) { W 'Una sostituzione e'' gia'' attiva: prima scegli "ripristina".'; return }
    $copied = @(); $backed = @()
    foreach ($f in 'd3d9.dll', 'dgVoodoo.conf') { $p = Join-Path $g $f; if (Test-Path $p) { Move-Item $p ($p + '.diag_bak') -Force; $backed += $f; W ('backup: ' + $f + ' -> ' + $f + '.diag_bak') } }
    if ($Action -eq 'native') { W 'Rimosso d3d9.dll dalla cartella (se c''era): il gioco usera'' il Direct3D 9 NATIVO di Windows.' }
    elseif ($Action -eq 'dgvoodoo' -or $Action -eq 'dgvoodoo60') {
        $conf = if ($Action -eq 'dgvoodoo60') { 'dgVoodoo_60fps.conf' } else { 'dgVoodoo.conf' }
        Copy-Item (Join-Path $src 'D3D9.dll') (Join-Path $g 'd3d9.dll') -Force; $copied += 'd3d9.dll'
        Copy-Item (Join-Path $src $conf) (Join-Path $g 'dgVoodoo.conf') -Force; $copied += 'dgVoodoo.conf'
        W ('Installato dgVoodoo2 (D3D9.dll + ' + $conf + ', stessa coppia della VM' + $(if ($Action -eq 'dgvoodoo60') { ', FPSLimit 60' } else { ', FPSLimit 0' }) + ').')
    } else { W 'Azione sconosciuta.'; return }
    SaveState @{ action = $Action; time = (Get-Date -Format 's'); copied = $copied; backed = $backed }
    W 'Ora avvia il gioco da Steam e riprova (pantaloni / wall-run). Per tornare indietro: opzione "ripristina".'
}

function Do-CrashDumps {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent(); $adm = (New-Object Security.Principal.WindowsPrincipal($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $adm) { W 'Servono i diritti di amministratore: riavvio con richiesta di elevazione...'; Start-Process powershell.exe -Verb RunAs -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "' + $MyInvocation.ScriptName + '" -Mode CrashDumps -Action ' + $Action) ; return }
    $k = 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\tru.exe'
    if ($Action -eq 'off') { Remove-Item $k -Force -ErrorAction SilentlyContinue; W 'Dump automatici disattivati.'; return }
    New-Item -ItemType Directory -Force 'C:\TRU_dumps\wer' | Out-Null
    New-Item -Path $k -Force | Out-Null
    New-ItemProperty $k -Name DumpFolder -Value 'C:\TRU_dumps\wer' -PropertyType ExpandString -Force | Out-Null
    New-ItemProperty $k -Name DumpCount -Value 3 -PropertyType DWord -Force | Out-Null
    New-ItemProperty $k -Name DumpType -Value 2 -PropertyType DWord -Force | Out-Null
    W 'Dump automatici ATTIVI per tru.exe in C:\TRU_dumps\wer (completi, max 3, anche file da 1-3 GB). Se il gioco crasha, il dump si crea da solo. Disattiva con DIAG.bat > 5 > off.'
}

# ================================================================ LIVE
function Do-Live {
    W ('trudlcport_diag LIVE  ' + (Get-Date -Format 's') + '  PowerShell a ' + ([IntPtr]::Size * 8) + ' bit')
    if ([IntPtr]::Size -ne 4) { W 'ATTENZIONE: PowerShell a 64 bit: i dump del gioco (32 bit) avranno contesti thread inutilizzabili. Usa DIAG.bat (avvia SysWOW64).' }
    $cs = Join-Path $Here 'TruLive.cs'
    if (-not (Test-Path $cs)) { W 'TruLive.cs mancante.'; return }
    try { Add-Type -Path $cs -ReferencedAssemblies 'System.Core', 'System.Drawing', 'System.Windows.Forms' -IgnoreWarnings -ErrorAction Stop }
    catch { W ('Compilazione di TruLive.cs non riuscita (antivirus/policy?): ' + $_.Exception.Message); W 'Se Defender ha bloccato lo script: vedi LEGGIMI.txt, sezione "Antivirus".'; return }
    $stop = Join-Path $Out 'STOP.txt'; Remove-Item $stop -ErrorAction SilentlyContinue
    W ''
    W 'ISTRUZIONI: 1) avvia il gioco da Steam (DLC2 per il wall-run). 2) Gioca normalmente.'
    W '  tasto +  = MARCATORE: premilo UNA volta poco prima della prova (wall-run, ledge...); poi per 20 s il campionamento e'' fitto.'
    W '  tasto e-grave = DUMP ARMATO: dopo 6 s (beep) scatta screenshot + dump completo (il gioco si blocca 10-60 s): usalo UNA volta sul difetto.'
    W '  Fine: chiudi il gioco (lo strumento chiude da solo dopo 20 s) oppure Ctrl+C in questa finestra.'
    W ''
    $sum = ''
    try { $sum = [TruLive]::Run($Out, $Stamp, $MarkVk, $DumpVk, $DumpMode, $stop, $IdleExitSec) }
    finally {
        if ($sum) { W ''; W $sum }
        # comprimi i dump (separati dallo zip principale)
        try { Add-Type -AssemblyName System.IO.Compression.FileSystem } catch { }
        foreach ($d in (Get-ChildItem $Out -Filter *.dmp -ErrorAction SilentlyContinue)) {
            $z = $d.FullName + '.zip'
            if (-not (Test-Path $z)) { try { Write-Host ('  comprimo ' + $d.Name + ' ...'); $za = [IO.Compression.ZipFile]::Open($z, 'Create'); [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($za, $d.FullName, $d.Name, 'Optimal'); $za.Dispose() } catch { W ('  compressione non riuscita: ' + $_.Exception.Message) } }
        }
        if (-not $NoPrompt) {
            try {
                $n = Read-Host 'Note libere (cosa hai visto, dove, quando; invio per saltare)'
                if ($n) { [IO.File]::WriteAllText((Join-Path $Out ('NOTE_' + $Stamp + '.txt')), $n, $Utf8) }
            } catch { }
            try { Do-Zip } catch { }     # anche dopo Ctrl+C (il blocco finally viene eseguito)
        }
    }
}

# ================================================================ ZIP
function Do-Zip {
    try { Add-Type -AssemblyName System.IO.Compression.FileSystem } catch { }
    if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
    $za = [IO.Compression.ZipFile]::Open($ZipPath, 'Create'); $n = 0
    foreach ($f in (Get-ChildItem $Out -Recurse -File)) {
        if ($f.Length -gt 300MB) { continue }
        $rel = $f.FullName.Substring($Out.Length).TrimStart('\')
        try { [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($za, $f.FullName, $rel, 'Optimal'); $n++ } catch { }
    }
    $za.Dispose()
    $big = @(Get-ChildItem $Out -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Length -gt 300MB -and $_.Extension -ne '.dmp' } )
    if (-not $big.Count) { $big = @(Get-ChildItem $Out -Recurse -File -Filter *.dmp -ErrorAction SilentlyContinue | Where-Object { $_.Length -gt 300MB }) }
    Write-Host ''
    Write-Host ('Zip pronto: {0}  ({1} file, {2:N1} MB)' -f $ZipPath, $n, ((Get-Item $ZipPath).Length / 1MB))
    foreach ($b in $big) { Write-Host ('Dump da inviare A PARTE (troppo grande per lo zip): {0}  ({1:N0} MB)' -f $b.FullName, ($b.Length / 1MB)) }
}

# ================================================================ main
try {
    switch ($Mode) {
        'Offline' {
            Do-Offline
            Hdr 'SINTESI'
            if ($script:Facts.Count) { $script:Facts | ForEach-Object { W ('  - ' + $_) } }
            if ($script:Find.Count) { W ''; $script:Find | ForEach-Object { W ('  ' + $_) } } else { W '  nessun riscontro particolare.' }
            $sin = Join-Path $Out ('SINTESI_offline_' + $Stamp + '.txt'); Copy-Item $script:Rep $sin -Force
            Do-Zip
        }
        'Live' { Do-Live }
        'Backend' { Do-Backend }
        'CrashDumps' { Do-CrashDumps }
        'Zip' { Do-Zip }
    }
} catch { Write-Host ('ERRORE: ' + $_.Exception.Message); Write-Host $_.ScriptStackTrace; try { Do-Zip } catch { } }

