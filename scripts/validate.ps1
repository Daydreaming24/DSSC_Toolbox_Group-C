#Requires -Version 5.1
<#
.SYNOPSIS
  Thin Windows wrapper: select repository .venv Python and run validate.py.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Suite,

    [switch]$VerboseOutput
)

$ErrorActionPreference = 'Stop'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'

if (-not $PSScriptRoot) {
    Write-Error "PSScriptRoot is empty; run this file as a script (e.g. .\\scripts\\validate.ps1 -Suite frozen)"
    exit 1
}
$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$VenvPython = Join-Path $RepoRoot '.venv\Scripts\python.exe'
$ValidatePy = Join-Path $RepoRoot 'scripts\validate.py'

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Error "Repository .venv not found. Run .\scripts\bootstrap.ps1 first."
    exit 1
}
if (-not (Test-Path -LiteralPath $ValidatePy)) {
    Write-Error "scripts\validate.py missing"
    exit 1
}

$argList = @($ValidatePy, '--suite', $Suite, '--profile', 'host')
if ($VerboseOutput) {
    $argList += '--verbose'
}

& $VenvPython -I @argList
exit $LASTEXITCODE
