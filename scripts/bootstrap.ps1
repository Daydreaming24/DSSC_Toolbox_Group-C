#Requires -Version 5.1
<#
.SYNOPSIS
  Create or refresh the repository .venv from the hash-locked requirements.

.DESCRIPTION
  Windows PowerShell 5.1 compatible. Resolves the repository root from this
  script's location (handles spaces and non-ASCII paths). Uses only
  py launcher / explicit -PythonPath to locate CPython 3.12.10, then always
  invokes .venv\Scripts\python.exe -I -m pip --isolated (never global pip.exe).
#>
[CmdletBinding()]
param(
    [string]$PythonPath = "",
    [switch]$SkipDoctor,
    [ValidateSet('host', 'host-no-docker')]
    [string]$DoctorProfile = 'host'
)

$ErrorActionPreference = 'Stop'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
$env:PYTHONNOUSERSITE = '1'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
$env:PIP_CONFIG_FILE = 'nul'
foreach ($redirectName in @('PIP_TARGET', 'PIP_PREFIX', 'PIP_ROOT', 'PIP_USER')) {
    Remove-Item -LiteralPath "Env:$redirectName" -ErrorAction SilentlyContinue
}

function Get-ExpectedPythonVersion {
    param([string]$Root)
    $versionFile = Join-Path $Root '.python-version'
    if (-not (Test-Path -LiteralPath $versionFile)) {
        throw ".python-version missing at repository root"
    }
    return ((Get-Content -LiteralPath $versionFile -Raw).Trim())
}

function Find-Python312 {
    param(
        [string]$Expected,
        [string]$ExplicitPath
    )

    if ($ExplicitPath) {
        if (-not (Test-Path -LiteralPath $ExplicitPath)) {
            throw "PythonPath not found: $ExplicitPath"
        }
        return (Resolve-Path -LiteralPath $ExplicitPath).Path
    }

    # Prefer py launcher with exact version.
    $candidates = @()
    try {
        $pyList = & py -0p 2>$null
        if ($LASTEXITCODE -eq 0 -and $pyList) {
            foreach ($line in ($pyList -split "`n")) {
                if ($line -match '3\.12') {
                    # lines look like: -V:3.12 *        C:\...\python.exe
                    if ($line -match '([A-Za-z]:\\.*python\.exe)') {
                        $candidates += $Matches[1].Trim()
                    }
                }
            }
        }
    } catch {
        # py launcher optional
    }

    try {
        $fromPy = & py -3.12 -I -S -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $fromPy) {
            $candidates += $fromPy.Trim()
        }
    } catch { }

    $candidates = $candidates | Select-Object -Unique
    foreach ($cand in $candidates) {
        if (-not (Test-Path -LiteralPath $cand)) { continue }
        $ver = & $cand -I -S -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
        if ($ver.Trim() -eq $Expected) {
            return (Resolve-Path -LiteralPath $cand).Path
        }
    }

    throw @"
Could not find CPython $Expected.
Install the official Windows x64 installer from python.org, then re-run:
  .\scripts\bootstrap.ps1
Or pass -PythonPath path\to\python.exe
"@
}

function Assert-InterpreterVersion {
    param(
        [string]$PythonExe,
        [string]$Expected
    )
    $ver = & $PythonExe -I -S -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    if ($ver.Trim() -ne $Expected) {
        throw "Interpreter version mismatch: got $($ver.Trim()), expected $Expected ($PythonExe)"
    }
    $impl = & $PythonExe -I -S -c "import platform; print(platform.python_implementation())"
    if ($impl.Trim() -ne 'CPython') {
        throw "Expected CPython, got $($impl.Trim())"
    }
    $bits = & $PythonExe -I -S -c "import struct; print(struct.calcsize('P') * 8)"
    if ($bits.Trim() -ne '64') {
        throw "Expected a 64-bit interpreter, got $($bits.Trim())-bit ($PythonExe)"
    }
}

if (-not $PSScriptRoot) {
    throw "PSScriptRoot is empty; run this file as a script"
}
$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $RepoRoot

$Expected = Get-ExpectedPythonVersion -Root $RepoRoot
Write-Host "Repository root: $RepoRoot"
Write-Host "Expected CPython: $Expected"

$BasePython = Find-Python312 -Expected $Expected -ExplicitPath $PythonPath
Write-Host "Base interpreter: $BasePython"
Assert-InterpreterVersion -PythonExe $BasePython -Expected $Expected
$EnsurePipVersion = & $BasePython -I -S -c "import ensurepip; print(ensurepip.version())"
if ($EnsurePipVersion.Trim() -ne '25.0.1') {
    throw "CPython ensurepip mismatch: got $($EnsurePipVersion.Trim()), expected 25.0.1"
}

$VenvDir = Join-Path $RepoRoot '.venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'
$VenvContract = Join-Path $RepoRoot 'scripts\dssc_validation\venv_contract.py'
$LockFile = Join-Path $RepoRoot 'requirements.lock'
$BootLock = Join-Path $RepoRoot 'requirements-bootstrap.lock'

if (-not (Test-Path -LiteralPath $LockFile)) {
    throw "requirements.lock missing; cannot bootstrap without a committed hash lock"
}
if (-not (Test-Path -LiteralPath $BootLock)) {
    throw "requirements-bootstrap.lock missing; cannot normalize pip without bootstrap tool lock"
}

