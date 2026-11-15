<#
.SYNOPSIS
    TruMenu 0.22.54: static check of every printf-style format string in TruMenu.cpp (Log / Out / LabelAdd / ...).

.DESCRIPTION
    The crash of 15.11. 19:48 was a "%s" fed with a non-pointer (kHow[] read past its end). MSVC checks the format
    strings of user functions only under /analyze and only when the format parameter carries the SAL annotation
    _Printf_format_string_ (TruMenu.cpp has it on Log, Out, LabelAdd, TextAdd, IniPut, Text, ShotNote, LxAppend,
    SndNote, ClkNote, QbResult and two lambdas since 0.22.54). The ImGui text functions (ImGui::Text, TextColored,
    SetTooltip, ...) carry IM_FMTARGS, which is empty under MSVC: this script copies imgui.h / imgui_internal.h into
    its own include folder with _Printf_format_string_ in front of their "const char* fmt" so those calls are checked
    too (the real headers stay untouched).

    Runs "cl /analyze:only" (no code) with the defines / includes of Build-TruAsi.ps1 and counts the format warnings
    (C4473 .. C4478, C6063 / C6064 / C6066 / C6067 / C6270 .. C6274 / C6302 / C6303 / C6328 / C6340) that point
    into TruMenu.cpp. Exit code 0 = none, 1 = at least one, 2 = the analysis did not run.
    Every run writes <OutDir>\Test-TruMenuFormats_<time>.log with the full compiler output.

.PARAMETER OutDir
    Work folder (patched headers, log). Default: work\fmt_1511\_out (not in the repository).

.PARAMETER VsPath
    Visual Studio folder (as Build-TruAsi.ps1).

.PARAMETER Trace
    Set-PSDebug -Trace 1 for the run.

.EXAMPLE
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File work\fmt_1511\Test-TruMenuFormats.ps1 -Verbose
#>
[CmdletBinding()]
param(
    [string]$OutDir,
    [string]$VsPath = (Join-Path $env:ProgramFiles 'Microsoft Visual Studio\2022\Community'),
    [switch]$Trace
)

$ErrorActionPreference = 'Stop'
if ($PSBoundParameters.ContainsKey('Debug')) { $DebugPreference = 'Continue' }
if ($Trace) { Set-PSDebug -Trace 1 }

$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (!$OutDir) { $OutDir = Join-Path $PSScriptRoot '_out' }
$incDir = Join-Path $OutDir 'inc'
New-Item -ItemType Directory -Force -Path $OutDir, $incDir | Out-Null
$logFile = Join-Path $OutDir ('Test-TruMenuFormats_{0}.log' -f (Get-Date -Format 'yyyyMMdd_HHmmss'))

function Write-RunLog {
    param([string]$Text, [string]$Level = 'INFO')
    $line = '{0} [{1}] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Level, $Text
    Add-Content -LiteralPath $logFile -Value $line -Encoding UTF8
    if ($Level -eq 'DEBUG') { Write-Debug $Text }
    elseif ($Level -eq 'VERBOSE') { Write-Verbose $Text }
    else { Write-Output $line }
}

