[CmdletBinding()]
param(
    [int]$HttpPort = 0,
    [switch]$PrepareOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageDir = Split-Path -Parent $ScriptDir
$RootDir = Split-Path -Parent $PackageDir
$LockPath = Join-Path $RootDir "tools\semantic-treehouse\upstream.lock.json"
$RuntimeDir = Join-Path $RootDir "build\phase-08\treehouse-runtime"
$EvidenceDir = Join-Path $RootDir "build\evidence\treehouse"
$EnvPath = Join-Path $RuntimeDir "synthetic.env"
$OverlayPath = Join-Path $RuntimeDir "compose.runtime.yml"
$InlineDockerfilePath = Join-Path $RuntimeDir "Dockerfile.runtime"
$RawLogPath = Join-Path $RuntimeDir $(if ($PrepareOnly) { "up.prepare-only.raw.log" } else { "up.raw.log" })
$RawLogEvidencePath = if ($PrepareOnly) { "build/phase-08/treehouse-runtime/up.prepare-only.raw.log" } else { "build/phase-08/treehouse-runtime/up.raw.log" }
$BoundaryPath = Join-Path $RuntimeDir "runtime-boundary.json"
$BoundaryEvidencePath = Join-Path $EvidenceDir "runtime-boundary.json"
$PrepareBoundaryEvidencePath = Join-Path $EvidenceDir "runtime-boundary-prepare-only.json"
$ResultEvidencePath = Join-Path $EvidenceDir $(if ($PrepareOnly) { "runtime-up-prepare-only.json" } else { "runtime-up.json" })
$NetworkOptionsEvidencePath = Join-Path $EvidenceDir "runtime-network-options.json"
$StatePath = Join-Path $RuntimeDir "runtime-state.json"
$PendingStatePath = Join-Path $RuntimeDir ".runtime-state.pending.json"
$script:FirstError = $null
$script:ComposeReady = $false
$script:UpAttempted = $false
$script:FreshDeploymentStarted = $false
$script:CreatedVolumes = New-Object System.Collections.Generic.List[string]
$script:ValidatedEnvMap = $null
$script:SecurityControllerPatchProjection = $null
$script:LastFailureStep = $null
$script:LastNativeExitCode = $null
$script:CleanupSummary = [ordered]@{
    attempted = $false
    compose_down_exit_code = $null
    volume_remove_failures = @()
    verification_error = $null
    remaining_project_containers = $null
    remaining_named_containers = $null
    remaining_project_networks = $null
    remaining_named_networks = $null
    remaining_project_volumes = $null
    remaining_named_volumes = $null
    complete = $null
}

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) {
        throw $Message
    }
}

function Get-Sha256 {
    param([string]$Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Get-TextSha256 {
    param([string]$Text)
    if ($null -eq $Text) { $Text = "" }
    $Hasher = [System.Security.Cryptography.SHA256]::Create()
    try {
        $Bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        return (($Hasher.ComputeHash($Bytes) | ForEach-Object { $_.ToString('x2') }) -join '')
    } finally {
        $Hasher.Dispose()
    }
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Text)
    $Parent = Split-Path -Parent $Path
    if (($Parent.Length -gt 0) -and (-not (Test-Path -LiteralPath $Parent -PathType Container))) {
        New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Text, (New-Object System.Text.UTF8Encoding($false)))
}

function Write-JsonFile {
    param([string]$Path, $Value)
    $Parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $Parent -PathType Container)) {
        New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    }
    $Json = $Value | ConvertTo-Json -Depth 30
    Write-Utf8NoBom $Path ($Json + "`n")
}

function Add-RawLog {
    param([string]$Step, [string]$Text)
    $Header = "`r`n===== $Step =====`r`n"
    $SafeText = ConvertTo-SafeRuntimeText $Text
    [System.IO.File]::AppendAllText($RawLogPath, ($Header + $SafeText + "`n"), (New-Object System.Text.UTF8Encoding($false)))
}

function Record-FirstError {
    param([string]$Step, [string]$Message, [int]$ExitCode = 1)
    $SafeMessage = ConvertTo-SafeRuntimeText $Message
    if ($null -eq $script:FirstError) {
        $script:FirstError = [ordered]@{
            step = $Step
            message = $SafeMessage
            exit_code = $ExitCode
        }
    }
    Add-RawLog $Step $Message
}

function ConvertTo-SafeEvidenceText {
    param([string]$Text)
    if ($null -eq $Text) { return "" }
    $Safe = $Text
    foreach ($SensitivePath in @($RootDir, $RuntimeDir, $env:USERPROFILE, $env:HOME)) {
        if (($null -ne $SensitivePath) -and ([string]$SensitivePath).Length -gt 0) {
            $Safe = $Safe.Replace([string]$SensitivePath, "<redacted-path>")
        }
    }
    foreach ($UserName in @($env:USERNAME, $env:USER)) {
        if (($null -ne $UserName) -and ([string]$UserName).Length -ge 3) {
            $Safe = $Safe.Replace([string]$UserName, "<redacted-user>")
        }
    }
    $Safe = [regex]::Replace($Safe, '(?i)[A-Z]:\\Users\\[^\\\s"'']+', '<redacted-home>')
    $Safe = [regex]::Replace($Safe, '(?i)/(?:home/[^/\s"'']+|root)(?:/[^\s"'']*)?', '<redacted-home>')
    return $Safe
}

function ConvertTo-SafeRuntimeText {
    param([string]$Text)
    $Safe = ConvertTo-SafeEvidenceText $Text
    if ($null -eq $Safe) { $Safe = "" }
    if ($null -ne $script:ValidatedEnvMap) {
        foreach ($Key in @("APP_SECRET", "DB2_PASSWORD", "DB2_ROOT_PASSWORD", "DB2_TEST_DB_PASSWORD")) {
            if ($script:ValidatedEnvMap.ContainsKey($Key)) {
                $Value = [string]$script:ValidatedEnvMap[$Key]
                if (($Value.Length -gt 0) -and $Safe.Contains($Value)) { $Safe = $Safe.Replace($Value, "<redacted-secret>") }
            }
        }
    }
    return [regex]::Replace($Safe, '(?im)^(APP_SECRET|DB2_PASSWORD|DB2_ROOT_PASSWORD|DB2_TEST_DB_PASSWORD|STH_AI_GATEWAY_DEFAULT_API_KEY)=.*$', '$1=<redacted-secret>')
}

function Assert-EvidenceSanitized {
    param([string]$Path, $EnvMap)
    $Text = Get-Content -Raw -Encoding UTF8 -LiteralPath $Path
    foreach ($Key in @("APP_SECRET", "DB2_PASSWORD", "DB2_ROOT_PASSWORD", "DB2_TEST_DB_PASSWORD")) {
        if (($null -ne $EnvMap) -and $EnvMap.ContainsKey($Key)) {
            $Value = [string]$EnvMap[$Key]
            Assert-True (($Value.Length -eq 0) -or (-not $Text.Contains($Value))) "Scrubbed evidence contains a synthetic secret value."
        }
    }
    foreach ($SensitivePath in @($RootDir, $RuntimeDir, $env:USERPROFILE, $env:HOME)) {
        if (($null -ne $SensitivePath) -and ([string]$SensitivePath).Length -gt 0) {
            Assert-True (-not $Text.Contains([string]$SensitivePath)) "Scrubbed evidence contains an absolute repository or home path."
        }
    }
    foreach ($UserName in @($env:USERNAME, $env:USER)) {
        if (($null -ne $UserName) -and ([string]$UserName).Length -ge 3) {
            Assert-True (-not $Text.Contains([string]$UserName)) "Scrubbed evidence contains the local username."
        }
    }
    Assert-True (-not [regex]::IsMatch($Text, '(?m)^(?:APP_SECRET|DB2_PASSWORD|DB2_ROOT_PASSWORD|DB2_TEST_DB_PASSWORD|STH_AI_GATEWAY_DEFAULT_API_KEY)=')) "Scrubbed evidence contains an env assignment."
    Assert-True (-not [regex]::IsMatch($Text, '(?i)[A-Z]:\\Users\\|/(?:home/[^/\s"'']+|root)(?:/|\b)')) "Scrubbed evidence contains a home/root absolute path."
}

function Invoke-NativeCapture {
    param([string]$File, [string[]]$Arguments, [string]$Step, [switch]$AllowFailure, [switch]$NoLog)
    $PreviousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $Lines = & $File @Arguments 2>&1
        $Code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $PreviousPreference
    }
    $Text = (($Lines | ForEach-Object { $_.ToString() }) -join "`n").Trim()
    if (-not $NoLog) { Add-RawLog $Step $Text }
    if (($Code -ne 0) -and (-not $AllowFailure)) {
        throw "$Step failed with exit code $Code."
    }
    return [PSCustomObject]@{ ExitCode = $Code; Text = $Text }
}