$CreatedVenv = $false
if (Test-Path -LiteralPath $VenvDir) {
    $VenvItem = Get-Item -LiteralPath $VenvDir -Force
    if (-not $VenvItem.PSIsContainer -or ($VenvItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Refusing to use .venv because it is not a real, non-link directory"
    }
    if ($VenvItem.Parent.FullName -ne $RepoRoot -or $VenvItem.Name -ne '.venv') {
        throw "Refusing to use .venv outside the repository root"
    }
    if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
        throw "Existing .venv is incomplete. Follow docs/environment.md safe rebuild steps."
    }
    Write-Host "Reusing existing .venv"
} else {
    Write-Host "Creating virtual environment at .venv ..."
    & $BasePython -I -S -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { throw "venv creation failed with exit $LASTEXITCODE" }
    $CreatedVenv = $true
}

$VenvItem = Get-Item -LiteralPath $VenvDir -Force
if (-not $VenvItem.PSIsContainer -or ($VenvItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $VenvItem.Parent.FullName -ne $RepoRoot) {
    throw "Created .venv failed the repository boundary check"
}
$VenvConfig = Join-Path $VenvDir 'pyvenv.cfg'
if (-not (Test-Path -LiteralPath $VenvConfig -PathType Leaf)) {
    throw "Repository .venv is missing pyvenv.cfg"
}
$VenvConfigItem = Get-Item -LiteralPath $VenvConfig -Force
$VenvPythonItem = Get-Item -LiteralPath $VenvPython -Force
if (($VenvConfigItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -or ($VenvPythonItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw "Repository .venv configuration/interpreter must not be a reparse point on Windows"
}
$PreflightMode = if ($CreatedVenv) { 'created-preflight' } else { 'reuse-preflight' }
& $BasePython -I -S $VenvContract --mode $PreflightMode --venv $VenvDir --expected-version $Expected --expected-pip-version 25.0.1 --base-python $BasePython --bootstrap-source-file $PSCommandPath --runtime-lock-file $LockFile --bootstrap-lock-file $BootLock
if ($LASTEXITCODE -ne 0) {
    throw "Repository .venv static trust preflight failed before launching its interpreter"
}

$RuntimeContractArgs = @($VenvContract, '--venv', $VenvDir, '--expected-version', $Expected, '--expected-pip-version', '25.0.1')
if ($CreatedVenv) { $RuntimeContractArgs += '--allow-missing-marker' }
& $VenvPython -I @RuntimeContractArgs
if ($LASTEXITCODE -ne 0) {
    throw "Repository .venv isolation contract failed before package installation"
}

Assert-InterpreterVersion -PythonExe $VenvPython -Expected $Expected

# Never call global pip.exe. Always isolated python -m pip from the venv.
Write-Host "Normalizing bootstrap toolchain from requirements-bootstrap.lock ..."
& $VenvPython -I -m pip --isolated --disable-pip-version-check install --upgrade --index-url https://pypi.org/simple --require-hashes -r $BootLock
if ($LASTEXITCODE -ne 0) { throw "bootstrap tool install failed with exit $LASTEXITCODE" }

& $VenvPython -I -c "from importlib.metadata import version; expected={'pip':'25.0.1','pip-tools':'7.4.1','setuptools':'75.8.2','wheel':'0.45.1'}; bad={k:(version(k),v) for k,v in expected.items() if version(k)!=v}; print('bootstrap-tools=' + ','.join(k+'=='+version(k) for k in sorted(expected))); raise SystemExit(1 if bad else 0)"
if ($LASTEXITCODE -ne 0) { throw "bootstrap tool version verification failed" }

Write-Host "Installing runtime dependencies from requirements.lock (--require-hashes) ..."
& $VenvPython -I -m pip --isolated --disable-pip-version-check install --index-url https://pypi.org/simple --require-hashes -r $LockFile
if ($LASTEXITCODE -ne 0) { throw "runtime dependency install failed with exit $LASTEXITCODE" }

Write-Host "Running pip check ..."
& $VenvPython -I -m pip --isolated --disable-pip-version-check check
if ($LASTEXITCODE -ne 0) { throw "pip check failed with exit $LASTEXITCODE" }

$pipVer = & $VenvPython -I -m pip --isolated --version
Write-Host "pip: $pipVer"

Write-Host "Writing hash-bound .venv trust marker ..."
& $BasePython -I -S $VenvContract --mode write-marker --venv $VenvDir --expected-version $Expected --expected-pip-version 25.0.1 --base-python $BasePython --bootstrap-source-file $PSCommandPath --runtime-lock-file $LockFile --bootstrap-lock-file $BootLock
if ($LASTEXITCODE -ne 0) { throw "failed to write repository .venv trust marker" }

if (-not $SkipDoctor) {
    Write-Host "Running doctor --profile $DoctorProfile ..."
    & $VenvPython -I (Join-Path $RepoRoot 'scripts\doctor.py') --profile $DoctorProfile
    if ($LASTEXITCODE -ne 0) { throw "doctor failed with exit $LASTEXITCODE" }
}

Write-Host "Bootstrap complete."
exit 0