try {
    $asiRoot = Join-Path $repo 'src\asi'
    $source = Join-Path $asiRoot 'TruMenu\TruMenu.cpp'
    $imgui = Join-Path $asiRoot 'third_party\imgui'
    $vcvars = Join-Path $VsPath 'VC\Auxiliary\Build\vcvarsall.bat'
    foreach ($p in $source, $imgui, $vcvars) { if (!(Test-Path -LiteralPath $p)) { throw "not found: $p" } }
    Write-RunLog "source $source, log $logFile"

    # the ImGui headers with the SAL format annotation (only the copies in $incDir)
    $patched = 0
    foreach ($name in 'imgui.h', 'imgui_internal.h') {
        $text = [IO.File]::ReadAllText((Join-Path $imgui $name))
        $rx = [regex]'(?<![_\w])const char\* fmt(?=, (\.\.\.|va_list args)\) IM_FMT(ARGS|LIST)\()'
        $count = $rx.Matches($text).Count
        $text = $rx.Replace($text, '_Printf_format_string_ const char* fmt')
        [IO.File]::WriteAllText((Join-Path $incDir $name), $text)
        $patched += $count
        Write-RunLog ('{0}: {1} format parameter(s) annotated' -f $name, $count) -Level VERBOSE
    }
    Write-RunLog "ImGui headers: $patched format parameter(s) annotated in the copies"

    $defines = @('IMGUI_IMPL_WIN32_DISABLE_GAMEPAD', 'IMGUI_DISABLE_WIN32_DEFAULT_IME_FUNCTIONS',
                 'IMGUI_DISABLE_DEFAULT_SHELL_FUNCTIONS', 'IMGUI_DISABLE_DEMO_WINDOWS') | ForEach-Object { "/D$_" }
    $includes = @($incDir, $imgui, (Join-Path $imgui 'backends')) | ForEach-Object { '/I"{0}"' -f $_ }
    $objDir = Join-Path $OutDir 'obj'
    New-Item -ItemType Directory -Force -Path $objDir | Out-Null

    # negative test first: a probe with three known mismatches (the crash pattern "%s" with an int, a missing argument,
    # an unsigned / signed mix) must give at least three format warnings, else the analysis is blind and nothing counts
    $probe = Join-Path $OutDir 'format_probe.cpp'
    $probeText = @(
        '#include <sal.h>',
        'void Log(int level, _Printf_format_string_ const char *fmt, ...);',
        'void Probe(int i, const char *s) {',
        '    Log(1, "%s", i);',
        '    Log(1, "%d %s", i);',
        '    Log(1, "%u", i - 1);',
        '    Log(1, "%s %d", s, i);',
        '}')
    [IO.File]::WriteAllLines($probe, $probeText)
    $probeCmd = 'call "{0}" amd64_x86 >nul && cl /nologo /c /analyze:only /analyze:WX- /W4 /EHsc "{1}" /Fo"{2}\\"' -f $vcvars, $probe, $objDir
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $probeOut = & cmd.exe /c $probeCmd 2>&1 | ForEach-Object { [string]$_ }
    } finally {
        $ErrorActionPreference = $previous
    }
    $probeOut | ForEach-Object { Add-Content -LiteralPath $logFile -Value ('  probe: ' + $_) -Encoding UTF8 }
    $probeHits = @($probeOut | Where-Object { $_ -match 'format_probe\.cpp\((\d+)' -and $_ -match 'warning (C447\d|C60\d\d|C627\d|C6328|C6340)' } |
                   ForEach-Object { if ($_ -match 'format_probe\.cpp\((\d+)') { $Matches[1] } } | Sort-Object -Unique)
    Write-RunLog ('negative test (probe, 3 bad lines 4 / 5 / 6, 1 good line 7): warnings on line(s) {0}' -f ($probeHits -join ', '))
    if (($probeHits -contains '4') -and ($probeHits -contains '5') -and ($probeHits -contains '6') -and !($probeHits -contains '7')) {
        Write-RunLog 'negative test ok: the analysis finds the three mismatches and not the good line'
    } else {
        Write-RunLog 'negative test FAILED: /analyze does not report the probe mismatches as expected - result not trustworthy' 'ERROR'
        exit 2
    }

    $cmd ='call "{0}" amd64_x86 >nul && cl /nologo /c /analyze:only /analyze:WX- /MT /W4 /EHsc /DNDEBUG {1} {2} "{3}" /Fo"{4}\\"' -f $vcvars, ($defines -join ' '), ($includes -join ' '), $source, $objDir
    Write-RunLog $cmd -Level DEBUG
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $out = & cmd.exe /c $cmd 2>&1 | ForEach-Object { [string]$_ }
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previous
    }
    $out | ForEach-Object { Add-Content -LiteralPath $logFile -Value ('  cl: ' + $_) -Encoding UTF8 }
    Write-RunLog "cl exit code $code, $(@($out).Count) output line(s)"
    if (@($out | Where-Object { $_ -match ' error C\d+' }).Count -gt 0) {
        $out | Where-Object { $_ -match ' error C\d+' } | Select-Object -First 10 | ForEach-Object { Write-RunLog $_ 'ERROR' }
        Write-RunLog 'the analysis did not run (compile errors)' 'ERROR'
        exit 2
    }

    $codes = 'C4473|C4474|C4475|C4476|C4477|C4478|C6063|C6064|C6066|C6067|C6270|C6271|C6272|C6273|C6274|C6302|C6303|C6328|C6340'
    $hits = @($out | Where-Object { $_ -match "TruMenu\.cpp\(\d+[,\)].*warning ($codes)" } | Sort-Object -Unique)
    $other = @($out | Where-Object { $_ -match 'warning C6\d{3}' -and $_ -notmatch "warning ($codes)" }).Count
    foreach ($h in $hits) {
        $short = $h -replace '^.*TruMenu\.cpp', 'TruMenu.cpp'
        Write-RunLog $short 'FAIL'
    }
    Write-RunLog ('format warnings in TruMenu.cpp: {0}; other /analyze warnings (not judged): {1}' -f $hits.Count, $other)
    if ($hits.Count -gt 0) { exit 1 }
    Write-RunLog 'ok: no format / argument mismatch found'
    exit 0
}
catch {
    Write-RunLog "FAILED: $($_.Exception.Message)" 'ERROR'
    exit 2
}
finally {
    if ($Trace) { Set-PSDebug -Off }
    Write-Host "Log: $logFile"
}
