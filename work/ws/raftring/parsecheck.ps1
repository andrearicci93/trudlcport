param([string]$f)
$e = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($f, [ref]$null, [ref]$e)
if ($e) { $e | Out-String } else { 'SYNTAX_OK' }