function ConvertTo-CommandLineArgument {
    param([string]$Value)
    if ($Value.Length -eq 0) { return '""' }
    if ($Value -notmatch '[\s"]') { return $Value }
    return '"' + ($Value.Replace('\', '\').Replace('"', '\"')) + '"'
}

function Invoke-SensitiveNativeCapture {
    param(
        [string]$File,
        [string[]]$Arguments,
        [string]$Step,
        [int]$TimeoutSeconds = 90
    )
    $Info = New-Object System.Diagnostics.ProcessStartInfo
    $Info.FileName = $File
    $Info.Arguments = (($Arguments | ForEach-Object { ConvertTo-CommandLineArgument $_ }) -join ' ')
    $Info.UseShellExecute = $false
    $Info.CreateNoWindow = $true
    $Info.RedirectStandardOutput = $true
    $Info.RedirectStandardError = $true
    $Process = New-Object System.Diagnostics.Process
    $Process.StartInfo = $Info
    Assert-True ($Process.Start()) "$Step could not start."
    try {
        $StdoutTask = $Process.StandardOutput.ReadToEndAsync()
        $StderrTask = $Process.StandardError.ReadToEndAsync()
        $TimedOut = -not $Process.WaitForExit($TimeoutSeconds * 1000)
        if ($TimedOut) {
            try { $Process.Kill() } catch { }
            $Process.WaitForExit()
        } else {
            $Process.WaitForExit()
        }
        $Process.Refresh()
        $NativeExitCode = [int]$Process.ExitCode
        $Stdout = $StdoutTask.Result
        $Stderr = $StderrTask.Result
        if ($Stderr.Length -gt 0) { Add-RawLog ($Step + "-stderr-safe") $Stderr }
        if ($TimedOut) { throw "$Step timed out after $TimeoutSeconds seconds." }
        if ($NativeExitCode -ne 0) { throw "$Step failed with exit code $NativeExitCode." }
        return [PSCustomObject]@{ ExitCode = $NativeExitCode; Text = $Stdout; Stderr = $Stderr }
    } finally {
        $Process.Dispose()
    }
}

function Invoke-SensitiveNativeWithStdin {
    param(
        [string]$File,
        [string[]]$Arguments,
        [string]$InputText,
        [string]$Step,
        [int]$TimeoutSeconds = 90
    )
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $Info = New-Object System.Diagnostics.ProcessStartInfo
    $Info.FileName = $File
    $Info.Arguments = (($Arguments | ForEach-Object { ConvertTo-CommandLineArgument $_ }) -join ' ')
    $Info.UseShellExecute = $false
    $Info.CreateNoWindow = $true
    $Info.RedirectStandardInput = $true
    $Info.RedirectStandardOutput = $true
    $Info.RedirectStandardError = $true
    $Process = New-Object System.Diagnostics.Process
    $Process.StartInfo = $Info
    Assert-True ($Process.Start()) "$Step could not start."
    try {
        $StdoutTask = $Process.StandardOutput.ReadToEndAsync()
        $StderrTask = $Process.StandardError.ReadToEndAsync()
        $InputBytes = $Utf8NoBom.GetBytes($InputText)
        $Process.StandardInput.BaseStream.Write($InputBytes, 0, $InputBytes.Length)
        $Process.StandardInput.BaseStream.Flush()
        $Process.StandardInput.Close()
        $TimedOut = -not $Process.WaitForExit($TimeoutSeconds * 1000)
        if ($TimedOut) {
            try { $Process.Kill() } catch { }
            $Process.WaitForExit()
        } else {
            $Process.WaitForExit()
        }
        $Process.Refresh()
        $NativeExitCode = [int]$Process.ExitCode
        $Stdout = $StdoutTask.Result
        $Stderr = $StderrTask.Result
        if ($Stderr.Length -gt 0) { Add-RawLog ($Step + "-stderr-safe") $Stderr }
        if ($TimedOut) { throw "$Step timed out after $TimeoutSeconds seconds." }
        if ($NativeExitCode -ne 0) { throw "$Step failed with exit code $NativeExitCode." }
        return [PSCustomObject]@{ ExitCode = $NativeExitCode; Text = $Stdout; Stderr = $Stderr }
    } finally {
        $Process.Dispose()
    }
}

function Invoke-BoundedNative {
    param(
        [string]$File,
        [string[]]$Arguments,
        [string]$Step,
        [int]$TimeoutSeconds,
        [switch]$AllowFailure
    )
    $SafeStep = ($Step -replace '[^A-Za-z0-9_.-]', '_')
    $OutPath = Join-Path $RuntimeDir ($SafeStep + ".stdout.raw.log")
    $ErrPath = Join-Path $RuntimeDir ($SafeStep + ".stderr.raw.log")
    $Info = New-Object System.Diagnostics.ProcessStartInfo
    $Info.FileName = $File
    $Info.Arguments = (($Arguments | ForEach-Object { ConvertTo-CommandLineArgument $_ }) -join ' ')
    $Info.UseShellExecute = $false
    $Info.CreateNoWindow = $true
    $Info.RedirectStandardOutput = $true
    $Info.RedirectStandardError = $true
    $Process = New-Object System.Diagnostics.Process
    $Process.StartInfo = $Info
    $TimedOut = $false
    $Stdout = ""
    $Stderr = ""
    $RawExitCode = $null
    try {
        Assert-True ($Process.Start()) "$Step could not start."
        $StdoutTask = $Process.StandardOutput.ReadToEndAsync()
        $StderrTask = $Process.StandardError.ReadToEndAsync()
        $TimedOut = -not $Process.WaitForExit($TimeoutSeconds * 1000)
        if ($TimedOut) {
            try { $Process.Kill() } catch { }
            Assert-True ($Process.WaitForExit(10000)) "$Step did not terminate after its timeout."
        }
        $Process.WaitForExit()
        $Process.Refresh()
        $RawExitCode = $Process.ExitCode
        Assert-True ($null -ne $RawExitCode) "$Step completed without a readable native exit code."
        $Stdout = [string]$StdoutTask.Result
        $Stderr = [string]$StderrTask.Result
    } catch {
        if ([string]::IsNullOrWhiteSpace([string]$script:LastFailureStep)) { $script:LastFailureStep = $Step }
        if ($null -eq $script:LastNativeExitCode) { $script:LastNativeExitCode = if ($TimedOut) { 124 } else { 1 } }
        throw
    } finally {
        $Process.Dispose()
    }

    $SafeStdout = ConvertTo-SafeRuntimeText $Stdout
    $SafeStderr = ConvertTo-SafeRuntimeText $Stderr
    Write-Utf8NoBom $OutPath $SafeStdout
    Write-Utf8NoBom $ErrPath $SafeStderr
    Add-RawLog $Step ((($SafeStdout, $SafeStderr) | Where-Object { $_ }) -join "`n")
    $Code = if ($TimedOut) { 124 } else { [int]$RawExitCode }
    $Combined = (($Stdout, $Stderr) | Where-Object { $null -ne $_ }) -join "`n"
    $TransportPattern = '(?im)(failed to solve|unexpected EOF|short read|^#\d+\s+ERROR\b)'
    $TransportMatch = [regex]::Match($Combined, $TransportPattern)
    if ($TransportMatch.Success) {
        $DiagnosticLine = @([regex]::Split($Combined, '\r\n|\n|\r') | Where-Object { $_ -match $TransportPattern } | Select-Object -First 1)
        $Diagnostic = if ($DiagnosticLine.Count -gt 0) { ConvertTo-SafeRuntimeText $DiagnosticLine[0] } else { ConvertTo-SafeRuntimeText $TransportMatch.Value }
        $script:LastFailureStep = $Step
        $script:LastNativeExitCode = $Code
        throw "$Step transport/build failure (native exit $Code): $Diagnostic"
    }
    if (($Code -ne 0) -and (-not $AllowFailure)) {
        $DiagnosticLine = @([regex]::Split($Stderr, '\r\n|\n|\r') | Where-Object { $_ -match '(?i)(error|failed|fatal)' } | Select-Object -First 1)
        if ($DiagnosticLine.Count -eq 0) { $DiagnosticLine = @([regex]::Split($Stderr, '\r\n|\n|\r') | Where-Object { $_.Trim().Length -gt 0 } | Select-Object -First 1) }
        $Diagnostic = if ($DiagnosticLine.Count -gt 0) { ": " + (ConvertTo-SafeRuntimeText $DiagnosticLine[0]) } else { "" }
        $script:LastFailureStep = $Step
        $script:LastNativeExitCode = $Code
        if ($TimedOut) { throw "$Step timed out after $TimeoutSeconds seconds.$Diagnostic" }
        throw "$Step failed with native exit code $Code$Diagnostic"
    }
    return [PSCustomObject]@{ ExitCode = $Code; TimedOut = $TimedOut; Stdout = $SafeStdout; Stderr = $SafeStderr }
}

function Resolve-ChildPath {
    param([string]$Parent, [string]$Relative, [string]$Description)
    Assert-True (-not [System.IO.Path]::IsPathRooted($Relative)) "$Description must be relative."
    Assert-True ($Relative -notmatch '(^|[\\/])\.\.([\\/]|$)') "$Description must not contain parent traversal."
    $ParentFull = [System.IO.Path]::GetFullPath($Parent).TrimEnd('\', '/')
    $Candidate = [System.IO.Path]::GetFullPath((Join-Path $Parent $Relative))
    Assert-True ($Candidate.StartsWith($ParentFull + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) "$Description escapes its approved parent."
    return $Candidate
}

function Get-LockContext {
    Assert-True (Test-Path -LiteralPath $LockPath -PathType Leaf) "The upstream lock is missing."
    $Lock = Get-Content -Raw -Encoding UTF8 -LiteralPath $LockPath | ConvertFrom-Json
    Assert-True ($Lock.schema -eq "dssc.semantic-treehouse.upstream-lock.v1") "Unexpected upstream lock schema."
    $Commit = [string]$Lock.upstream.commit
    Assert-True ($Commit -cmatch '^[0-9a-f]{40}$') "The lock commit must be 40 lowercase hexadecimal characters."
    $ProjectName = [string]$Lock.compose.project_name
    Assert-True ($ProjectName -cmatch '^[a-z0-9][a-z0-9_-]+$') "The locked Compose project name is invalid."
    Assert-True ([string]$Lock.runtime.target_service -ceq "sth") "The locked target service must be sth."
    $Dependencies = @($Lock.runtime.dependency_services | ForEach-Object { [string]$_ })
    Assert-True (($Dependencies.Count -eq 1) -and ($Dependencies[0] -ceq "sth-db2")) "The locked dependency closure must name only sth-db2."
    Assert-True ([string]$Lock.runtime.bind_address -ceq "127.0.0.1") "The runtime bind address must be loopback."
    Assert-True ([string]$Lock.runtime.network_topology -ceq "dual-network-app-ingress") "The runtime network topology must be dual-network-app-ingress."
    Assert-True ([bool]$Lock.runtime.internal_network) "The runtime network must be internal."
    Assert-True ([bool]$Lock.runtime.app_outbound_access) "The application ingress network must explicitly authorize outbound access."
    Assert-True ($Lock.runtime.PSObject.Properties.Name -contains "ingress_network_internal") "The ingress network internal flag must be explicit."
    Assert-True (-not [bool]$Lock.runtime.ingress_network_internal) "The ingress network must be an ordinary non-internal bridge."
    $IngressServices = @($Lock.runtime.ingress_services | ForEach-Object { [string]$_ })
    Assert-True (($IngressServices.Count -eq 1) -and ($IngressServices[0] -ceq "sth")) "Only sth may attach to the ingress network."
    $ExpectedNetworkOptions = Get-ExpectedRuntimeNetworkOptions $Lock
    $InternalNetworkName = [string]$Lock.runtime.network_name
    $IngressNetworkName = [string]$Lock.runtime.ingress_network_name
    Assert-True (($InternalNetworkName -cmatch '^[a-z0-9][a-z0-9_-]+$') -and ($IngressNetworkName -cmatch '^[a-z0-9][a-z0-9_-]+$')) "Locked runtime network names are invalid."
    Assert-True ($InternalNetworkName -cne $IngressNetworkName) "Internal and ingress network names must differ."
    Assert-True ([bool]$Lock.runtime.project_scoped_volumes) "Runtime volumes must be project scoped."
    $LockedPort = [int]$Lock.runtime.default_http_port
    $SelectedPort = if ($HttpPort -eq 0) { $LockedPort } else { $HttpPort }
    Assert-True (($SelectedPort -ge 1024) -and ($SelectedPort -le 65535)) "HttpPort must be between 1024 and 65535."
    $UpstreamDir = Resolve-ChildPath $RootDir ([string]$Lock.checkout.path) "checkout.path"
    Assert-True (Test-Path -LiteralPath $UpstreamDir -PathType Container) "The locked upstream checkout is absent."
    $ComposePath = Resolve-ChildPath $UpstreamDir ([string]$Lock.compose.path) "compose.path"
    Assert-True (Test-Path -LiteralPath $ComposePath -PathType Leaf) "The locked Compose file is absent."
    $ImageMap = @{}
    foreach ($Image in @($Lock.images)) {
        $Reference = [string]$Image.reference
        $Digest = [string]$Image.linux_amd64_digest
        Assert-True ($Digest -cmatch '^sha256:[0-9a-f]{64}$') "Invalid linux/amd64 digest for $Reference."
        $ImageMap[$Reference] = $Digest
    }
    foreach ($RequiredImage in @("node:22", "composer:2", "dunglas/frankenphp:php8.4", "mariadb:11.4")) {
        Assert-True $ImageMap.ContainsKey($RequiredImage) "The lock is missing $RequiredImage."
    }
    return [PSCustomObject]@{
        Lock = $Lock
        Commit = $Commit
        ProjectName = $ProjectName
        HttpPort = $SelectedPort
        UpstreamDir = $UpstreamDir
        ComposePath = $ComposePath
        NetworkName = $InternalNetworkName
        IngressNetworkName = $IngressNetworkName
        ExpectedNetworkOptions = $ExpectedNetworkOptions
        AppVolumeName = [string]$Lock.runtime.volume_names.'sth-app-data'
        DbVolumeName = [string]$Lock.runtime.volume_names.'sth-db2-data'
        ImageMap = $ImageMap
    }
}

function Assert-LocalDockerDaemon {
    foreach ($DockerEnvKey in @("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH")) {
        Assert-True ([string]::IsNullOrWhiteSpace([System.Environment]::GetEnvironmentVariable($DockerEnvKey, "Process"))) "$DockerEnvKey override is forbidden."
    }
    $ContextName = (Invoke-NativeCapture "docker" @("context", "show") "docker-context-show").Text.Trim()
    Assert-True ($ContextName.Length -gt 0) "Docker context name is empty."
    $ContextJson = (Invoke-NativeCapture "docker" @("context", "inspect", $ContextName) "docker-context-inspect" -NoLog).Text | ConvertFrom-Json
    Assert-True (@($ContextJson).Count -eq 1) "Docker context inspection was ambiguous."
    $HostValue = [string]$ContextJson[0].Endpoints.docker.Host
    Assert-True ($HostValue -match '^(?:npipe|unix)://') "Remote TCP/HTTP/SSH Docker contexts are forbidden."
    Assert-True ($HostValue -notmatch '^(?:tcp|http|https|ssh)://') "Remote Docker daemon endpoint is forbidden."
    Add-RawLog "docker-context-boundary" ("context=" + $ContextName + "; endpoint_scheme=" + $HostValue.Split(':')[0] + "; remote=false")
    $Server = (Invoke-NativeCapture "docker" @("version", "--format", "{{.Server.Os}}|{{.Server.Arch}}") "docker-server-platform").Text.Trim().Split('|')
    Assert-True (($Server.Count -eq 2) -and ($Server[0] -ceq "linux") -and ($Server[1] -ceq "amd64")) "Docker daemon must be local Linux/amd64."
    return [ordered]@{
        context = $ContextName
        endpoint_scheme = $HostValue.Split(':')[0]
        server_os = $Server[0]
        server_architecture = $Server[1]
        remote_daemon = $false
    }
}

function Assert-Checkout {
    param($Context)
    Assert-True (Test-Path -LiteralPath (Join-Path $Context.UpstreamDir ".git") -PathType Container) "The upstream checkout has no .git directory."
    $Head = (Invoke-NativeCapture "git" @("-C", $Context.UpstreamDir, "rev-parse", "HEAD") "git-head").Text.Trim()
    Assert-True ($Head -ceq $Context.Commit) "Upstream HEAD does not match the lock."
    $Symbolic = Invoke-NativeCapture "git" @("-C", $Context.UpstreamDir, "symbolic-ref", "-q", "HEAD") "git-detached" -AllowFailure
    Assert-True (($Symbolic.ExitCode -ne 0) -and ($Symbolic.Text.Trim().Length -eq 0)) "Upstream checkout must remain detached."
    $AutoCrlf = (Invoke-NativeCapture "git" @("-C", $Context.UpstreamDir, "config", "--local", "--get", "core.autocrlf") "git-core-autocrlf").Text.Trim()
    Assert-True ($AutoCrlf -ceq "false") "The upstream checkout must set local core.autocrlf=false."
    $Status = (Invoke-NativeCapture "git" @("-C", $Context.UpstreamDir, "status", "--porcelain=v1", "--untracked-files=all") "git-status").Text.Trim()
    Assert-True ($Status.Length -eq 0) "The upstream worktree is not clean."
    $Ignored = @((Invoke-NativeCapture "git" @("-C", $Context.UpstreamDir, "status", "--ignored=matching", "--porcelain=v1", "--untracked-files=all", "--", ".") "git-ignored-build-context").Text -split "`r?`n" | Where-Object { $_ -match '^!! ' })
    Assert-True ($Ignored.Count -eq 0) "Ignored material exists in the upstream build context."
    Assert-True (-not (Test-Path -LiteralPath (Join-Path $Context.UpstreamDir ".env"))) "A root upstream .env is forbidden."

    $ForbiddenExact = @(
        "backend/.env.local",
        "backend/.env.local.php",
        "backend/vendor",
        "backend/var",
        "backend/config/secrets/prod/prod.decrypt.private.php",
        "frontend/node_modules",
        "frontend/.pnpm-store",
        "frontend/.angular/cache"
    )
    foreach ($Relative in $ForbiddenExact) {
        $Path = Resolve-ChildPath $Context.UpstreamDir $Relative "forbidden build-context path"
        Assert-True (-not (Test-Path -LiteralPath $Path)) "Forbidden build-context path exists: $Relative"
    }
    $BackendDir = Join-Path $Context.UpstreamDir "backend"
    $LocalEnvFiles = @(Get-ChildItem -LiteralPath $BackendDir -Force -File -Filter ".env.*.local" -ErrorAction SilentlyContinue)
    Assert-True ($LocalEnvFiles.Count -eq 0) "Forbidden backend/.env.*.local files are present."

    foreach ($Scope in @($Context.Lock.source_materialization.required_scopes)) {
        $ScopeName = [string]$Scope
        Assert-True ($ScopeName -cmatch '^[A-Za-z0-9._-]+$') "Invalid materialization scope in lock."
        $Tracked = @((Invoke-NativeCapture "git" @("-C", $Context.UpstreamDir, "ls-tree", "-r", "--name-only", $Context.Commit, "--", $ScopeName) ("materialization-" + $ScopeName)).Text -split "`r?`n" | Where-Object { $_ })
        Assert-True ($Tracked.Count -gt 0) "Locked materialization scope is empty: $ScopeName"
        foreach ($Relative in $Tracked) {
            $TrackedPath = Resolve-ChildPath $Context.UpstreamDir $Relative "tracked materialized path"
            Assert-True (Test-Path -LiteralPath $TrackedPath) "Tracked source is not materialized: $Relative"
        }
    }

    foreach ($Property in $Context.Lock.source_materialization.sha256.PSObject.Properties) {
        $Relative = [string]$Property.Name
        $Expected = [string]$Property.Value
        Assert-True ($Expected -cmatch '^[0-9a-f]{64}$') "Invalid locked source hash for $Relative."
        $Path = Resolve-ChildPath $Context.UpstreamDir $Relative "source hash path"
        Assert-True (Test-Path -LiteralPath $Path -PathType Leaf) "Locked source file is missing: $Relative"
        Assert-True ((Get-Sha256 $Path) -ceq $Expected) "Source hash mismatch: $Relative"
    }
}

function New-RandomHex {
    param([int]$Bytes = 32)
    $Buffer = New-Object byte[] $Bytes
    $Rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $Rng.GetBytes($Buffer) } finally { $Rng.Dispose() }
    return (($Buffer | ForEach-Object { $_.ToString("x2") }) -join "")
}

function Read-SyntheticEnv {
    param([string]$Path)
    $Map = @{}
    foreach ($Line in (Get-Content -Encoding UTF8 -LiteralPath $Path)) {
        if (($Line.Length -eq 0) -or $Line.StartsWith("#")) { continue }
        $Index = $Line.IndexOf("=")
        Assert-True ($Index -gt 0) "Malformed synthetic env line."
        $Key = $Line.Substring(0, $Index)
        $Value = $Line.Substring($Index + 1)
        Assert-True ($Key -cmatch '^[A-Z][A-Z0-9_]*$') "Invalid synthetic env key."
        Assert-True (-not $Map.ContainsKey($Key)) "Duplicate synthetic env key."
        $Map[$Key] = $Value
    }
    $AllowedKeys = @(
        "APP_ENV", "APP_DEBUG", "APP_SECRET", "DB2_DBNAME", "DB2_USER", "DB2_PASSWORD", "DB2_ROOT_PASSWORD", "DB2_TEST_DB_PASSWORD",
        "MAILER_DSN", "SERVER_HOST_NAME", "STH_FRONTEND_CONFIG", "STH_GCS_PATH_PREFIX", "STH_NOTIFICATIONS_ENABLED",
        "STH_LOCAL_REVIEW_LOGIN",
        "STH_VALIDATOR_ENDPOINT", "STH_JSON_VALIDATOR_ENDPOINT", "STH_SHACL_VALIDATOR_ENDPOINT", "STH_AI_GATEWAY_ENABLED",
        "STH_AI_GATEWAY_ENDPOINT", "STH_AI_GATEWAY_DEFAULT_MODEL_PROVIDER", "STH_AI_GATEWAY_DEFAULT_MODEL", "STH_AI_GATEWAY_DEFAULT_API_KEY"
    )
    Assert-True ($Map.Count -eq $AllowedKeys.Count) "Synthetic env key count differs from the exact allowlist."
    foreach ($Key in $Map.Keys) { Assert-True ($AllowedKeys -contains $Key) "Synthetic env contains an unapproved key: $Key" }
    foreach ($Key in $AllowedKeys) { Assert-True ($Map.ContainsKey($Key)) "Synthetic env is missing approved key: $Key" }
    foreach ($SecretKey in @("APP_SECRET", "DB2_PASSWORD", "DB2_ROOT_PASSWORD", "DB2_TEST_DB_PASSWORD")) {
        Assert-True ($Map.ContainsKey($SecretKey)) "Synthetic env is missing $SecretKey."
        Assert-True ([string]$Map[$SecretKey] -cmatch '^[0-9a-f]{64}$') "Synthetic $SecretKey is not a 256-bit CSPRNG hex value."
    }
    Assert-True ([string]$Map["APP_ENV"] -ceq "prod") "Synthetic APP_ENV must be prod."
    Assert-True ([string]$Map["APP_DEBUG"] -ceq "0") "Synthetic APP_DEBUG must be 0."
    Assert-True ([string]$Map["STH_LOCAL_REVIEW_LOGIN"] -ceq "1") "Synthetic STH_LOCAL_REVIEW_LOGIN must be the explicit value 1."
    return $Map
}

function Initialize-SyntheticEnv {
    param($Context)
    if (-not (Test-Path -LiteralPath $EnvPath -PathType Leaf)) {
        $Lines = @(
            "APP_ENV=prod",
            "APP_DEBUG=0",
            ("APP_SECRET=" + (New-RandomHex)),
            "DB2_DBNAME=app",
            "DB2_USER=sth",
            ("DB2_PASSWORD=" + (New-RandomHex)),
            ("DB2_ROOT_PASSWORD=" + (New-RandomHex)),
            ("DB2_TEST_DB_PASSWORD=" + (New-RandomHex)),
            "MAILER_DSN=null://null",
            ("SERVER_HOST_NAME=http://127.0.0.1:" + $Context.HttpPort),
            "STH_FRONTEND_CONFIG=default",
            "STH_GCS_PATH_PREFIX=",
            "STH_NOTIFICATIONS_ENABLED=0",
            "STH_LOCAL_REVIEW_LOGIN=1",
            "STH_VALIDATOR_ENDPOINT=http://127.0.0.1:9/disabled",
            "STH_JSON_VALIDATOR_ENDPOINT=http://127.0.0.1:9/disabled",
            "STH_SHACL_VALIDATOR_ENDPOINT=http://127.0.0.1:9/disabled",
            "STH_AI_GATEWAY_ENABLED=0",
            "STH_AI_GATEWAY_ENDPOINT=http://127.0.0.1:9/disabled",
            "STH_AI_GATEWAY_DEFAULT_MODEL_PROVIDER=disabled",
            "STH_AI_GATEWAY_DEFAULT_MODEL=disabled",
            "STH_AI_GATEWAY_DEFAULT_API_KEY=disabled"
        )
        Write-Utf8NoBom $EnvPath (($Lines -join "`n") + "`n")
    } else {
        $ExistingLines = @(Get-Content -Encoding UTF8 -LiteralPath $EnvPath)
        $ExistingLocalReviewKeys = @($ExistingLines | Where-Object { $_ -cmatch '^STH_LOCAL_REVIEW_LOGIN=' })
        Assert-True ($ExistingLocalReviewKeys.Count -le 1) "Synthetic env contains duplicate STH_LOCAL_REVIEW_LOGIN keys."
        if ($ExistingLocalReviewKeys.Count -eq 0) {
            $ExistingLines += "STH_LOCAL_REVIEW_LOGIN=1"
            Write-Utf8NoBom $EnvPath (($ExistingLines -join "`n") + "`n")
        }
    }
    $Map = Read-SyntheticEnv $EnvPath
    $Map["SERVER_HOST_NAME"] = "http://127.0.0.1:" + $Context.HttpPort
    $OrderedKeys = @(
        "APP_ENV", "APP_DEBUG", "APP_SECRET", "DB2_DBNAME", "DB2_USER", "DB2_PASSWORD", "DB2_ROOT_PASSWORD", "DB2_TEST_DB_PASSWORD",
        "MAILER_DSN", "SERVER_HOST_NAME", "STH_FRONTEND_CONFIG", "STH_GCS_PATH_PREFIX", "STH_NOTIFICATIONS_ENABLED",
        "STH_LOCAL_REVIEW_LOGIN",
        "STH_VALIDATOR_ENDPOINT", "STH_JSON_VALIDATOR_ENDPOINT", "STH_SHACL_VALIDATOR_ENDPOINT", "STH_AI_GATEWAY_ENABLED",
        "STH_AI_GATEWAY_ENDPOINT", "STH_AI_GATEWAY_DEFAULT_MODEL_PROVIDER", "STH_AI_GATEWAY_DEFAULT_MODEL", "STH_AI_GATEWAY_DEFAULT_API_KEY"
    )
    $Canonical = @($OrderedKeys | ForEach-Object { $_ + "=" + [string]$Map[$_] })
    Write-Utf8NoBom $EnvPath (($Canonical -join "`n") + "`n")
    return Read-SyntheticEnv $EnvPath
}

function Get-DigestReference {
    param([string]$TaggedReference, [string]$Digest)
    $LastColon = $TaggedReference.LastIndexOf(":")
    Assert-True ($LastColon -gt 0) "Image reference lacks a tag: $TaggedReference"
    return $TaggedReference.Substring(0, $LastColon) + "@" + $Digest
}

function New-InlineDockerfile {
    param($Context)
    $DockerfilePath = Join-Path $Context.UpstreamDir "Dockerfile"
    $Text = Get-Content -Raw -Encoding UTF8 -LiteralPath $DockerfilePath
    $BracedBuildToken = '${STH_APP_VERSION_BUILD}'
    $BracedBuildTokenCount = @([regex]::Matches($Text, [regex]::Escape($BracedBuildToken))).Count
    Assert-True ($BracedBuildTokenCount -eq 1) "The pinned Dockerfile must contain exactly one braced STH_APP_VERSION_BUILD token."
    $Text = $Text.Replace($BracedBuildToken, $Context.Commit.Substring(0, 12))
    $FrontendToken = '$STH_FRONTEND_CONFIG'
    Assert-True (@([regex]::Matches($Text, [regex]::Escape($FrontendToken))).Count -eq 1) "The pinned Dockerfile must contain exactly one STH_FRONTEND_CONFIG expansion token."
    $Text = $Text.Replace($FrontendToken, 'default')
    $PhpIniToken = '$PHP_INI_DIR'
    Assert-True (@([regex]::Matches($Text, [regex]::Escape($PhpIniToken))).Count -eq 3) "The pinned Dockerfile must contain exactly three PHP_INI_DIR expansion tokens."
    $Text = $Text.Replace($PhpIniToken, '/usr/local/etc/php')

    $SecurityControllerRelativePath = "backend/src/Controller/SecurityController.php"
    $SecurityControllerContainerPath = "/app/src/Controller/SecurityController.php"
    $ExpectedSecurityControllerSha256 = "14332816e463349182363e2446799e88ce2f7c78bfdf2b63487e12d7f2a1c06d"
    $ExpectedPatchedSecurityControllerSha256 = "f694f53157af74fc706fda6a36dd63e4d033d7f3620703290246edbaac0312b1"
    $SecurityControllerPath = Resolve-ChildPath $Context.UpstreamDir $SecurityControllerRelativePath "SecurityController patch source"
    Assert-True (Test-Path -LiteralPath $SecurityControllerPath -PathType Leaf) "The pinned SecurityController patch source is missing."
    Assert-True ((Get-Sha256 $SecurityControllerPath) -ceq $ExpectedSecurityControllerSha256) "The pinned SecurityController differs from the reviewed local-login patch preimage."
    $SecurityControllerText = Get-Content -Raw -Encoding UTF8 -LiteralPath $SecurityControllerPath
    $OriginalDevLoginGate = @(
        '    ): Response {'
        '        $this->denyUnlessDev($kernel);'
        ''
        '        // Save login timestamp'
    ) -join "`n"
    $PatchedDevLoginGate = @(
        '    ): Response {'
        '        if ($kernel->getEnvironment() !== ''dev'' && (getenv(''STH_LOCAL_REVIEW_LOGIN'') !== ''1'' || $account->getId() !== ''admin'')) {'
        '            throw $this->createAccessDeniedException(''Only for development or explicit admin local review'');'
        '        }'
        ''
        '        // Save login timestamp'
    ) -join "`n"
    $JsonLoginDevOnlyGate = @(
        '    public function jsonLogin(#[CurrentUser] ?Account $account, KernelInterface $kernel, Security $security): Response'
        '    {'
        '        $this->denyUnlessDev($kernel);'
    ) -join "`n"
    Assert-True (@([regex]::Matches($SecurityControllerText, [regex]::Escape($OriginalDevLoginGate))).Count -eq 1) "The reviewed devLogin gate patch must have exactly one preimage match."
    Assert-True (@([regex]::Matches($SecurityControllerText, [regex]::Escape($JsonLoginDevOnlyGate))).Count -eq 1) "The reviewed jsonLogin dev-only gate is absent from the patch preimage."
    $PatchedSecurityControllerText = $SecurityControllerText.Replace($OriginalDevLoginGate, $PatchedDevLoginGate)
    Assert-True (@([regex]::Matches($PatchedSecurityControllerText, [regex]::Escape($OriginalDevLoginGate))).Count -eq 0) "The devLogin patch preimage remains after deterministic replacement."
    Assert-True (@([regex]::Matches($PatchedSecurityControllerText, [regex]::Escape($PatchedDevLoginGate))).Count -eq 1) "The devLogin patch postimage must occur exactly once."
    Assert-True (@([regex]::Matches($PatchedSecurityControllerText, [regex]::Escape($JsonLoginDevOnlyGate))).Count -eq 1) "The jsonLogin dev-only gate changed during local-review patching."
    Assert-True (@([regex]::Matches($PatchedSecurityControllerText, [regex]::Escape("STH_LOCAL_REVIEW_LOGIN"))).Count -eq 1) "The local-review flag must occur only in the devLogin gate."
    Assert-True (@([regex]::Matches($PatchedSecurityControllerText, [regex]::Escape("`$account->getId() !== 'admin'"))).Count -eq 1) "The production local-review gate must be restricted to the seeded admin account."
    $PatchedSecurityControllerSha256 = Get-TextSha256 $PatchedSecurityControllerText
    Assert-True ($PatchedSecurityControllerSha256 -ceq $ExpectedPatchedSecurityControllerSha256) "The deterministic SecurityController patch postimage hash differs from review."

    $OriginalGateBase64 = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($OriginalDevLoginGate))
    $PatchedGateBase64 = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($PatchedDevLoginGate))
    $BackendCopyAnchor = "COPY --from=backend-builder /app /app"
    Assert-True (@([regex]::Matches($Text, [regex]::Escape($BackendCopyAnchor))).Count -eq 1) "The runtime backend COPY anchor must occur exactly once."
    $PatchDockerfileLines = @(
        $BackendCopyAnchor,
        "",
        "# DSSC derived-runtime patch: explicit loopback local review login; upstream checkout remains unchanged.",
        ('RUN echo "{0}  {1}" | sha256sum -c - \' -f $ExpectedSecurityControllerSha256, $SecurityControllerContainerPath),
        (' && php -r "file_put_contents(''{0}'', str_replace(base64_decode(''{1}''), base64_decode(''{2}''), file_get_contents(''{0}'')));" \' -f $SecurityControllerContainerPath, $OriginalGateBase64, $PatchedGateBase64),
        (' && echo "{0}  {1}" | sha256sum -c -' -f $ExpectedPatchedSecurityControllerSha256, $SecurityControllerContainerPath)
    )
    $Text = $Text.Replace($BackendCopyAnchor, ($PatchDockerfileLines -join "`n"))
    Assert-True (@([regex]::Matches($Text, [regex]::Escape($ExpectedSecurityControllerSha256))).Count -eq 1) "The runtime Dockerfile must contain one SecurityController preimage hash check."
    Assert-True (@([regex]::Matches($Text, [regex]::Escape($ExpectedPatchedSecurityControllerSha256))).Count -eq 1) "The runtime Dockerfile must contain one SecurityController postimage hash check."
    Assert-True (@([regex]::Matches($Text, [regex]::Escape($OriginalGateBase64))).Count -eq 1) "The runtime Dockerfile must contain one reviewed patch preimage."
    Assert-True (@([regex]::Matches($Text, [regex]::Escape($PatchedGateBase64))).Count -eq 1) "The runtime Dockerfile must contain one reviewed patch postimage."
    $script:SecurityControllerPatchProjection = [ordered]@{
        source_path = $SecurityControllerRelativePath
        container_path = $SecurityControllerContainerPath
        source_sha256 = $ExpectedSecurityControllerSha256
        patched_sha256 = $ExpectedPatchedSecurityControllerSha256
        exact_replacement_count = 1
        build_preimage_hash_check = $true
        build_postimage_hash_check = $true
        runtime_flag = "STH_LOCAL_REVIEW_LOGIN"
        required_runtime_value = "1"
        dev_login_policy = "dev-or-explicit-admin-local-review"
        json_login_policy = "dev-only-unchanged"
        mutation_scope = "derived-runtime-image-only"
        upstream_checkout_modified = $false
    }
    Assert-True (@([regex]::Matches($Text, '\$')).Count -eq 0) "The deterministic runtime Dockerfile must contain zero dollar tokens."
    $ExpectedReferences = @("node:22", "composer:2", "dunglas/frankenphp:php8.4")
    $Observed = @([regex]::Matches($Text, '(?m)^FROM[ \t]+(?<image>\S+)') | ForEach-Object { $_.Groups['image'].Value })
    Assert-True ($Observed.Count -eq 3) "The upstream Dockerfile must contain exactly three FROM instructions."
    foreach ($Reference in $ExpectedReferences) {
        Assert-True ((@($Observed | Where-Object { $_ -ceq $Reference })).Count -eq 1) "Unexpected FROM contract for $Reference."
        $DigestReference = Get-DigestReference $Reference $Context.ImageMap[$Reference]
        $Pattern = '(?m)^FROM[ \t]+' + [regex]::Escape($Reference) + '(?<suffix>[ \t]+AS[ \t]+[^\r\n]+)?[ \t]*$'
        $Text = [regex]::Replace($Text, $Pattern, { param($Match) "FROM $DigestReference" + $Match.Groups['suffix'].Value })
    }
    Assert-True (-not [regex]::IsMatch($Text, '(?m)^FROM[ \t]+[^@\s]+:[^\s]+')) "A mutable FROM reference remains after substitution."
    Write-Utf8NoBom $InlineDockerfilePath $Text
    return $Text
}

function New-Overlay {
    param($Context, [string]$DockerfileText)
    $AppImage = ($Context.ProjectName + "-sth:" + $Context.Commit.Substring(0, 12))
    $DbImage = Get-DigestReference "mariadb:11.4" $Context.ImageMap["mariadb:11.4"]
    $DockerfileLines = $DockerfileText -split "`r?`n"
    $Lines = New-Object System.Collections.Generic.List[string]
    foreach ($Line in @(
        "services:",
        "  sth:",
        ("    container_name: `"" + $Context.ProjectName + "-sth`""),
        "    labels:",
        ("      dssc.semantic-treehouse.project: `"" + $Context.ProjectName + "`""),
        ("      dssc.semantic-treehouse.upstream-commit: `"" + $Context.Commit + "`""),
        "      dssc.semantic-treehouse.runtime-contract: v1",
        ("    image: `"" + $AppImage + "`""),
        "    platform: linux/amd64",
        "    build: !override",
        "      context: .",
        "      dockerfile_inline: |"
    )) { $Lines.Add($Line) }
    foreach ($Line in $DockerfileLines) {
        $Lines.Add("        " + $Line)
    }
    foreach ($Line in @(
        "      args:",
        "        STH_FRONTEND_CONFIG: default",
        ("        STH_APP_VERSION_BUILD: `"" + $Context.Commit.Substring(0, 12) + "`""),
        "    environment: !override",
        "      APP_ENV: prod",
        "      APP_DEBUG: `"0`"",
        '      APP_SECRET: ${APP_SECRET}',
        '      APP_DBUSER: ${DB2_USER}',
        '      APP_DBPASS: ${DB2_PASSWORD}',
        "      APP_DBHOST: sth-db2",
        '      APP_DBNAME: ${DB2_DBNAME:-app}',
        "      APP_DBVERSION: 11.4.10-MariaDB",
        "      SERVER_NAME: ':80'",
        '      SERVER_HOST_NAME: ${SERVER_HOST_NAME}',
        '      MAILER_DSN: ${MAILER_DSN}',
        "      STH_GCS_PATH_PREFIX: ''",
        "      STH_NOTIFICATIONS_ENABLED: '0'",
        '      STH_LOCAL_REVIEW_LOGIN: ${STH_LOCAL_REVIEW_LOGIN}',
        "      STH_AI_GATEWAY_ENABLED: '0'",
        "    depends_on: !override",
        "      sth-db2:",
        "        condition: service_healthy",
        "        required: true",
        "    ports: !override",
        ("      - `"127.0.0.1:" + $Context.HttpPort + ":80`""),
        "    volumes: !override",
        "      - sth-app-data:/app/var/user_data",
        "    networks: !override",
        "      - treehouse-internal",
        "      - treehouse-ingress",
        "    security_opt: !override",
        "      - no-new-privileges:true",
        "    restart: `"no`"",
        "    extra_hosts: !reset []",
        "    privileged: false",
        "",
        "  sth-db2:",
        ("    container_name: `"" + $Context.ProjectName + "-sth-db2`""),
        "    labels:",
        ("      dssc.semantic-treehouse.project: `"" + $Context.ProjectName + "`""),
        ("      dssc.semantic-treehouse.upstream-commit: `"" + $Context.Commit + "`""),
        "      dssc.semantic-treehouse.runtime-contract: v1",
        ("    image: `"" + $DbImage + "`""),
        "    platform: linux/amd64",
        "    environment: !override",
        '      MARIADB_DATABASE: ${DB2_DBNAME:-app}',
        '      MARIADB_ROOT_PASSWORD: ${DB2_ROOT_PASSWORD}',
        '      MARIADB_USER: ${DB2_USER}',
        '      MARIADB_PASSWORD: ${DB2_PASSWORD}',
        "    volumes: !override",
        "      - sth-db2-data:/var/lib/mysql",
        "    ports: !override []",
        "    networks: !override",
        "      - treehouse-internal",
        "    security_opt: !override",
        "      - no-new-privileges:true",
        "    restart: `"no`"",
        "    extra_hosts: !reset []",
        "    privileged: false",
        "    healthcheck: !override",
        "      test: [CMD, healthcheck.sh, --connect, --innodb_initialized]",
        "      interval: 5s",
        "      timeout: 5s",
        "      retries: 30",
        "      start_period: 20s",
        "",
        "volumes:",
        "  sth-app-data:",
        "    external: true",
        ("    name: `"" + $Context.AppVolumeName + "`""),
        "  sth-db2-data:",
        "    external: true",
        ("    name: `"" + $Context.DbVolumeName + "`""),
        "",
        "networks:",
        "  treehouse-internal:",
        ("    name: `"" + $Context.NetworkName + "`""),
        "    driver: bridge",
        "    internal: true",
        "    labels:",
        ("      dssc.semantic-treehouse.project: `"" + $Context.ProjectName + "`""),
        ("      dssc.semantic-treehouse.upstream-commit: `"" + $Context.Commit + "`""),
        "      dssc.semantic-treehouse.runtime-contract: v1",
        "      dssc.semantic-treehouse.network-role: internal",
        "",
        "  treehouse-ingress:",
        ("    name: `"" + $Context.IngressNetworkName + "`""),
        "    driver: bridge",
        "    internal: false",
        "    labels:",
        ("      dssc.semantic-treehouse.project: `"" + $Context.ProjectName + "`""),
        ("      dssc.semantic-treehouse.upstream-commit: `"" + $Context.Commit + "`""),
        "      dssc.semantic-treehouse.runtime-contract: v1",
        "      dssc.semantic-treehouse.network-role: ingress"
    )) { $Lines.Add($Line) }
    Write-Utf8NoBom $OverlayPath (($Lines -join "`n") + "`n")
    return [PSCustomObject]@{ AppImage = $AppImage; DbImage = $DbImage }
}

function Get-ComposeArguments {
    param($Context)
    return @(
        "compose", "--project-name", $Context.ProjectName,
        "--project-directory", $Context.UpstreamDir,
        "--env-file", $EnvPath,
        "-f", $Context.ComposePath,
        "-f", $OverlayPath
    )
}

function Get-PropertyNames {
    param($Value)
    if ($null -eq $Value) { return @() }
    return @($Value.PSObject.Properties | ForEach-Object { $_.Name })
}

function Get-ExpectedRuntimeNetworkOptions {
    param($Lock)
    Assert-True ($Lock.runtime.PSObject.Properties.Name -ccontains "realized_network_options") "The lock must declare realized_network_options."
    $Options = $Lock.runtime.realized_network_options
    Assert-True ($null -ne $Options) "The locked realized network options are null."
    $ActualNames = @(Get-PropertyNames $Options | Sort-Object)
    $ExpectedNames = @(@("com.docker.network.enable_ipv4", "com.docker.network.enable_ipv6") | Sort-Object)
    Assert-True (($ActualNames.Count -eq 2) -and (($ActualNames -join "|") -ceq ($ExpectedNames -join "|"))) "The lock must contain the exact realized network option key set."
    Assert-True (($Options.'com.docker.network.enable_ipv4' -is [string]) -and ($Options.'com.docker.network.enable_ipv4' -ceq "true") -and ($Options.'com.docker.network.enable_ipv6' -is [string]) -and ($Options.'com.docker.network.enable_ipv6' -ceq "false")) "The locked realized network option values differ from the approved literals."
    return [ordered]@{
        "com.docker.network.enable_ipv4" = "true"
        "com.docker.network.enable_ipv6" = "false"
    }
}

function Test-ExactRuntimeNetworkOptions {
    param($Actual, $Expected)
    if (($null -eq $Actual) -or ($null -eq $Expected)) { return $false }
    $ActualNames = @(Get-PropertyNames $Actual | Sort-Object)
    $ExpectedNames = @($Expected.Keys | Sort-Object)
    if (($ActualNames.Count -ne $ExpectedNames.Count) -or (($ActualNames -join "|") -cne ($ExpectedNames -join "|"))) { return $false }
    foreach ($Name in $ExpectedNames) {
        $ActualValue = $Actual.PSObject.Properties[$Name].Value
        if (($ActualValue -isnot [string]) -or ($ActualValue -cne [string]$Expected[$Name])) { return $false }
    }
    return $true
}

function ConvertTo-SafeRuntimeNetworkOptions {
    param($Actual)
    $Projection = [ordered]@{}
    if ($null -eq $Actual) { return $Projection }
    foreach ($Property in @($Actual.PSObject.Properties | Sort-Object Name)) {
        $Name = ConvertTo-SafeRuntimeText ([string]$Property.Name)
        $Projection[$Name] = ConvertTo-SafeRuntimeText ([string]$Property.Value)
    }
    return $Projection
}

function Get-PublishedHostBindingCount {
    param($PortMap)
    if ($null -eq $PortMap) { return 0 }
    $Count = 0
    foreach ($Property in @($PortMap.PSObject.Properties)) {
        $Count += @($Property.Value | Where-Object { $null -ne $_ }).Count
    }
    return $Count
}

function Assert-NoUnsafeServiceFields {
    param($Service, [string]$Name)
    if ($Service.PSObject.Properties.Name -contains "privileged") {
        Assert-True (-not [bool]$Service.privileged) "$Name must not be privileged."
    }
    foreach ($Field in @("cap_add", "devices", "extra_hosts")) {
        if ($Service.PSObject.Properties.Name -contains $Field) {
            Assert-True (@($Service.$Field).Count -eq 0) "$Name contains forbidden $Field."
        }
    }
    $Security = @($Service.security_opt | ForEach-Object { [string]$_ })
    Assert-True ($Security -contains "no-new-privileges:true") "$Name lacks no-new-privileges."
    foreach ($Mount in @($Service.volumes)) {
        Assert-True ([string]$Mount.type -ceq "volume") "$Name contains a non-volume mount."
    }
}

function Assert-ComposeBoundary {
    param($Context, $RuntimeImages, $Config, [string]$ExpectedDockerfileText)
    $ServiceNames = @(Get-PropertyNames $Config.services)
    Assert-True ($ServiceNames -contains "sth") "Effective config has no sth service."
    Assert-True ($ServiceNames -contains "sth-db2") "Effective config has no sth-db2 service."

    $Visited = @{}
    $Pending = New-Object System.Collections.Stack
    $Pending.Push("sth")
    while ($Pending.Count -gt 0) {
        $Name = [string]$Pending.Pop()
        if ($Visited.ContainsKey($Name)) { continue }
        Assert-True ($ServiceNames -contains $Name) "Dependency service is absent: $Name"
        $Visited[$Name] = $true
        $Service = $Config.services.$Name
        $DependsOn = if ($Service.PSObject.Properties.Name -contains "depends_on") { $Service.depends_on } else { $null }
        foreach ($Dependency in (Get-PropertyNames $DependsOn)) { $Pending.Push($Dependency) }
    }
    $Closure = @($Visited.Keys | Sort-Object)
    Assert-True (($Closure.Count -eq 2) -and ($Closure[0] -ceq "sth") -and ($Closure[1] -ceq "sth-db2")) "Target dependency closure must equal {sth, sth-db2}."

    $App = $Config.services.sth
    $Db = $Config.services.'sth-db2'
    Assert-NoUnsafeServiceFields $App "sth"
    Assert-NoUnsafeServiceFields $Db "sth-db2"
    foreach ($Service in @($App, $Db)) {
        Assert-True ([string]$Service.labels.'dssc.semantic-treehouse.project' -ceq $Context.ProjectName) "Service project ownership label differs from lock."
        Assert-True ([string]$Service.labels.'dssc.semantic-treehouse.upstream-commit' -ceq $Context.Commit) "Service upstream ownership label differs from lock."
        Assert-True ([string]$Service.labels.'dssc.semantic-treehouse.runtime-contract' -ceq "v1") "Service runtime contract label is absent."
    }
    Assert-True ([string]$App.image -ceq $RuntimeImages.AppImage) "Unexpected sth image name."
    Assert-True ([string]$Db.image -ceq $RuntimeImages.DbImage) "MariaDB image is not the locked digest reference."
    Assert-True ($null -ne $App.build.dockerfile_inline) "sth must use dockerfile_inline."
    $EffectiveDockerfileText = [string]$App.build.dockerfile_inline
    Assert-True ((Get-FunctionalDockerfileProjection $EffectiveDockerfileText) -ceq (Get-FunctionalDockerfileProjection $ExpectedDockerfileText)) "Compose config functional dockerfile_inline differs from the deterministic runtime Dockerfile."
    Assert-True (@([regex]::Matches($EffectiveDockerfileText, '\$')).Count -eq 0) "Compose config dockerfile_inline must contain zero dollar tokens."
    Assert-True ($null -ne $script:SecurityControllerPatchProjection) "The reviewed derived-runtime SecurityController patch projection is absent."
    $ExpectedAppEnvKeys = @(
        "APP_ENV", "APP_DEBUG", "APP_SECRET", "APP_DBUSER", "APP_DBPASS", "APP_DBHOST", "APP_DBNAME", "APP_DBVERSION",
        "SERVER_NAME", "SERVER_HOST_NAME", "MAILER_DSN", "STH_GCS_PATH_PREFIX", "STH_NOTIFICATIONS_ENABLED",
        "STH_LOCAL_REVIEW_LOGIN", "STH_AI_GATEWAY_ENABLED"
    )
    $AppEnvKeys = @(Get-PropertyNames $App.environment)
    Assert-True ($AppEnvKeys.Count -eq $ExpectedAppEnvKeys.Count) "Effective sth environment key count differs from the exact allowlist."
    foreach ($Key in $AppEnvKeys) { Assert-True ($ExpectedAppEnvKeys -contains $Key) "Effective sth environment contains an unapproved key: $Key" }
    foreach ($Key in $ExpectedAppEnvKeys) { Assert-True ($AppEnvKeys -contains $Key) "Effective sth environment is missing approved key: $Key" }
    Assert-True ([string]$App.environment.APP_ENV -ceq "prod") "Effective APP_ENV must be prod."
    Assert-True ([string]$App.environment.APP_DEBUG -ceq "0") "Effective APP_DEBUG must be 0."
    Assert-True ([string]$App.environment.STH_LOCAL_REVIEW_LOGIN -ceq "1") "Effective STH_LOCAL_REVIEW_LOGIN must be the explicit value 1."
    Assert-True ([string]$App.environment.APP_SECRET -ceq [string]$script:ValidatedEnvMap["APP_SECRET"]) "Effective APP_SECRET differs from the validated synthetic env."
    Assert-True ([string]$App.environment.APP_DBPASS -ceq [string]$script:ValidatedEnvMap["DB2_PASSWORD"]) "Effective app DB password differs from synthetic env."
    Assert-True ([string]$Db.environment.MARIADB_PASSWORD -ceq [string]$script:ValidatedEnvMap["DB2_PASSWORD"]) "Effective MariaDB password differs from synthetic env."
    Assert-True ([string]$Db.environment.MARIADB_ROOT_PASSWORD -ceq [string]$script:ValidatedEnvMap["DB2_ROOT_PASSWORD"]) "Effective MariaDB root password differs from synthetic env."
    Assert-True ([string]$App.restart -ceq "no") "sth restart policy must be no."
    Assert-True ([string]$Db.restart -ceq "no") "sth-db2 restart policy must be no."
    $DbPorts = @(if ($Db.PSObject.Properties.Name -contains "ports") { $Db.ports })
    Assert-True ($DbPorts.Count -eq 0) "The database must publish zero ports."
    $Ports = @($App.ports)
    Assert-True ($Ports.Count -eq 1) "sth must publish exactly one port."
    $Port = $Ports[0]
    Assert-True ([string]$Port.host_ip -ceq "127.0.0.1") "sth must bind only to loopback."
    Assert-True ([int]$Port.published -eq $Context.HttpPort) "sth published port differs from HttpPort."
    Assert-True ([int]$Port.target -eq 80) "sth target port must be 80."

    $AppMounts = @($App.volumes)
    $DbMounts = @($Db.volumes)
    Assert-True (($AppMounts.Count -eq 1) -and ([string]$AppMounts[0].source -ceq "sth-app-data") -and ([string]$AppMounts[0].target -ceq "/app/var/user_data")) "Unexpected sth volume mapping."
    Assert-True (($DbMounts.Count -eq 1) -and ([string]$DbMounts[0].source -ceq "sth-db2-data") -and ([string]$DbMounts[0].target -ceq "/var/lib/mysql")) "Unexpected database volume mapping."
    $DbEnvKeys = @(Get-PropertyNames $Db.environment)
    $ExpectedDbEnvKeys = @("MARIADB_DATABASE", "MARIADB_ROOT_PASSWORD", "MARIADB_USER", "MARIADB_PASSWORD")
    Assert-True ($DbEnvKeys.Count -eq $ExpectedDbEnvKeys.Count) "Effective sth-db2 environment key count differs from the exact allowlist."
    foreach ($Key in $DbEnvKeys) { Assert-True ($ExpectedDbEnvKeys -contains $Key) "Effective sth-db2 environment contains an unapproved key: $Key" }
    foreach ($Key in $ExpectedDbEnvKeys) { Assert-True ($DbEnvKeys -contains $Key) "Effective sth-db2 environment is missing approved key: $Key" }

    $AppNetworks = @(Get-PropertyNames $App.networks)
    $DbNetworks = @(Get-PropertyNames $Db.networks)
    Assert-True (($AppNetworks.Count -eq 2) -and ($AppNetworks -contains "treehouse-internal") -and ($AppNetworks -contains "treehouse-ingress")) "sth network boundary is invalid."
    Assert-True (($DbNetworks.Count -eq 1) -and ($DbNetworks[0] -ceq "treehouse-internal")) "sth-db2 network boundary is invalid."
    Assert-True ([bool]$Config.networks.'treehouse-internal'.internal) "Effective Treehouse network is not internal."
    Assert-True ([string]$Config.networks.'treehouse-internal'.driver -ceq "bridge") "Effective internal network driver must be bridge."
    Assert-True (-not ($Config.networks.'treehouse-internal'.PSObject.Properties.Name -contains "external")) "Effective internal network must be project managed."
    $InternalDriverOptions = if ($Config.networks.'treehouse-internal'.PSObject.Properties.Name -contains "driver_opts") { $Config.networks.'treehouse-internal'.driver_opts } else { $null }
    Assert-True (@(Get-PropertyNames $InternalDriverOptions).Count -eq 0) "Effective internal network driver options are forbidden."
    Assert-True ([string]$Config.networks.'treehouse-internal'.name -ceq $Context.NetworkName) "Effective network name differs from lock."
    Assert-True ([string]$Config.networks.'treehouse-internal'.labels.'dssc.semantic-treehouse.network-role' -ceq "internal") "Effective internal network role label is absent."
    $EffectiveIngressInternal = if ($Config.networks.'treehouse-ingress'.PSObject.Properties.Name -contains "internal") { [bool]$Config.networks.'treehouse-ingress'.internal } else { $false }
    Assert-True (-not $EffectiveIngressInternal) "Effective ingress network must be non-internal."
    Assert-True ([string]$Config.networks.'treehouse-ingress'.driver -ceq "bridge") "Effective ingress network driver must be bridge."
    Assert-True (-not ($Config.networks.'treehouse-ingress'.PSObject.Properties.Name -contains "external")) "Effective ingress network must be project managed."
    $IngressDriverOptions = if ($Config.networks.'treehouse-ingress'.PSObject.Properties.Name -contains "driver_opts") { $Config.networks.'treehouse-ingress'.driver_opts } else { $null }
    Assert-True (@(Get-PropertyNames $IngressDriverOptions).Count -eq 0) "Effective ingress network driver options are forbidden."
    Assert-True ([string]$Config.networks.'treehouse-ingress'.name -ceq $Context.IngressNetworkName) "Effective ingress network name differs from lock."
    Assert-True ([string]$Config.networks.'treehouse-ingress'.labels.'dssc.semantic-treehouse.network-role' -ceq "ingress") "Effective ingress network role label is absent."
    Assert-True ([string]$Config.volumes.'sth-app-data'.name -ceq $Context.AppVolumeName) "Effective app volume differs from lock."
    Assert-True ([string]$Config.volumes.'sth-db2-data'.name -ceq $Context.DbVolumeName) "Effective DB volume differs from lock."

    return [ordered]@{
        dependency_closure = $Closure
        target_service = "sth"
        dependency_service = "sth-db2"
        http_binding = ("127.0.0.1:" + $Context.HttpPort + ":80")
        database_published_ports = 0
        app_image = $RuntimeImages.AppImage
        database_image = $RuntimeImages.DbImage
        dockerfile_inline = $true
        dockerfile_inline_functional_exact = $true
        dockerfile_inline_dollar_count = 0
        deterministic_build_version = $Context.Commit.Substring(0, 12)
        deterministic_frontend_config = "default"
        deterministic_php_ini_dir = "/usr/local/etc/php"
        compose_unset_variable_warnings = 0
        app_env = "prod"
        app_debug = "0"
        application_environment_allowlist = @($ExpectedAppEnvKeys | Sort-Object)
        database_environment_allowlist = @($ExpectedDbEnvKeys | Sort-Object)
        local_review_login_enabled = $true
        local_review_login_scope = "loopback-fake-admin-devLogin-only"
        json_login_policy = "dev-only-unchanged"
        security_controller_patch = $script:SecurityControllerPatchProjection
        security_opt = "no-new-privileges:true"
        network_topology = "dual-network-app-ingress"
        internal_network = $Context.NetworkName
        ingress_network = $Context.IngressNetworkName
        ingress_network_internal = $false
        app_outbound_access = $true
        configured_driver_options = [ordered]@{}
        expected_realized_network_options = $Context.ExpectedNetworkOptions
        database_networks = @($Context.NetworkName)
        application_networks = @($Context.NetworkName, $Context.IngressNetworkName)
        volumes = @($Context.AppVolumeName, $Context.DbVolumeName)
        app_volume_target = "/app/var/user_data"
        bind_mounts = 0
        extra_hosts = 0
        privileged = $false
        cap_add = 0
        devices = 0
    }
}

function Normalize-OneTrailingLineEnding {
    param([string]$Text)
    return [regex]::Replace($Text, '(?:\r\n|\n|\r)?\z', '')
}

function Assert-BakePrintBoundary {
    param($BakePlan, [string]$ExpectedDockerfileText)
    Assert-True ($null -ne $BakePlan.target) "Compose build --print omitted the target map."
    Assert-True ($BakePlan.target.PSObject.Properties.Name -contains "sth") "Compose build --print omitted target sth."
    $BakeTarget = $BakePlan.target.sth
    Assert-True ($BakeTarget.PSObject.Properties.Name -contains "dockerfile-inline") "Compose build --print omitted dockerfile-inline."
    $BakeDockerfileText = [string]$BakeTarget.'dockerfile-inline'
    Assert-True ((Get-FunctionalDockerfileProjection $BakeDockerfileText) -ceq (Get-FunctionalDockerfileProjection $ExpectedDockerfileText)) "Compose Bake functional dockerfile-inline differs from the deterministic runtime Dockerfile."
    Assert-True (@([regex]::Matches($BakeDockerfileText, '\$')).Count -eq 0) "Compose Bake dockerfile-inline must contain zero dollar tokens."
    return [ordered]@{
        build_print_validated = $true
        bake_dockerfile_inline_functional_exact = $true
        bake_dockerfile_inline_dollar_count = 0
        bake_unset_variable_warnings = 0
    }
}

function Get-FunctionalDockerfileProjection {
    param([string]$Text)
    $FunctionalLines = @([regex]::Split($Text, '\r\n|\n|\r') | Where-Object {
        $Trimmed = $_.Trim()
        ($Trimmed.Length -gt 0) -and (-not $Trimmed.StartsWith('#'))
    })
    return ($FunctionalLines -join "`n")
}

function Assert-FinalBakeBoundary {
    param($FinalPlan, [string]$ExpectedDockerfileText)
    Assert-True ($null -ne $FinalPlan.target) "Buildx Bake final plan omitted the target map."
    Assert-True ($FinalPlan.target.PSObject.Properties.Name -contains "sth") "Buildx Bake final plan omitted target sth."
    $FinalTarget = $FinalPlan.target.sth
    Assert-True ($FinalTarget.PSObject.Properties.Name -contains "dockerfile-inline") "Buildx Bake final plan omitted dockerfile-inline."
    $FinalDockerfileText = [string]$FinalTarget.'dockerfile-inline'

    $RuntimeLines = @([regex]::Split($ExpectedDockerfileText, '\r\n|\n|\r'))
    $NonAsciiLines = @($RuntimeLines | Where-Object { $_ -match '[^\x00-\x7f]' })
    Assert-True ($NonAsciiLines.Count -eq 4) "The pinned runtime Dockerfile must contain exactly four non-ASCII lines."
    Assert-True (@($NonAsciiLines | Where-Object { -not $_.TrimStart().StartsWith('#') }).Count -eq 0) "Every non-ASCII runtime Dockerfile line must be a pure comment."

    $ExpectedFunctional = Get-FunctionalDockerfileProjection $ExpectedDockerfileText
    $FinalFunctional = Get-FunctionalDockerfileProjection $FinalDockerfileText
    if ($FinalFunctional -cne $ExpectedFunctional) {
        $ExpectedLines = @($ExpectedFunctional -split "`n")
        $FinalLines = @($FinalFunctional -split "`n")
        $FirstDifference = -1
        for ($Index = 0; $Index -lt [Math]::Max($ExpectedLines.Count, $FinalLines.Count); $Index++) {
            if (($Index -ge $ExpectedLines.Count) -or ($Index -ge $FinalLines.Count) -or ($ExpectedLines[$Index] -cne $FinalLines[$Index])) { $FirstDifference = $Index; break }
        }
        $ExpectedLine = if (($FirstDifference -ge 0) -and ($FirstDifference -lt $ExpectedLines.Count)) { $ExpectedLines[$FirstDifference] } else { "" }
        $FinalLine = if (($FirstDifference -ge 0) -and ($FirstDifference -lt $FinalLines.Count)) { $FinalLines[$FirstDifference] } else { "" }
        throw ("Buildx Bake final functional Dockerfile differs at line " + ($FirstDifference + 1) + "; expected_lines=" + $ExpectedLines.Count + "; final_lines=" + $FinalLines.Count + "; expected_length=" + $ExpectedLine.Length + "; final_length=" + $FinalLine.Length + "; expected_sha256=" + (Get-TextSha256 $ExpectedLine) + "; final_sha256=" + (Get-TextSha256 $FinalLine) + "; expected_dollars=" + @([regex]::Matches($ExpectedLine, '\$')).Count + "; final_dollars=" + @([regex]::Matches($FinalLine, '\$')).Count + "; final_total_dollars=" + @([regex]::Matches($FinalFunctional, '\$')).Count + "; final_double_pairs=" + @([regex]::Matches($FinalFunctional, '\$\$')).Count + "; final_double_build_version=" + @([regex]::Matches($FinalFunctional, [regex]::Escape('$$STH_APP_VERSION_BUILD'))).Count + "; final_double_frontend=" + @([regex]::Matches($FinalFunctional, [regex]::Escape('$$STH_FRONTEND_CONFIG'))).Count + "; final_double_php_ini=" + @([regex]::Matches($FinalFunctional, [regex]::Escape('$$PHP_INI_DIR'))).Count + ".")
    }
    $DollarCount = @([regex]::Matches($FinalFunctional, '\$')).Count
    Assert-True ($DollarCount -eq 0) "Buildx Bake final functional Dockerfile must contain zero dollar tokens."
    return [ordered]@{
        buildx_bake_print_validated = $true
        final_functional_dockerfile_exact = $true
        final_dockerfile_dollar_count = 0
        runtime_non_ascii_comment_lines = 4
        buildx_unset_variable_warnings = 0
    }
}

function Test-DockerObjectExists {
    param([string]$Kind, [string]$Name)
    $Template = if ($Kind -ceq "volume") { "{{.Name}}" } else { "{{.Id}}" }
    $Result = Invoke-NativeCapture "docker" @($Kind, "inspect", "--format", $Template, $Name) ("inspect-" + $Kind + "-" + $Name) -AllowFailure -NoLog
    return ($Result.ExitCode -eq 0)
}

function Get-VolumeLabels {
    param([string]$Name)
    $Result = Invoke-NativeCapture "docker" @("volume", "inspect", "--format", "{{json .Labels}}", $Name) ("volume-labels-" + $Name)
    return ($Result.Text | ConvertFrom-Json)
}

function Get-RequiredVolumeLabels {
    param($Context, [string]$LogicalName)
    return [ordered]@{
        "com.docker.compose.project" = $Context.ProjectName
        "com.docker.compose.volume" = $LogicalName
        "dssc.semantic-treehouse.managed" = "true"
        "dssc.semantic-treehouse.project" = $Context.ProjectName
        "dssc.semantic-treehouse.upstream-commit" = $Context.Commit
        "dssc.semantic-treehouse.logical-volume" = $LogicalName
        "dssc.semantic-treehouse.runtime-contract" = "v1"
    }
}

function Assert-VolumeLabels {
    param($Context, [string]$Name, [string]$LogicalName)
    $Actual = Get-VolumeLabels $Name
    $Expected = Get-RequiredVolumeLabels $Context $LogicalName
    foreach ($Key in $Expected.Keys) {
        Assert-True ($Actual.PSObject.Properties.Name -contains $Key) "Volume $Name lacks required label $Key."
        Assert-True ([string]$Actual.$Key -ceq [string]$Expected[$Key]) "Volume $Name has mismatched label $Key."
    }
}

function Assert-FreshRuntimeResources {
    param($Context)
    $Containers = (Invoke-NativeCapture "docker" @("ps", "-a", "--filter", ("label=com.docker.compose.project=" + $Context.ProjectName), "--format", "{{.ID}}") "fresh-project-containers").Text.Trim()
    Assert-True ($Containers.Length -eq 0) "Existing containers with the locked project label are forbidden for a fresh deployment."
    foreach ($ContainerName in @(($Context.ProjectName + "-sth"), ($Context.ProjectName + "-sth-db2"))) {
        $Named = Invoke-NativeCapture "docker" @("container", "inspect", "--format", "{{.Id}}", $ContainerName) ("fresh-container-name-" + $ContainerName) -AllowFailure -NoLog
        Assert-True ($Named.ExitCode -ne 0) "Target container name already exists: $ContainerName"
    }
    Assert-True (-not (Test-DockerObjectExists "network" $Context.NetworkName)) "The locked internal runtime network already exists."
    Assert-True (-not (Test-DockerObjectExists "network" $Context.IngressNetworkName)) "The locked ingress runtime network already exists."
    $ProjectNetworks = @((Invoke-NativeCapture "docker" @("network", "ls", "--filter", ("label=com.docker.compose.project=" + $Context.ProjectName), "--format", "{{.ID}}") "fresh-project-networks").Text -split "`r?`n" | Where-Object { $_ })
    Assert-True ($ProjectNetworks.Count -eq 0) "Existing project-labeled networks are forbidden for a fresh deployment."
    $ProjectVolumes = @((Invoke-NativeCapture "docker" @("volume", "ls", "--filter", ("label=com.docker.compose.project=" + $Context.ProjectName), "--format", "{{.Name}}") "fresh-project-volumes").Text -split "`r?`n" | Where-Object { $_ })
    Assert-True ($ProjectVolumes.Count -eq 0) "Existing project-labeled volumes are forbidden for a fresh deployment."
    foreach ($Name in @($Context.AppVolumeName, $Context.DbVolumeName)) {
        Assert-True (-not (Test-DockerObjectExists "volume" $Name)) "Existing target volume is forbidden for a fresh deployment: $Name"
    }
    $Listener = New-Object System.Net.Sockets.TcpListener -ArgumentList ([System.Net.IPAddress]::Parse("127.0.0.1"), $Context.HttpPort)
    try { $Listener.Start() } catch { throw "Approved loopback HTTP port is already occupied: $($Context.HttpPort)" } finally { try { $Listener.Stop() } catch { } }
}

function Assert-NoExistingRuntimeResourcesBeforeArtifactWrite {
    param($Context)
    foreach ($DockerEnvKey in @("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH")) {
        Assert-True ([string]::IsNullOrWhiteSpace([System.Environment]::GetEnvironmentVariable($DockerEnvKey, "Process"))) "Remote Docker environment overrides are forbidden."
    }
    $ContextName = (Invoke-NativeCapture "docker" @("context", "show") "artifact-guard-docker-context" -NoLog).Text.Trim()
    $ContextHost = (Invoke-NativeCapture "docker" @("context", "inspect", "--format", "{{.Endpoints.docker.Host}}", $ContextName) "artifact-guard-docker-endpoint" -NoLog).Text.Trim()
    Assert-True ($ContextHost -match '^(?:npipe|unix)://') "Remote Docker context is forbidden."
    $Containers = (Invoke-NativeCapture "docker" @("ps", "-a", "--filter", ("label=com.docker.compose.project=" + $Context.ProjectName), "--format", "{{.ID}}") "artifact-guard-project-containers" -NoLog).Text.Trim()
    Assert-True ($Containers.Length -eq 0) "Existing project containers forbid overwriting runtime artifacts."
    $Networks = (Invoke-NativeCapture "docker" @("network", "ls", "--filter", ("label=com.docker.compose.project=" + $Context.ProjectName), "--format", "{{.ID}}") "artifact-guard-project-networks" -NoLog).Text.Trim()
    Assert-True ($Networks.Length -eq 0) "Existing project networks forbid overwriting runtime artifacts."
    $Volumes = (Invoke-NativeCapture "docker" @("volume", "ls", "--filter", ("label=com.docker.compose.project=" + $Context.ProjectName), "--format", "{{.Name}}") "artifact-guard-project-volumes" -NoLog).Text.Trim()
    Assert-True ($Volumes.Length -eq 0) "Existing project volumes forbid overwriting runtime artifacts."
    foreach ($ContainerName in @(($Context.ProjectName + "-sth"), ($Context.ProjectName + "-sth-db2"))) {
        $NamedContainer = Invoke-NativeCapture "docker" @("container", "inspect", "--format", "{{.Id}}", $ContainerName) ("artifact-guard-container-" + $ContainerName) -AllowFailure -NoLog
        Assert-True ($NamedContainer.ExitCode -ne 0) "A locked container name forbids overwriting runtime artifacts: $ContainerName"
    }
    foreach ($NetworkName in @($Context.NetworkName, $Context.IngressNetworkName)) {
        $NamedNetwork = Invoke-NativeCapture "docker" @("network", "inspect", "--format", "{{.Id}}", $NetworkName) ("artifact-guard-network-" + $NetworkName) -AllowFailure -NoLog
        Assert-True ($NamedNetwork.ExitCode -ne 0) "A locked network name forbids overwriting runtime artifacts: $NetworkName"
    }
    foreach ($VolumeName in @($Context.AppVolumeName, $Context.DbVolumeName)) {
        $NamedVolume = Invoke-NativeCapture "docker" @("volume", "inspect", "--format", "{{.Name}}", $VolumeName) ("artifact-guard-volume-" + $VolumeName) -AllowFailure -NoLog
        Assert-True ($NamedVolume.ExitCode -ne 0) "A locked volume name forbids overwriting runtime artifacts: $VolumeName"
    }
}

function Assert-RealizedIngressBoundary {
    param($Context, [string[]]$ComposeArgs)
    $ContainerId = (Invoke-NativeCapture "docker" ($ComposeArgs + @("ps", "-q", "sth")) "realized-sth-container-id").Text.Trim()
    $DbContainerId = (Invoke-NativeCapture "docker" ($ComposeArgs + @("ps", "-q", "sth-db2")) "realized-sth-db2-container-id").Text.Trim()
    Assert-True ($ContainerId -cmatch '^[0-9a-f]{12,64}$') "The realized sth container ID is absent or malformed."
    Assert-True ($DbContainerId -cmatch '^[0-9a-f]{12,64}$') "The realized sth-db2 container ID is absent or malformed."

    $NetworksJson = (Invoke-NativeCapture "docker" @("inspect", "--format", "{{json .NetworkSettings.Networks}}", $ContainerId) "realized-sth-networks" -NoLog).Text.Trim()
    $PortsJson = (Invoke-NativeCapture "docker" @("inspect", "--format", "{{json .NetworkSettings.Ports}}", $ContainerId) "realized-sth-ports" -NoLog).Text.Trim()
    $HostBindingsJson = (Invoke-NativeCapture "docker" @("inspect", "--format", "{{json .HostConfig.PortBindings}}", $ContainerId) "realized-sth-host-bindings" -NoLog).Text.Trim()
    try {
        $Networks = $NetworksJson | ConvertFrom-Json
        $Ports = $PortsJson | ConvertFrom-Json
        $HostBindings = $HostBindingsJson | ConvertFrom-Json
    } catch {
        throw "The realized ingress projection is not valid JSON."
    }

    $AttachedNetworkNames = @(Get-PropertyNames $Networks | Sort-Object)
    $ExpectedNetworkNames = @(@($Context.IngressNetworkName, $Context.NetworkName) | Sort-Object)
    Assert-True (($AttachedNetworkNames.Count -eq 2) -and (($AttachedNetworkNames -join "|") -ceq ($ExpectedNetworkNames -join "|"))) "sth is not attached to the exact internal + ingress network set."

    $DbNetworksJson = (Invoke-NativeCapture "docker" @("inspect", "--format", "{{json .NetworkSettings.Networks}}", $DbContainerId) "realized-sth-db2-networks" -NoLog).Text.Trim()
    $DbPortsJson = (Invoke-NativeCapture "docker" @("inspect", "--format", "{{json .NetworkSettings.Ports}}", $DbContainerId) "realized-sth-db2-ports" -NoLog).Text.Trim()
    $DbHostBindingsJson = (Invoke-NativeCapture "docker" @("inspect", "--format", "{{json .HostConfig.PortBindings}}", $DbContainerId) "realized-sth-db2-host-bindings" -NoLog).Text.Trim()
    try {
        $DbNetworks = $DbNetworksJson | ConvertFrom-Json
        $DbPorts = $DbPortsJson | ConvertFrom-Json
        $DbHostBindings = $DbHostBindingsJson | ConvertFrom-Json
    } catch {
        throw "The realized database network projection is not valid JSON."
    }
    $DbAttachedNetworkNames = @(Get-PropertyNames $DbNetworks)
    Assert-True (($DbAttachedNetworkNames.Count -eq 1) -and ($DbAttachedNetworkNames[0] -ceq $Context.NetworkName)) "sth-db2 must attach only to the internal network."
    Assert-True ((Get-PublishedHostBindingCount $DbPorts) -eq 0) "sth-db2 has an effective published port."
    Assert-True ((Get-PublishedHostBindingCount $DbHostBindings) -eq 0) "sth-db2 retains a requested host port binding."

    $PortKey = "80/tcp"
    Assert-True ($Ports.PSObject.Properties.Name -contains $PortKey) "Docker did not program NetworkSettings.Ports for 80/tcp."
    Assert-True ($HostBindings.PSObject.Properties.Name -contains $PortKey) "Docker did not retain HostConfig.PortBindings for 80/tcp."
    $RealizedBindings = @($Ports.PSObject.Properties[$PortKey].Value)
    $RequestedBindings = @($HostBindings.PSObject.Properties[$PortKey].Value)
    Assert-True (($RealizedBindings.Count -eq 1) -and ($RequestedBindings.Count -eq 1)) "The realized port binding cardinality must equal one."
    foreach ($Binding in @($RealizedBindings[0], $RequestedBindings[0])) {
        Assert-True ([string]$Binding.HostIp -ceq "127.0.0.1") "The realized port binding leaves loopback."
        Assert-True ([string]$Binding.HostPort -ceq [string]$Context.HttpPort) "The realized port differs from the approved HTTP port."
    }

    $NetworkChecks = New-Object System.Collections.Generic.List[object]
    foreach ($Spec in @(
        @($Context.NetworkName, $true, "internal"),
        @($Context.IngressNetworkName, $false, "ingress")
    )) {
        $NetworkProjection = (Invoke-NativeCapture "docker" @("network", "inspect", "--format", "{{json .Internal}}|{{.Driver}}|{{json .Options}}|{{json .Labels}}", [string]$Spec[0]) ("realized-network-" + [string]$Spec[2]) -NoLog).Text.Trim()
        $Parts = @($NetworkProjection.Split([char[]]@('|'), 4))
        Assert-True ($Parts.Count -eq 4) "The realized network projection is malformed."
        $Internal = $Parts[0] | ConvertFrom-Json
        $Driver = $Parts[1]
        $Options = $Parts[2] | ConvertFrom-Json
        $Labels = $Parts[3] | ConvertFrom-Json
        $SafeOptions = ConvertTo-SafeRuntimeNetworkOptions $Options
        $OptionsMatch = Test-ExactRuntimeNetworkOptions $Options $Context.ExpectedNetworkOptions
        $LabelsMatch = (($null -ne $Labels) -and ($Labels.'com.docker.compose.project' -ceq $Context.ProjectName) -and ($Labels.'dssc.semantic-treehouse.project' -ceq $Context.ProjectName) -and ($Labels.'dssc.semantic-treehouse.upstream-commit' -ceq $Context.Commit) -and ($Labels.'dssc.semantic-treehouse.runtime-contract' -ceq "v1") -and ($Labels.'dssc.semantic-treehouse.network-role' -ceq [string]$Spec[2]))
        $NetworkChecks.Add([PSCustomObject]@{
            Name = [string]$Spec[0]
            Role = [string]$Spec[2]
            ExpectedInternal = [bool]$Spec[1]
            Internal = [bool]$Internal
            Driver = $Driver
            Options = $Options
            SafeOptions = $SafeOptions
            OptionsMatch = $OptionsMatch
            LabelsMatch = $LabelsMatch
        })
    }

    $NetworkOptionRows = @($NetworkChecks | ForEach-Object {
        [ordered]@{
            name = $_.Name
            role = $_.Role
            internal = $_.Internal
            driver = $_.Driver
            options = $_.SafeOptions
            options_match = [bool]$_.OptionsMatch
        }
    })
    $AllNetworkOptionsMatch = (($NetworkOptionRows.Count -eq 2) -and (@($NetworkOptionRows | Where-Object { -not $_.options_match }).Count -eq 0))
    $NetworkOptionsEvidence = [ordered]@{
        schema = "dssc.semantic-treehouse.runtime-network-options.v1"
        status = if ($AllNetworkOptionsMatch) { "PASS" } else { "REJECTED" }
        upstream_commit = $Context.Commit
        project_name = $Context.ProjectName
        lock_sha256 = Get-Sha256 $LockPath
        runtime_boundary_sha256 = Get-Sha256 $BoundaryPath
        compose_driver_options = "EMPTY"
        expected_options = $Context.ExpectedNetworkOptions
        networks = $NetworkOptionRows
    }
    Write-JsonFile $NetworkOptionsEvidencePath $NetworkOptionsEvidence
    Assert-EvidenceSanitized $NetworkOptionsEvidencePath $script:ValidatedEnvMap

    foreach ($NetworkCheck in $NetworkChecks) {
        Assert-True ($NetworkCheck.Internal -eq $NetworkCheck.ExpectedInternal) "The realized network internal flag differs from the lock."
        Assert-True ($NetworkCheck.Driver -ceq "bridge") "The realized network driver must be bridge."
        Assert-True $NetworkCheck.OptionsMatch "The realized network options differ from the exact approved two-key allowlist."
        Assert-True $NetworkCheck.LabelsMatch "The realized network ownership/role labels differ from the lock."
    }
    Add-RawLog "realized-ingress-boundary" ("PASS; binding=127.0.0.1:" + $Context.HttpPort + ":80; networks=internal+ingress; realized_network_options=exact-two-key; database_published_ports=0")
    return [ordered]@{
        status = "PASS"
        binding = ("127.0.0.1:" + $Context.HttpPort + ":80")
        network_settings_ports_programmed = $true
        host_config_binding_matches = $true
        application_networks = @($Context.NetworkName, $Context.IngressNetworkName)
        database_networks = @($Context.NetworkName)
        networks = $NetworkOptionRows
        realized_network_options_evidence_sha256 = Get-Sha256 $NetworkOptionsEvidencePath
        database_published_ports = 0
        application_outbound_access = $true
    }
}

function New-ProjectVolume {
    param($Context, [string]$Name, [string]$LogicalName)
    $Labels = Get-RequiredVolumeLabels $Context $LogicalName
    $Arguments = New-Object System.Collections.Generic.List[string]
    $Arguments.Add("volume")
    $Arguments.Add("create")
    foreach ($Key in $Labels.Keys) {
        $Arguments.Add("--label")
        $Arguments.Add($Key + "=" + $Labels[$Key])
    }
    $Arguments.Add($Name)
    Invoke-NativeCapture "docker" $Arguments.ToArray() ("create-volume-" + $LogicalName) | Out-Null
    $script:CreatedVolumes.Add($Name)
    Assert-VolumeLabels $Context $Name $LogicalName
}

function Remove-NewVolumesSafely {
    param($Context)
    $Failures = New-Object System.Collections.Generic.List[string]
    foreach ($Name in @($script:CreatedVolumes)) {
        $LogicalName = if ($Name -ceq $Context.AppVolumeName) { "sth-app-data" } elseif ($Name -ceq $Context.DbVolumeName) { "sth-db2-data" } else { $null }
        if ($null -eq $LogicalName) { continue }
        try {
            Assert-VolumeLabels $Context $Name $LogicalName
            $RemoveResult = Invoke-NativeCapture "docker" @("volume", "rm", $Name) ("cleanup-volume-" + $LogicalName) -AllowFailure
            if ($RemoveResult.ExitCode -ne 0) { $Failures.Add($LogicalName) }
        } catch {
            Add-RawLog "cleanup-volume-refused" $_.Exception.Message
            $Failures.Add($LogicalName)
        }
    }
    return @($Failures)
}

function Get-SafeImageProjection {
    param([string]$Reference, [string]$Name)
    $Projection = [ordered]@{}
    foreach ($Spec in @(
        @("os", "{{.Os}}"),
        @("architecture", "{{.Architecture}}"),
        @("user", "{{json .Config.User}}"),
        @("entrypoint", "{{json .Config.Entrypoint}}"),
        @("cmd", "{{json .Config.Cmd}}"),
        @("healthcheck", "{{json .Config.Healthcheck}}"),
        @("repo_digests", "{{json .RepoDigests}}")
    )) {
        $Result = Invoke-NativeCapture "docker" @("image", "inspect", "--format", $Spec[1], $Reference) ("image-" + $Name + "-" + $Spec[0])
        $Value = $Result.Text.Trim()
        if ($Spec[0] -in @("user", "entrypoint", "cmd", "healthcheck", "repo_digests")) {
            try { $Value = $Value | ConvertFrom-Json } catch { }
        }
        $Projection[$Spec[0]] = $Value
    }
    Assert-True ([string]$Projection.os -ceq "linux") "$Name image OS must be linux."
    Assert-True ([string]$Projection.architecture -ceq "amd64") "$Name image architecture must be amd64."
    $EntrypointText = ($Projection.entrypoint | ConvertTo-Json -Compress)
    $CmdText = ($Projection.cmd | ConvertTo-Json -Compress)
    if ($Name -ceq "sth") {
        Assert-True ($EntrypointText -match 'docker-php-entrypoint') "sth image Entrypoint differs from the reviewed runtime base."
        Assert-True ($CmdText -match 'frankenphp') "sth image Cmd differs from the reviewed runtime base."
        $EnvJson = (Invoke-NativeCapture "docker" @("image", "inspect", "--format", "{{json .Config.Env}}", $Reference) "image-sth-env-safe-projection" -NoLog).Text.Trim()
        try {
            $ImageEnvironment = $EnvJson | ConvertFrom-Json
        } catch {
            throw "sth image environment projection is not valid JSON."
        }
        $PhpIniMatches = @($ImageEnvironment | Where-Object { [string]$_ -ceq "PHP_INI_DIR=/usr/local/etc/php" })
        Assert-True ($PhpIniMatches.Count -eq 1) "sth image PHP_INI_DIR differs from /usr/local/etc/php."
        Add-RawLog "image-sth-php-ini-dir-safe-marker" "MATCH"
        $Projection["php_ini_dir"] = "/usr/local/etc/php"
    } else {
        Assert-True ($EntrypointText -match 'docker-entrypoint\.sh') "MariaDB Entrypoint differs from the reviewed image."
        Assert-True ($CmdText -match 'mariadbd') "MariaDB Cmd differs from the reviewed image."
    }
    $Projection["user_review"] = if (([string]$Projection.user -in @("", "root", "0", '""', '"root"', '"0"'))) { "ACCEPTED_KNOWN_REVIEW" } else { "EXPLICIT_NON_ROOT" }
    return $Projection
}

function Set-IsolatedComposeEnvironment {
    param($EnvMap)
    foreach ($ControlKey in @("COMPOSE_FILE", "COMPOSE_PROFILES", "COMPOSE_PROJECT_NAME", "COMPOSE_PATH_SEPARATOR", "COMPOSE_ENV_FILES", "COMPOSE_DISABLE_ENV_FILE", "DOCKER_DEFAULT_PLATFORM")) {
        [System.Environment]::SetEnvironmentVariable($ControlKey, $null, [System.EnvironmentVariableTarget]::Process)
    }
    foreach ($Key in $EnvMap.Keys) {
        [System.Environment]::SetEnvironmentVariable([string]$Key, [string]$EnvMap[$Key], [System.EnvironmentVariableTarget]::Process)
    }
}

function Assert-RuntimeContainsNoSecretValues {
    param($EnvMap)
    foreach ($File in @(Get-ChildItem -LiteralPath $RuntimeDir -File -Force)) {
        if ($File.FullName -ceq $EnvPath) { continue }
        $Text = Get-Content -Raw -Encoding UTF8 -LiteralPath $File.FullName -ErrorAction SilentlyContinue
        if ($null -eq $Text) { $Text = "" }
        foreach ($Key in @("APP_SECRET", "DB2_PASSWORD", "DB2_ROOT_PASSWORD", "DB2_TEST_DB_PASSWORD")) {
            $Value = [string]$EnvMap[$Key]
            Assert-True (-not $Text.Contains($Value)) "Runtime artifact contains a synthetic secret value: $($File.Name)"
        }
    }
}

function Protect-RuntimeArtifacts {
    param($EnvMap)
    $OperationalFiles = @($EnvPath, $OverlayPath, $InlineDockerfilePath)
    $ExplicitArtifacts = @(
        $RawLogPath, $BoundaryPath, $StatePath, $ResultEvidencePath, $BoundaryEvidencePath, $PrepareBoundaryEvidencePath, $NetworkOptionsEvidencePath,
        (Join-Path $RuntimeDir "build-sth.stdout.raw.log"), (Join-Path $RuntimeDir "build-sth.stderr.raw.log"),
        (Join-Path $RuntimeDir "pull-mariadb.stdout.raw.log"), (Join-Path $RuntimeDir "pull-mariadb.stderr.raw.log"),
        (Join-Path $RuntimeDir "up-sth.stdout.raw.log"), (Join-Path $RuntimeDir "up-sth.stderr.raw.log"),
        (Join-Path $RuntimeDir "migration-metadata.stdout.raw.log"), (Join-Path $RuntimeDir "migration-metadata.stderr.raw.log"),
        (Join-Path $RuntimeDir "migration-production.stdout.raw.log"), (Join-Path $RuntimeDir "migration-production.stderr.raw.log"),
        (Join-Path $RuntimeDir "failure-down-preserve-volumes.stdout.raw.log"), (Join-Path $RuntimeDir "failure-down-preserve-volumes.stderr.raw.log"),
        (Join-Path $RuntimeDir "smoke-root.response.raw.txt"), (Join-Path $RuntimeDir "smoke-api-environment-info.response.raw.txt")
    )
    foreach ($Path in $ExplicitArtifacts) {
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { continue }
        if ($Path -ceq $EnvPath) { continue }
        $Text = Get-Content -Raw -Encoding UTF8 -LiteralPath $Path -ErrorAction SilentlyContinue
        if ($null -eq $Text) { continue }
        $Safe = ConvertTo-SafeEvidenceText $Text
        foreach ($Key in @("APP_SECRET", "DB2_PASSWORD", "DB2_ROOT_PASSWORD", "DB2_TEST_DB_PASSWORD")) {
            $Value = [string]$EnvMap[$Key]
            if ($Value.Length -gt 0) { $Safe = $Safe.Replace($Value, "<redacted-secret>") }
        }
        $Safe = [regex]::Replace($Safe, '(?im)^(APP_SECRET|DB2_PASSWORD|DB2_ROOT_PASSWORD|DB2_TEST_DB_PASSWORD|STH_AI_GATEWAY_DEFAULT_API_KEY)=.*$', '$1=<redacted-secret>')
        if ($Safe -cne $Text) {
            Assert-True (-not ($OperationalFiles -contains $Path)) "Operational runtime config unexpectedly requires redaction: $([System.IO.Path]::GetFileName($Path))"
            Write-Utf8NoBom $Path $Safe
        }
    }
}

function Wait-ForDatabase {
    param($Context, [string[]]$ComposeArgs, [int]$TimeoutSeconds = 240)
    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $Deadline) {
        $IdResult = Invoke-NativeCapture "docker" ($ComposeArgs + @("ps", "-q", "sth-db2")) "db-container-id" -AllowFailure
        $Id = $IdResult.Text.Trim()
        if ($Id.Length -gt 0) {
            $Health = Invoke-NativeCapture "docker" @("inspect", "--format", "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}", $Id) "db-health" -AllowFailure
            if (($Health.ExitCode -eq 0) -and ($Health.Text.Trim() -ceq "healthy")) { return }
            if ($Health.Text.Trim() -ceq "unhealthy") { throw "MariaDB reported unhealthy." }
        }
        Start-Sleep -Seconds 3
    }
    throw "MariaDB readiness timed out after $TimeoutSeconds seconds."
}

function Invoke-SmokeGet {
    param([string]$Url, [string]$Name, [int]$TimeoutSeconds = 180)
    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $LastMessage = "no response"
    $RequestUri = New-Object System.Uri($Url)
    Assert-True ($RequestUri.Scheme -ceq "http") "$Name smoke must use HTTP loopback."
    Assert-True ($RequestUri.Host -ceq "127.0.0.1") "$Name smoke host must be 127.0.0.1."
    while ((Get-Date) -lt $Deadline) {
        try {
            $Request = [System.Net.HttpWebRequest]::Create($RequestUri)
            $Request.Method = "GET"
            $Request.AllowAutoRedirect = $false
            $Request.Timeout = 10000
            $Request.ReadWriteTimeout = 10000
            $Request.Proxy = $null
            $Response = $Request.GetResponse()
            try {
                $Reader = New-Object System.IO.StreamReader($Response.GetResponseStream(), [System.Text.Encoding]::UTF8)
                try { $Body = $Reader.ReadToEnd() } finally { $Reader.Dispose() }
                $StatusCode = [int]$Response.StatusCode
                $ContentType = [string]$Response.ContentType
                $Location = [string]$Response.Headers["Location"]
            } finally {
                $Response.Dispose()
            }
            Write-Utf8NoBom (Join-Path $RuntimeDir ($Name + ".response.raw.txt")) $Body
            $Accepted = (($StatusCode -ge 200) -and ($StatusCode -lt 300)) -or ($StatusCode -in @(301, 302, 303, 307, 308))
            if ($Accepted) {
                $LocationProjection = $null
                if ($StatusCode -in @(301, 302, 303, 307, 308)) {
                    Assert-True ($Location.Length -gt 0) "$Name redirect lacks Location."
                    $LocationUri = New-Object System.Uri($RequestUri, $Location)
                    Assert-True ($LocationUri.Scheme -ceq "http") "$Name redirect must stay on HTTP loopback."
                    Assert-True ($LocationUri.Host -in @("127.0.0.1", "localhost")) "$Name redirect leaves loopback."
                    Assert-True ($LocationUri.Port -eq $RequestUri.Port) "$Name redirect changes the approved port."
                    $LocationProjection = [ordered]@{ scheme = $LocationUri.Scheme; host = $LocationUri.Host; port = $LocationUri.Port; path = $LocationUri.AbsolutePath }
                }
                return [ordered]@{
                    url = $Url
                    status_code = $StatusCode
                    redirect_followed = $false
                    location = $LocationProjection
                    content_type = $ContentType
                    response_bytes = [System.Text.Encoding]::UTF8.GetByteCount($Body)
                    response_sha256 = (Get-Sha256 (Join-Path $RuntimeDir ($Name + ".response.raw.txt")))
                }
            }
            $LastMessage = "HTTP " + $StatusCode
        } catch {
            if (($_.Exception -is [System.Net.WebException]) -and ($null -ne $_.Exception.Response)) {
                $LastMessage = "HTTP " + [int]$_.Exception.Response.StatusCode
                $_.Exception.Response.Dispose()
            } else {
                $LastMessage = $_.Exception.Message
            }
        }
        Start-Sleep -Seconds 3
    }
    throw "$Name smoke GET failed: $LastMessage"
}

function Invoke-LocalReviewLoginSmoke {
    param([string]$BaseUrl)
    Assert-True ($null -ne $script:ValidatedEnvMap) "Local-review login smoke requires a validated synthetic env."
    Assert-True ([string]$script:ValidatedEnvMap["APP_ENV"] -ceq "prod") "Local-review login smoke must run with APP_ENV=prod."
    Assert-True ([string]$script:ValidatedEnvMap["STH_LOCAL_REVIEW_LOGIN"] -ceq "1") "Local-review login smoke requires the explicit opt-in value 1."
    $BaseUri = New-Object System.Uri($BaseUrl)
    Assert-True (($BaseUri.Scheme -ceq "http") -and ($BaseUri.Host -ceq "127.0.0.1")) "Local-review login smoke must use HTTP loopback."
    $Cookies = New-Object System.Net.CookieContainer

    $LoginUri = New-Object System.Uri($BaseUri, "/api/security/dev_login/admin")
    $LoginRequest = [System.Net.HttpWebRequest]::Create($LoginUri)
    $LoginRequest.Method = "GET"
    $LoginRequest.AllowAutoRedirect = $false
    $LoginRequest.Timeout = 15000
    $LoginRequest.ReadWriteTimeout = 15000
    $LoginRequest.Proxy = $null
    $LoginRequest.CookieContainer = $Cookies
    try {
        $LoginResponse = $LoginRequest.GetResponse()
        try {
            $LoginStatus = [int]$LoginResponse.StatusCode
            $LoginLocation = [string]$LoginResponse.Headers["Location"]
        } finally {
            $LoginResponse.Dispose()
        }
    } catch {
        $LoginFailureStatus = if (($_.Exception -is [System.Net.WebException]) -and ($null -ne $_.Exception.Response)) { [int]$_.Exception.Response.StatusCode } else { 0 }
        throw ("Explicit local-review admin login request failed; http_status=" + $LoginFailureStatus + ".")
    }
    Assert-True ($LoginStatus -in @(301, 302, 303, 307, 308)) "Explicit local-review admin login must return a redirect."
    Assert-True ($LoginLocation.Length -gt 0) "Explicit local-review admin login redirect lacks Location."
    $LoginRedirectUri = New-Object System.Uri($LoginUri, $LoginLocation)
    Assert-True (($LoginRedirectUri.Scheme -ceq "http") -and ($LoginRedirectUri.Host -in @("127.0.0.1", "localhost")) -and ($LoginRedirectUri.Port -eq $BaseUri.Port)) "Explicit local-review admin login redirect leaves the approved loopback origin."

    $AccountUri = New-Object System.Uri($BaseUri, "/api/security/account_info")
    $AccountRequest = [System.Net.HttpWebRequest]::Create($AccountUri)
    $AccountRequest.Method = "GET"
    $AccountRequest.AllowAutoRedirect = $false
    $AccountRequest.Timeout = 15000
    $AccountRequest.ReadWriteTimeout = 15000
    $AccountRequest.Proxy = $null
    $AccountRequest.CookieContainer = $Cookies
    try {
        $AccountResponse = $AccountRequest.GetResponse()
        try {
            $AccountStatus = [int]$AccountResponse.StatusCode
            $Reader = New-Object System.IO.StreamReader($AccountResponse.GetResponseStream(), [System.Text.Encoding]::UTF8)
            try { $AccountBody = $Reader.ReadToEnd() } finally { $Reader.Dispose() }
        } finally {
            $AccountResponse.Dispose()
        }
    } catch {
        $AccountFailureStatus = if (($_.Exception -is [System.Net.WebException]) -and ($null -ne $_.Exception.Response)) { [int]$_.Exception.Response.StatusCode } else { 0 }
        throw ("Cookie-aware local-review account verification failed; http_status=" + $AccountFailureStatus + ".")
    }
    Assert-True ($AccountStatus -eq 200) "Cookie-aware local-review account verification must return HTTP 200."
    try { $Account = $AccountBody | ConvertFrom-Json } catch { throw "Local-review account verification returned invalid JSON." }
    Assert-True ([string]$Account.id -ceq "admin") "Local-review login did not authenticate the fixed admin account id."
    Assert-True ([string]$Account.username -ceq "admin") "Local-review login did not authenticate the fixed admin username."
    $Roles = @($Account.roles | ForEach-Object { [string]$_ })
    Assert-True ($Roles -contains "ROLE_ADMINISTRATOR") "Local-review admin session lacks ROLE_ADMINISTRATOR."

    return [ordered]@{
        name = "local-review-admin-login"
        login_path = "/api/security/dev_login/admin"
        login_status_code = $LoginStatus
        login_redirect = [ordered]@{
            scheme = $LoginRedirectUri.Scheme
            host = $LoginRedirectUri.Host
            port = $LoginRedirectUri.Port
            path = $LoginRedirectUri.AbsolutePath
        }
        account_info_path = "/api/security/account_info"
        account_info_status_code = $AccountStatus
        account_id = "admin"
        account_username = "admin"
        administrator_role_present = $true
        cookie_aware = $true
        cookie_values_recorded = $false
        client_session_material_persisted = $false
        app_env = "prod"
        explicit_opt_in = $true
        json_login_policy = "dev-only-unchanged-static-hash-verified"
    }
}

function Invoke-FailureDown {
    param($Context, [string[]]$ComposeArgs)
    $script:CleanupSummary.attempted = $true
    if ($script:UpAttempted -and $script:ComposeReady) {
        $DownResult = Invoke-BoundedNative "docker" ($ComposeArgs + @("down")) "failure-down-preserve-volumes" 180 -AllowFailure
        $script:CleanupSummary.compose_down_exit_code = [int]$DownResult.ExitCode
    }
    $RemoveFailures = @(Remove-NewVolumesSafely $Context)
    $script:CleanupSummary.volume_remove_failures = $RemoveFailures

    try {
        $ProjectContainers = @((Invoke-NativeCapture "docker" @("ps", "-a", "--filter", ("label=com.docker.compose.project=" + $Context.ProjectName), "--format", "{{.ID}}") "cleanup-verify-project-containers" -NoLog).Text -split "`r?`n" | Where-Object { $_ })
        $NamedContainers = @()
        foreach ($Name in @(($Context.ProjectName + "-sth"), ($Context.ProjectName + "-sth-db2"))) {
            $Inspect = Invoke-NativeCapture "docker" @("container", "inspect", "--format", "{{.Id}}", $Name) ("cleanup-verify-container-" + $Name) -AllowFailure -NoLog
            if ($Inspect.ExitCode -eq 0) { $NamedContainers += $Name }
        }
        $ProjectNetworks = @((Invoke-NativeCapture "docker" @("network", "ls", "--filter", ("label=com.docker.compose.project=" + $Context.ProjectName), "--format", "{{.Name}}") "cleanup-verify-project-networks" -NoLog).Text -split "`r?`n" | Where-Object { $_ })
        $NamedNetworks = @()
        foreach ($Name in @($Context.NetworkName, $Context.IngressNetworkName)) {
            $Inspect = Invoke-NativeCapture "docker" @("network", "inspect", "--format", "{{.Id}}", $Name) ("cleanup-verify-network-" + $Name) -AllowFailure -NoLog
            if ($Inspect.ExitCode -eq 0) { $NamedNetworks += $Name }
        }
        $ProjectVolumes = @((Invoke-NativeCapture "docker" @("volume", "ls", "--filter", ("label=com.docker.compose.project=" + $Context.ProjectName), "--format", "{{.Name}}") "cleanup-verify-project-volumes" -NoLog).Text -split "`r?`n" | Where-Object { $_ })
        $NamedVolumes = @()
        foreach ($Name in @($Context.AppVolumeName, $Context.DbVolumeName)) {
            $Inspect = Invoke-NativeCapture "docker" @("volume", "inspect", "--format", "{{.Name}}", $Name) ("cleanup-verify-volume-" + $Name) -AllowFailure -NoLog
            if ($Inspect.ExitCode -eq 0) { $NamedVolumes += $Name }
        }
        $script:CleanupSummary.remaining_project_containers = $ProjectContainers.Count
        $script:CleanupSummary.remaining_named_containers = $NamedContainers.Count
        $script:CleanupSummary.remaining_project_networks = $ProjectNetworks.Count
        $script:CleanupSummary.remaining_named_networks = $NamedNetworks.Count
        $script:CleanupSummary.remaining_project_volumes = $ProjectVolumes.Count
        $script:CleanupSummary.remaining_named_volumes = $NamedVolumes.Count
        $script:CleanupSummary.complete = (($ProjectContainers.Count -eq 0) -and ($NamedContainers.Count -eq 0) -and ($ProjectNetworks.Count -eq 0) -and ($NamedNetworks.Count -eq 0) -and ($ProjectVolumes.Count -eq 0) -and ($NamedVolumes.Count -eq 0) -and ($RemoveFailures.Count -eq 0) -and (($null -eq $script:CleanupSummary.compose_down_exit_code) -or ($script:CleanupSummary.compose_down_exit_code -eq 0)))
    } catch {
        $script:CleanupSummary.verification_error = ConvertTo-SafeRuntimeText $_.Exception.Message
        $script:CleanupSummary.complete = $false
        try { Add-RawLog "failure-cleanup-verification-error" $_.Exception.Message } catch { }
    }
    Add-RawLog "failure-cleanup-summary" ($script:CleanupSummary | ConvertTo-Json -Compress)
}

New-Item -ItemType Directory -Force -Path $RuntimeDir, $EvidenceDir | Out-Null
try {
    $ArtifactGuardContext = Get-LockContext
    if ($PrepareOnly) {
        Assert-True ((-not (Test-Path -LiteralPath $StatePath)) -and (-not (Test-Path -LiteralPath $PendingStatePath))) "PrepareOnly refuses an existing runtime state marker."
    }
    Assert-NoExistingRuntimeResourcesBeforeArtifactWrite $ArtifactGuardContext
} catch {
    Write-Error (ConvertTo-SafeRuntimeText $_.Exception.Message)
    exit 1
}
Write-Utf8NoBom $RawLogPath "Semantic Treehouse runtime wrapper raw log`n"

$Context = $null
$ComposeArgs = $null
try {
    $Context = Get-LockContext
    Assert-Checkout $Context
    $DockerBoundary = Assert-LocalDockerDaemon
    $EnvMap = Initialize-SyntheticEnv $Context
    $script:ValidatedEnvMap = $EnvMap
    Set-IsolatedComposeEnvironment $EnvMap
    $DockerfileText = New-InlineDockerfile $Context
    $RuntimeImages = New-Overlay $Context $DockerfileText
    $ComposeArgs = Get-ComposeArguments $Context
    $ConfigResult = Invoke-SensitiveNativeCapture "docker" ($ComposeArgs + @("config", "--format", "json")) "compose-config-sensitive-in-memory"
    Assert-True (-not [regex]::IsMatch([string]$ConfigResult.Stderr, '(?im)\bvariable\b.*\bis not set\b')) "Compose reported an unset-variable warning while rendering dockerfile_inline."
    $Config = $ConfigResult.Text | ConvertFrom-Json
    $Projection = Assert-ComposeBoundary $Context $RuntimeImages $Config $DockerfileText
    $BakeResult = Invoke-SensitiveNativeCapture "docker" ($ComposeArgs + @("build", "--print", "sth")) "compose-build-print-sensitive-in-memory"
    Assert-True (-not [regex]::IsMatch([string]$BakeResult.Stderr, '(?im)\bvariable\b.*\bis not set\b')) "Compose build --print reported an unset-variable warning."
    $BakePlan = $BakeResult.Text | ConvertFrom-Json
    $BakeProjection = Assert-BakePrintBoundary $BakePlan $DockerfileText
    foreach ($Key in $BakeProjection.Keys) { $Projection[$Key] = $BakeProjection[$Key] }
    $FinalBakeResult = Invoke-SensitiveNativeWithStdin "docker" @("buildx", "bake", "--print", "--file", "-") $BakeResult.Text "buildx-bake-final-print-sensitive-in-memory"
    Assert-True (-not [regex]::IsMatch([string]$FinalBakeResult.Stderr, '(?im)\bvariable\b.*\bis not set\b')) "Buildx Bake final print reported an unset-variable warning."
    $FinalBakePlan = $FinalBakeResult.Text | ConvertFrom-Json
    $FinalBakeProjection = Assert-FinalBakeBoundary $FinalBakePlan $DockerfileText
    foreach ($Key in $FinalBakeProjection.Keys) { $Projection[$Key] = $FinalBakeProjection[$Key] }
    $script:ComposeReady = $true

    $Boundary = [ordered]@{
        schema = "dssc.semantic-treehouse.runtime-boundary.v1"
        status = "PASS"
        prepare_only = [bool]$PrepareOnly
        lock_path = "tools/semantic-treehouse/upstream.lock.json"
        lock_sha256 = Get-Sha256 $LockPath
        upstream_commit = $Context.Commit
        project_name = $Context.ProjectName
        source_hash_count = @($Context.Lock.source_materialization.sha256.PSObject.Properties).Count
        compose_sha256 = Get-Sha256 $Context.ComposePath
        overlay_sha256 = Get-Sha256 $OverlayPath
        dockerfile_inline_sha256 = Get-Sha256 $InlineDockerfilePath
        synthetic_env_sha256 = Get-Sha256 $EnvPath
        synthetic_env_keys = @($EnvMap.Keys | Sort-Object)
        synthetic_secret_values_recorded = $false
        synthetic_env_storage = "private-runtime-only"
        docker = $DockerBoundary
        boundary = $Projection
        operations = [ordered]@{
            pull = 0
            build = 0
            up = 0
            container_create = 0
            volume_create = 0
            migration = 0
            smoke = 0
            derived_runtime_source_patch = 1
            build_print = 1
            buildx_bake_print = 1
        }
    }
    Write-JsonFile $BoundaryPath $Boundary
    $SelectedBoundaryEvidencePath = if ($PrepareOnly) { $PrepareBoundaryEvidencePath } else { $BoundaryEvidencePath }
    Write-JsonFile $SelectedBoundaryEvidencePath $Boundary
    Assert-EvidenceSanitized $SelectedBoundaryEvidencePath $EnvMap
    Assert-RuntimeContainsNoSecretValues $EnvMap

    if ($PrepareOnly) {
        Write-Output ("PrepareOnly PASS: " + $SelectedBoundaryEvidencePath)
        exit 0
    }

    Assert-FreshRuntimeResources $Context
    if (Test-Path -LiteralPath $NetworkOptionsEvidencePath -PathType Leaf) {
        Remove-Item -Force -LiteralPath $NetworkOptionsEvidencePath
    }
    foreach ($SuccessMarker in @($StatePath, $PendingStatePath)) {
        if (Test-Path -LiteralPath $SuccessMarker) { Remove-Item -Force -LiteralPath $SuccessMarker }
    }
    $script:FreshDeploymentStarted = $true
    New-ProjectVolume $Context $Context.AppVolumeName "sth-app-data"
    New-ProjectVolume $Context $Context.DbVolumeName "sth-db2-data"

    $BuildResult = Invoke-BoundedNative "docker" ($ComposeArgs + @("build", "--pull", "sth")) "build-sth" 1800
    $PullResult = Invoke-BoundedNative "docker" @("pull", "--platform", "linux/amd64", $RuntimeImages.DbImage) "pull-mariadb" 600
    $AppImage = Get-SafeImageProjection $RuntimeImages.AppImage "sth"
    $DbImage = Get-SafeImageProjection $RuntimeImages.DbImage "sth-db2"
    $ExpectedDbRepoDigest = "mariadb@" + $Context.ImageMap["mariadb:11.4"]
    Assert-True (@($DbImage.repo_digests) -contains $ExpectedDbRepoDigest) "MariaDB RepoDigests do not contain the locked linux/amd64 digest."

    $script:UpAttempted = $true
    Invoke-BoundedNative "docker" ($ComposeArgs + @("up", "--detach", "--no-build", "--pull", "never", "sth")) "up-sth" 300 | Out-Null
    $RealizedIngress = Assert-RealizedIngressBoundary $Context $ComposeArgs
    Wait-ForDatabase $Context $ComposeArgs
    Assert-True ($script:CreatedVolumes.Count -eq 2) "Production migration is allowed only with both volumes created by this invocation."
    Invoke-BoundedNative "docker" ($ComposeArgs + @("exec", "-T", "sth", "php", "bin/console", "--env=prod", "doctrine:migrations:sync-metadata-storage", "--no-interaction")) "migration-metadata" 300 | Out-Null
    Invoke-BoundedNative "docker" ($ComposeArgs + @("exec", "-T", "sth", "php", "bin/console", "--env=prod", "doctrine:migrations:migrate", "--no-interaction")) "migration-production" 600 | Out-Null

    $PendingState = [ordered]@{
        schema = "dssc.semantic-treehouse.runtime-state.v1"
        upstream_commit = $Context.Commit
        project_name = $Context.ProjectName
        lock_sha256 = Get-Sha256 $LockPath
        runtime_boundary_sha256 = Get-Sha256 $BoundaryPath
        compose_sha256 = Get-Sha256 $Context.ComposePath
        overlay_sha256 = Get-Sha256 $OverlayPath
        synthetic_env_sha256 = Get-Sha256 $EnvPath
        volumes = @($Context.AppVolumeName, $Context.DbVolumeName)
        bind_address = "127.0.0.1"
        http_port = $Context.HttpPort
        network_topology = "dual-network-app-ingress"
        internal_network = $Context.NetworkName
        ingress_network = $Context.IngressNetworkName
        application_outbound_access = $true
        local_review_login = [ordered]@{
            enabled = $true
            runtime_flag = "STH_LOCAL_REVIEW_LOGIN"
            runtime_value = "1"
            dev_login_policy = "dev-or-explicit-admin-local-review"
            json_login_policy = "dev-only-unchanged"
            security_controller_source_sha256 = $script:SecurityControllerPatchProjection.source_sha256
            security_controller_patched_sha256 = $script:SecurityControllerPatchProjection.patched_sha256
        }
        application_volume_target = "/app/var/user_data"
        realized_ingress = $RealizedIngress
        deployment = "PENDING_SMOKE"
        first_migration = "PASS"
        production_migration = "PASS"
        smoke = "PENDING"
        root_smoke = "PENDING"
        api_smoke = "PENDING"
        local_review_login_smoke = "PENDING"
        success_state = $false
    }
    Write-JsonFile $PendingStatePath $PendingState
    $RootSmoke = Invoke-SmokeGet ("http://127.0.0.1:" + $Context.HttpPort + "/") "smoke-root"
    $ApiSmoke = Invoke-SmokeGet ("http://127.0.0.1:" + $Context.HttpPort + "/api/environment/info") "smoke-api-environment-info"
    $LocalReviewLoginSmoke = Invoke-LocalReviewLoginSmoke ("http://127.0.0.1:" + $Context.HttpPort + "/")
    $PendingState.deployment = "PASS"
    $PendingState.smoke = "PASS"
    $PendingState.root_smoke = "PASS"
    $PendingState.api_smoke = "PASS"
    $PendingState.local_review_login_smoke = "PASS"
    $PendingState.success_state = $true
    Write-JsonFile $PendingStatePath $PendingState
    Assert-True (-not (Test-Path -LiteralPath $StatePath)) "A stale runtime success state appeared during the deployment."
    [System.IO.File]::Move($PendingStatePath, $StatePath)

    $Result = [ordered]@{
        schema = "dssc.semantic-treehouse.runtime-up.v1"
        status = "PASS"
        upstream_commit = $Context.Commit
        project_name = $Context.ProjectName
        lock_sha256 = Get-Sha256 $LockPath
        runtime_boundary_sha256 = Get-Sha256 $BoundaryPath
        target_service = "sth"
        dependency_closure = @("sth", "sth-db2")
        fresh_volumes_created = @($script:CreatedVolumes)
        existing_resources_reused = $false
        production_migration = "PASS"
        realized_ingress = $RealizedIngress
        local_review_login = [ordered]@{
            enabled = $true
            scope = "loopback-fake-admin-devLogin-only"
            app_env = "prod"
            json_login_policy = "dev-only-unchanged"
            security_controller_patch = $script:SecurityControllerPatchProjection
        }
        application_volume = [ordered]@{
            name = $Context.AppVolumeName
            target = "/app/var/user_data"
        }
        app_image = $AppImage
        database_image = $DbImage
        smoke = @($RootSmoke, $ApiSmoke, $LocalReviewLoginSmoke)
        first_error = $null
        success_runtime_retained = $true
        realized_network_options_evidence = [ordered]@{
            path = "build/evidence/treehouse/runtime-network-options.json"
            sha256 = Get-Sha256 $NetworkOptionsEvidencePath
        }
        raw_log_path = $RawLogEvidencePath
    }
    Write-JsonFile $ResultEvidencePath $Result
    Assert-EvidenceSanitized $ResultEvidencePath $EnvMap
    Assert-RuntimeContainsNoSecretValues $EnvMap
    Write-Output ("Treehouse runtime PASS: " + $ResultEvidencePath)
    exit 0
} catch {
    $CaughtMessage = if (($null -ne $_.Exception) -and (-not [string]::IsNullOrWhiteSpace([string]$_.Exception.Message))) { [string]$_.Exception.Message } else { "Runtime up failed without an exception message." }
    $CaughtStep = if (-not [string]::IsNullOrWhiteSpace([string]$script:LastFailureStep)) { [string]$script:LastFailureStep } else { "runtime-up" }
    $CaughtExitCode = if ($null -ne $script:LastNativeExitCode) { [int]$script:LastNativeExitCode } else { 1 }
    Record-FirstError $CaughtStep $CaughtMessage $CaughtExitCode
    if (($null -ne $Context) -and ($null -ne $ComposeArgs) -and (-not $PrepareOnly)) {
        try { Invoke-FailureDown $Context $ComposeArgs } catch { try { Add-RawLog "post-failure-cleanup-secondary-error" $_.Exception.Message } catch { } }
    }
    if ($script:FreshDeploymentStarted) {
        foreach ($SuccessMarker in @($StatePath, $PendingStatePath)) {
            try { if (Test-Path -LiteralPath $SuccessMarker) { Remove-Item -Force -LiteralPath $SuccessMarker } } catch { try { Add-RawLog "post-failure-state-cleanup-secondary-error" $_.Exception.Message } catch { } }
        }
    }
    $Failure = [ordered]@{
        schema = "dssc.semantic-treehouse.runtime-up.v1"
        status = "ERROR"
        prepare_only = [bool]$PrepareOnly
        upstream_commit = if ($null -ne $Context) { $Context.Commit } else { $null }
        project_name = if ($null -ne $Context) { $Context.ProjectName } else { $null }
        lock_sha256 = if (Test-Path -LiteralPath $LockPath -PathType Leaf) { Get-Sha256 $LockPath } else { $null }
        runtime_boundary_sha256 = if (Test-Path -LiteralPath $BoundaryPath -PathType Leaf) { Get-Sha256 $BoundaryPath } else { $null }
        first_error = $script:FirstError
        workload_started = [bool]$script:UpAttempted
        new_volumes_created = @($script:CreatedVolumes)
        failure_down_used_volumes_flag = $false
        cleanup = $script:CleanupSummary
        realized_network_options_evidence = if (Test-Path -LiteralPath $NetworkOptionsEvidencePath -PathType Leaf) {
            [ordered]@{
                path = "build/evidence/treehouse/runtime-network-options.json"
                sha256 = Get-Sha256 $NetworkOptionsEvidencePath
            }
        } else { $null }
        raw_log_path = $RawLogEvidencePath
    }
    Write-JsonFile $ResultEvidencePath $Failure
    if (Test-Path -LiteralPath $EnvPath -PathType Leaf) {
        try {
            $FailureEnvMap = Read-SyntheticEnv $EnvPath
            Protect-RuntimeArtifacts $FailureEnvMap
            Assert-EvidenceSanitized $ResultEvidencePath $FailureEnvMap
            Assert-RuntimeContainsNoSecretValues $FailureEnvMap
        } catch {
            try { Add-RawLog "post-failure-scrub-secondary-error" $_.Exception.Message } catch { }
        }
    }
    Write-Error (ConvertTo-SafeRuntimeText $CaughtMessage)
    exit 1
}
