#Requires -Version 5.1
<#
.SYNOPSIS
  Bootstrap the repository environment and run the frozen all suite.

.DESCRIPTION
  Thin Windows PowerShell 5.1-compatible orchestration wrapper. Resolves the
  repository from this script's location, delegates environment creation and
  verification to bootstrap.ps1, then delegates validation to validate.ps1.
  This command accepts no arguments.
#>
param()

$ErrorActionPreference = 'Stop'

if ($args.Count -ne 0) {
    Write-Error "Usage: .\scripts\reproduce.ps1 (no arguments)" -ErrorAction Continue
    exit 2
}

if (-not $PSScriptRoot) {
    Write-Error "PSScriptRoot is empty; run this file as a script" -ErrorAction Continue
    exit 1
}

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$Bootstrap = Join-Path $RepoRoot 'scripts\bootstrap.ps1'
$Validate = Join-Path $RepoRoot 'scripts\validate.ps1'
$WindowsPowerShell = Join-Path $PSHOME 'powershell.exe'

if (-not (Test-Path -LiteralPath $WindowsPowerShell -PathType Leaf)) {
    $WindowsPowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
}
if (-not (Test-Path -LiteralPath $WindowsPowerShell -PathType Leaf)) {
    Write-Error "Windows PowerShell 5.1 executable not found" -ErrorAction Continue
    exit 1
}

& $WindowsPowerShell -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $Bootstrap
$BootstrapExitCode = $LASTEXITCODE
if ($BootstrapExitCode -ne 0) {
    exit $BootstrapExitCode
}

& $WindowsPowerShell -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $Validate -Suite 'all'
$ValidationExitCode = $LASTEXITCODE
exit $ValidationExitCode
