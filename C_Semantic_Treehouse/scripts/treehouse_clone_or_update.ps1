[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageDir = Split-Path -Parent $ScriptDir
$RootDir = Split-Path -Parent $PackageDir
$LockFile = Join-Path $RootDir "tools\semantic-treehouse\upstream.lock.json"
$EvidenceDir = Join-Path $RootDir "build\evidence\treehouse"
$EvidenceFile = Join-Path $EvidenceDir "checkout-wrapper.json"
$script:FailureCode = 1
$script:Stage = "initialize"

function Write-Utf8NoBom {
    param([string]$Path, [string]$Text)
    $Encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $Encoding)
}

function Get-Sha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Convert-ToRelativePath {
    param([string]$Path)
    $Root = [System.IO.Path]::GetFullPath($RootDir).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    $Full = [System.IO.Path]::GetFullPath($Path)
    if (-not $Full.StartsWith($Root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside the repository root: $Path"
    }
    return $Full.Substring($Root.Length).Replace('\', '/')
}

function Sanitize-Text {
    param([string]$Text)
    if ($null -eq $Text) { return "" }
    $Value = [string]$Text
    $Value = $Value.Replace($RootDir, "<repo>")
    if ($env:USERPROFILE) { $Value = $Value.Replace($env:USERPROFILE, "<user-home>") }
    $Value = [regex]::Replace(
        $Value,
        '(?i)(authorization|bearer|password|passwd|token|secret|api[_-]?key|credential)(\s*[=:]\s*)([^\s]+)',
        '$1$2<redacted>'
    )
    return $Value
}

function Write-Evidence {
    param(
        [string]$Status,
        [int]$ExitCode,
        [string]$ErrorText,
        [object]$Lock,
        [hashtable]$Observed
    )
    New-Item -ItemType Directory -Force $EvidenceDir | Out-Null
    $Payload = [ordered]@{
        schema = "dssc.semantic-treehouse.checkout-wrapper.v1"
        status = $Status
        exit_code = $ExitCode
        stage = $script:Stage
        network_scope = "exact locked reference only"
        workload_executed = $false
        upstream = if ($null -ne $Lock) { [ordered]@{
            url = $Lock.upstream.url
            reference = $Lock.upstream.reference
            expected_commit = $Lock.upstream.commit
            checkout_path = $Lock.checkout.path
        } } else { $null }
        observed = $Observed
        error = Sanitize-Text $ErrorText
    }
    Write-Utf8NoBom -Path $EvidenceFile -Text (($Payload | ConvertTo-Json -Depth 12) + "`n")
}

function Invoke-Git {
    param([string[]]$Arguments, [switch]$AllowFailure)
    $SavedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $Output = @(& git @Arguments 2>&1)
        $Code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $SavedPreference
    }
    $Text = (($Output | ForEach-Object { [string]$_ }) -join "`n").Trim()
    if (($Code -ne 0) -and (-not $AllowFailure)) {
        $script:FailureCode = if ($Code -gt 0) { $Code } else { 1 }
        throw "git $($Arguments -join ' ') failed with exit code $Code`: $(Sanitize-Text $Text)"
    }
    return [PSCustomObject]@{ ExitCode = $Code; Text = $Text }
}

function Invoke-GitBounded {
    param([string[]]$Arguments, [int]$TimeoutSeconds = 180)
    $GitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($null -eq $GitCommand) { $GitCommand = Get-Command git -ErrorAction Stop }
    $OutFile = Join-Path $EvidenceDir ".git-fetch-$PID.out.tmp"
    $ErrFile = Join-Path $EvidenceDir ".git-fetch-$PID.err.tmp"
    $Quoted = @($Arguments | ForEach-Object { '"' + ([string]$_).Replace('"', '\"') + '"' }) -join ' '
    $OldPrompt = $env:GIT_TERMINAL_PROMPT
    $env:GIT_TERMINAL_PROMPT = '0'
    try {
        $Process = Start-Process -FilePath $GitCommand.Source -ArgumentList $Quoted -NoNewWindow -PassThru -RedirectStandardOutput $OutFile -RedirectStandardError $ErrFile
        if (-not $Process.WaitForExit($TimeoutSeconds * 1000)) {
            Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
            try { $Process.WaitForExit() } catch { }
            $script:FailureCode = 124
            throw "Bounded Git operation exceeded the $TimeoutSeconds second wall-clock limit."
        }
        # Windows PowerShell 5.1 can expose an empty ExitCode after the timed
        # WaitForExit overload until the process handle is fully refreshed.
        $Process.WaitForExit()
        $Process.Refresh()
        $ExitCode = [int]$Process.ExitCode
        $Stdout = if (Test-Path -LiteralPath $OutFile) { Get-Content -LiteralPath $OutFile -Raw -Encoding UTF8 } else { "" }
        $Stderr = if (Test-Path -LiteralPath $ErrFile) { Get-Content -LiteralPath $ErrFile -Raw -Encoding UTF8 } else { "" }
        $Text = (($Stdout, $Stderr) | Where-Object { $_ }) -join "`n"
        if ($ExitCode -ne 0) {
            $script:FailureCode = if ($ExitCode -gt 0) { $ExitCode } else { 1 }
            throw "Bounded Git operation failed with exit code ${ExitCode}: $(Sanitize-Text $Text)"
        }
    } finally {
        $env:GIT_TERMINAL_PROMPT = $OldPrompt
        Remove-Item -LiteralPath $OutFile, $ErrFile -Force -ErrorAction SilentlyContinue
    }
}

function Assert-SafeRelativePath {
    param([string]$Relative, [string]$BasePath, [string]$Description)
    $Normalized = $Relative.Replace('\', '/')
    if (-not $Normalized -or $Normalized.StartsWith('/') -or $Normalized.StartsWith('-') -or $Normalized.Contains('../') -or $Normalized.Contains('/..')) {
        throw "Unsafe $Description path in lock: $Relative"
    }
    $Base = [System.IO.Path]::GetFullPath($BasePath).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    $Resolved = [System.IO.Path]::GetFullPath((Join-Path $BasePath ($Normalized -replace '/', '\')))
    if (-not $Resolved.StartsWith($Base, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "$Description path escapes the pinned upstream root: $Relative"
    }
    return $Resolved
}

function Assert-NoIgnoredBuildResidue {
    param([string]$UpstreamDir)
    foreach ($Relative in @(
        '.env', 'backend/.env.local', 'backend/.env.local.php',
        'backend/config/secrets/prod/prod.decrypt.private.php',
        'backend/vendor', 'backend/var', 'backend/user_data',
        'frontend/node_modules', 'frontend/.pnpm-store', 'frontend/.angular/cache'
    )) {
        $Path = Assert-SafeRelativePath -Relative $Relative -BasePath $UpstreamDir -Description 'residue'
        if (Test-Path -LiteralPath $Path) { throw "Ignored build residue is forbidden before materialization/deployment: $Relative" }
    }
    foreach ($Match in @(Get-ChildItem -LiteralPath (Join-Path $UpstreamDir 'backend') -Force -File -Filter '.env.*.local' -ErrorAction SilentlyContinue)) {
        throw "Ignored build residue is forbidden before materialization/deployment: backend/$($Match.Name)"
    }
}

function Assert-Lock {
    param([object]$Lock)
    if ($Lock.schema -ne "dssc.semantic-treehouse.upstream-lock.v1") { throw "Unexpected upstream lock schema." }
    if ([string]$Lock.upstream.commit -notmatch '^[0-9a-f]{40}$') { throw "Lock commit must be 40 lowercase hexadecimal characters." }
    if ([string]$Lock.upstream.reference -notmatch '^refs/tags/[^\s]+$') { throw "Lock reference must be an exact tag ref." }
    if ([bool]$Lock.checkout.follow_default_branch) { throw "Lock must prohibit following the default branch." }
    if ($Lock.checkout.mode -ne "exact-detached-commit") { throw "Unsupported checkout mode." }
    if ($Lock.source_materialization.mode -ne "bounded-sparse-fixed-commit") { throw "Unsupported source materialization mode." }
    if (@($Lock.source_materialization.required_scopes).Count -eq 0) { throw "No sparse materialization scopes are locked." }
    if (@($Lock.source_materialization.required_files).Count -eq 0) { throw "No materialized files are locked." }
    foreach ($Scope in @($Lock.source_materialization.required_scopes)) {
        $Value = ([string]$Scope).Replace('\', '/')
        if (-not $Value -or $Value.StartsWith('/') -or $Value.StartsWith('-') -or $Value.Contains('../') -or $Value.Contains('/..')) {
            throw "Unsafe sparse materialization scope: $Scope"
        }
    }
}

$Lock = $null
$Observed = @{}
try {
    $script:Stage = "read-lock"
    if (-not (Test-Path -LiteralPath $LockFile -PathType Leaf)) { throw "Missing upstream lock file." }
    $Lock = Get-Content -LiteralPath $LockFile -Raw -Encoding UTF8 | ConvertFrom-Json
    Assert-Lock $Lock
    $Observed.lock_sha256 = Get-Sha256 $LockFile

    $ExpectedCheckout = "tools/semantic-treehouse/upstream"
    if (([string]$Lock.checkout.path).Replace('\', '/') -ne $ExpectedCheckout) {
        throw "Checkout path differs from the approved fixed path."
    }
    $UpstreamDir = Join-Path $RootDir (($Lock.checkout.path -replace '/', '\'))
    $ToolsDir = Split-Path -Parent $UpstreamDir
    New-Item -ItemType Directory -Force $ToolsDir, $EvidenceDir | Out-Null

    $script:Stage = "initialize-checkout"
    $GitDir = Join-Path $UpstreamDir ".git"
    if (Test-Path -LiteralPath $UpstreamDir) {
        if (-not (Test-Path -LiteralPath $GitDir)) { throw "Refusing to overwrite a non-Git upstream path." }
        $DirtyBefore = Invoke-Git -Arguments @('-C', $UpstreamDir, 'status', '--porcelain=v1', '--untracked-files=all')
        if ($DirtyBefore.Text) { throw "Pinned upstream worktree is dirty before materialization." }
        $Origin = Invoke-Git -Arguments @('-C', $UpstreamDir, 'remote', 'get-url', 'origin')
        if ($Origin.Text.Trim() -ne [string]$Lock.upstream.url) { throw "Existing origin URL differs from the lock." }
        Assert-NoIgnoredBuildResidue -UpstreamDir $UpstreamDir
    } else {
        New-Item -ItemType Directory -Force $UpstreamDir | Out-Null
        Invoke-Git -Arguments @('-C', $UpstreamDir, 'init') | Out-Null
        Invoke-Git -Arguments @('-C', $UpstreamDir, 'remote', 'add', 'origin', [string]$Lock.upstream.url) | Out-Null
        Invoke-Git -Arguments @('-C', $UpstreamDir, 'config', 'remote.origin.promisor', 'true') | Out-Null
        Invoke-Git -Arguments @('-C', $UpstreamDir, 'config', 'remote.origin.partialclonefilter', 'blob:none') | Out-Null
    }
    Invoke-Git -Arguments @('-C', $UpstreamDir, 'config', '--local', 'core.autocrlf', 'false') | Out-Null
    $AutoCrlf = (Invoke-Git -Arguments @('-C', $UpstreamDir, 'config', '--local', '--get', 'core.autocrlf')).Text.Trim().ToLowerInvariant()
    if ($AutoCrlf -ne 'false') { throw "Pinned upstream checkout requires core.autocrlf=false." }

    $script:Stage = "materialize-locked-commit"
    $HasCommit = Invoke-Git -Arguments @('-C', $UpstreamDir, 'cat-file', '-e', "$($Lock.upstream.commit)^{commit}") -AllowFailure
    if ($HasCommit.ExitCode -ne 0) {
        Invoke-GitBounded -Arguments @(
            '-C', $UpstreamDir,
            '-c', 'http.version=HTTP/1.1',
            '-c', 'http.lowSpeedLimit=1024',
            '-c', 'http.lowSpeedTime=60',
            'fetch', '--no-tags', '--depth=1', '--filter=blob:none',
            'origin', [string]$Lock.upstream.reference
        )
        $Fetched = Invoke-Git -Arguments @('-C', $UpstreamDir, 'rev-parse', 'FETCH_HEAD^{commit}')
        if ($Fetched.Text.Trim() -ne [string]$Lock.upstream.commit) { throw "Fetched tag does not resolve to the locked commit." }
    }

    $ScopeArgs = @('-C', $UpstreamDir, 'sparse-checkout', 'set', '--cone') + @($Lock.source_materialization.required_scopes | ForEach-Object { [string]$_ })
    $BoundedScopeArgs = @('-C', $UpstreamDir, '-c', 'http.lowSpeedLimit=1024', '-c', 'http.lowSpeedTime=60', 'sparse-checkout', 'set', '--cone') + @($Lock.source_materialization.required_scopes | ForEach-Object { [string]$_ })
    Invoke-GitBounded -Arguments $BoundedScopeArgs
    Invoke-GitBounded -Arguments @('-C', $UpstreamDir, '-c', 'http.lowSpeedLimit=1024', '-c', 'http.lowSpeedTime=60', 'checkout', '--detach', [string]$Lock.upstream.commit)
    # Re-apply the bounded scopes after checkout so promisor blobs required by the build are materialized.
    Invoke-GitBounded -Arguments $BoundedScopeArgs

    $script:Stage = "verify-materialization"
    $Head = (Invoke-Git -Arguments @('-C', $UpstreamDir, 'rev-parse', 'HEAD')).Text.Trim()
    if ($Head -ne [string]$Lock.upstream.commit) { throw "Upstream HEAD differs from the lock." }
    $Branch = (Invoke-Git -Arguments @('-C', $UpstreamDir, 'symbolic-ref', '-q', '--short', 'HEAD') -AllowFailure)
    if ($Branch.ExitCode -eq 0) { throw "Upstream checkout must be detached." }
    if (Test-Path -LiteralPath (Join-Path $UpstreamDir '.env')) { throw "Refusing an upstream .env file; runtime configuration must stay isolated." }
    Assert-NoIgnoredBuildResidue -UpstreamDir $UpstreamDir

    $Hashes = [ordered]@{}
    foreach ($Relative in @($Lock.source_materialization.required_files)) {
        $Rel = ([string]$Relative).Replace('\', '/')
        if ($Rel.StartsWith('/') -or $Rel.Contains('../')) { throw "Unsafe required file path in lock: $Rel" }
        $Path = Assert-SafeRelativePath -Relative $Rel -BasePath $UpstreamDir -Description 'required file'
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required materialized file is missing: $Rel" }
        $ActualHash = Get-Sha256 $Path
        $ExpectedHash = [string]$Lock.source_materialization.sha256.$Rel
        if ($ActualHash -ne $ExpectedHash) { throw "SHA-256 mismatch for $Rel" }
        $Hashes[$Rel] = $ActualHash
    }

    $DirtyAfter = Invoke-Git -Arguments @('-C', $UpstreamDir, 'status', '--porcelain=v1', '--untracked-files=all')
    if ($DirtyAfter.Text) { throw "Pinned upstream worktree is dirty after materialization." }
    $IgnoredAfter = Invoke-Git -Arguments @('-C', $UpstreamDir, 'status', '--porcelain=v1', '--ignored=matching')
    if (@($IgnoredAfter.Text -split "`r?`n" | Where-Object { $_ -match '^!!\s+' }).Count -ne 0) {
        throw "Pinned upstream contains ignored residue after materialization."
    }
    $LicensePath = Join-Path $UpstreamDir (($Lock.license.reference_path -replace '/', '\'))
    $LicenseText = Get-Content -LiteralPath $LicensePath -Raw -Encoding UTF8
    if (($Lock.license.expected_spdx -eq 'Apache-2.0') -and ($LicenseText -notmatch 'Apache License')) {
        throw "Materialized license does not match the expected Apache-2.0 reference."
    }

    $Observed.head = $Head
    $Observed.detached = $true
    $Observed.clean_worktree = $true
    $Observed.sparse_mode = "cone"
    $Observed.core_autocrlf = "false"
    $Observed.ignored_material_absent = $true
    $Observed.forbidden_paths_absent = @(
        '.env', 'backend/.env.local', 'backend/.env.local.php', 'backend/.env.*.local',
        'backend/config/secrets/prod/prod.decrypt.private.php', 'backend/vendor', 'backend/var',
        'backend/user_data', 'frontend/node_modules', 'frontend/.pnpm-store', 'frontend/.angular/cache'
    )
    $Observed.required_scopes = @($Lock.source_materialization.required_scopes)
    $Observed.file_sha256 = $Hashes
    $Observed.upstream_env_present = $false
    Write-Evidence -Status "PASS" -ExitCode 0 -ErrorText "" -Lock $Lock -Observed $Observed
    Write-Output "Semantic Treehouse pinned checkout verified: $Head"
    exit 0
} catch {
    $Message = Sanitize-Text $_.Exception.Message
    try { Write-Evidence -Status "FAILED" -ExitCode $script:FailureCode -ErrorText $Message -Lock $Lock -Observed $Observed } catch { }
    Write-Error $Message
    exit $script:FailureCode
}
