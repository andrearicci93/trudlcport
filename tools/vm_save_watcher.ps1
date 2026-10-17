# vm_save_watcher.ps1 - osserva i *.TRUSave e copia ogni save nuovo/modificato in Z:\tru-port\work\saves_lib\ (M0.4, Appendice E).
# Non e' un servizio: gira per -Hours N e poi esce. Legge soltanto il gioco; scrive solo sotto Z:\tru-port\work\saves_lib.
#   powershell -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_save_watcher.ps1 -Hours 2
# Set: <yyyyMMdd_HHmmss>_<livello>_<exe8>_<baseline>\ con TUTTI i file della cartella save (non solo quello modificato).
# Baseline: C:\TRU_state\baseline.txt (scritto da vm_baseline_sync.ps1 -Mode apply). exe md5: tru.exe di gioco.
param([double]$Hours = 1, [string]$Root = 'Z:\tru-port')
$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding $false
$saveDir = "$env:USERPROFILE\Documents\Eidos\Tomb Raider - Underworld"
$game = 'C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld'
$lib = Join-Path $Root 'work\saves_lib'
$index = Join-Path $lib 'INDEX.tsv'
New-Item -ItemType Directory -Force -Path $lib | Out-Null
if (-not (Test-Path -LiteralPath $index)) {
    [IO.File]::WriteAllText($index, "time`tlivello`tbaseline`texe_md5`tfile`tmd5`r`n", $utf8)
}
if (-not (Test-Path -LiteralPath $saveDir)) { throw "INFRA: cartella save assente: $saveDir" }

function Md5File([string]$f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }

function Get-Baseline {
    $bf = 'C:\TRU_state\baseline.txt'
    if (Test-Path -LiteralPath $bf) { return (Get-Content -LiteralPath $bf -Raw).Trim() }
    return 'nobase'
}

# md5 di tru.exe ricalcolato solo se cambiano dimensione o data (vm_swap_exe.ps1 lo sostituisce)
$exeCache = @{ stamp = ''; md5 = '' }
function Get-ExeMd5 {
    $f = Join-Path $game 'tru.exe'
    $fi = Get-Item -LiteralPath $f
    $stamp = [string]$fi.Length + '|' + [string]$fi.LastWriteTimeUtc.Ticks
    if ($exeCache.stamp -ne $stamp) {
        $exeCache.md5 = Md5File $f
        $exeCache.stamp = $stamp
    }
    return $exeCache.md5
}

# Livello = prima stringa dlc_* del save (nel file, in ASCII). Nessuna stringa -> nodlc.
function Get-Level([string]$f) {
    $txt = [Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes($f))
    $m = [regex]::Match($txt, '(?i)dlc_[a-z0-9_]+')
    if ($m.Success) { return $m.Value.ToLower() }
    return 'nodlc'
}

function Copy-Retry([string]$src, [string]$dst) {
    for ($k = 0; $k -lt 5; $k++) {
        try { Copy-Item -LiteralPath $src -Destination $dst -Force; return }
        catch { Start-Sleep -Milliseconds 500 }
    }
    throw "copia fallita (file bloccato?): $src"
}

$lastMd5 = @{}
function Save-Set([string]$trigger) {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $lvl = Get-Level $trigger
    $base = Get-Baseline
    $exe = Get-ExeMd5
    $name = $stamp + '_' + $lvl + '_' + $exe.Substring(0, 8) + '_' + $base
    $dst = Join-Path $lib $name
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    $files = @(Get-ChildItem -LiteralPath $saveDir -File)
    $lines = New-Object 'System.Collections.Generic.List[string]'
    foreach ($fi in $files) {
        Copy-Retry $fi.FullName (Join-Path $dst $fi.Name)
        $m = Md5File (Join-Path $dst $fi.Name)
        $lines.Add($stamp + "`t" + $lvl + "`t" + $base + "`t" + $exe + "`t" + $fi.Name + "`t" + $m)
    }
    [IO.File]::AppendAllLines($index, $lines.ToArray(), $utf8)
    Write-Output ('SET ' + $name + ' file=' + $files.Count)
}

$w = New-Object IO.FileSystemWatcher $saveDir, '*.TRUSave'
$w.IncludeSubdirectories = $false
$w.NotifyFilter = [IO.NotifyFilters]'FileName, LastWrite, Size'
$deadline = (Get-Date).AddHours($Hours)
Write-Output ('watch ' + $saveDir + ' fino a ' + $deadline.ToString('yyyy-MM-dd HH:mm:ss'))
try {
    while ((Get-Date) -lt $deadline) {
        $r = $w.WaitForChanged([IO.WatcherChangeTypes]'Created, Changed, Renamed', 1000)
        if ($r.TimedOut) { continue }
        if ($r.Name -notlike '*.TRUSave') { continue }
        Start-Sleep -Milliseconds 1500
        $f = Join-Path $saveDir $r.Name
        if (-not (Test-Path -LiteralPath $f)) { continue }
        $m = Md5File $f
        if ($lastMd5[$r.Name] -eq $m) { continue }
        $lastMd5[$r.Name] = $m
        Save-Set $f
    }
}
finally {
    $w.Dispose()
    Write-Output 'watch fine'
}
