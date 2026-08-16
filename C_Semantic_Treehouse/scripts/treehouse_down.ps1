[CmdletBinding()]
param()

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
$BoundaryPath = Join-Path $RuntimeDir "runtime-boundary.json"
$StatePath = Join-Path $RuntimeDir "runtime-state.json"
$RawPath = Join-Path $RuntimeDir "down.raw.log"
$EvidencePath = Join-Path $EvidenceDir "runtime-down.json"
$NetworkOptionsEvidencePath = Join-Path $EvidenceDir "runtime-network-options.json"

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Get-Sha256 {
    param([string]$Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Get-StringSha256 {
    param([string]$Text)
    $Hasher = [System.Security.Cryptography.SHA256]::Create()
    try {
        $Bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        return (($Hasher.ComputeHash($Bytes) | ForEach-Object { $_.ToString("x2") }) -join '')
    } finally {
        $Hasher.Dispose()
    }
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Text)
    $Parent = Split-Path -Parent $Path
    if (($Parent.Length -gt 0) -and (-not (Test-Path -LiteralPath $Parent -PathType Container))) { New-Item -ItemType Directory -Force -Path $Parent | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Text, (New-Object System.Text.UTF8Encoding($false)))
}

function Write-JsonFile {
    param([string]$Path, $Value)
    $Parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $Parent -PathType Container)) { New-Item -ItemType Directory -Force -Path $Parent | Out-Null }
    Write-Utf8NoBom $Path (($Value | ConvertTo-Json -Depth 20) + "`n")
}

function Resolve-ChildPath {
    param([string]$Parent, [string]$Relative)
    Assert-True (-not [System.IO.Path]::IsPathRooted($Relative)) "Locked path must be relative."
    Assert-True ($Relative -notmatch '(^|[\\/])\.\.([\\/]|$)') "Locked path contains traversal."
    $ParentFull = [System.IO.Path]::GetFullPath($Parent).TrimEnd('\', '/')
    $Candidate = [System.IO.Path]::GetFullPath((Join-Path $Parent $Relative))
    Assert-True ($Candidate.StartsWith($ParentFull + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) "Locked path escapes repository."
    return $Candidate
}

function Invoke-NativeCapture {
    param([string]$File, [string[]]$Arguments, [string]$Step, [switch]$AllowFailure, [switch]$NoLog)
    $PreviousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $Lines = & $File @Arguments 2>&1
        $Code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $PreviousPreference }
    $Text = (($Lines | ForEach-Object { $_.ToString() }) -join "`n").Trim()
    if (-not $NoLog) { [System.IO.File]::AppendAllText($RawPath, ("`r`n===== " + $Step + " =====`r`n" + (Protect-Message $Text) + "`n"), (New-Object System.Text.UTF8Encoding($false))) }
    if (($Code -ne 0) -and (-not $AllowFailure)) { throw "$Step failed with exit code $Code." }
    return [PSCustomObject]@{ ExitCode = $Code; Text = $Text }
}

function ConvertTo-CommandLineArgument {
    param([string]$Value)
    if ($Value.Length -eq 0) { return '""' }
    if ($Value -notmatch '[\s"]') { return $Value }
    return '"' + $Value.Replace('"', '\"') + '"'
}

function Invoke-BoundedDocker {
    param([string[]]$Arguments, [string]$Step, [int]$TimeoutSeconds)
    $OutPath = Join-Path $RuntimeDir ($Step + ".stdout.raw.log")
    $ErrPath = Join-Path $RuntimeDir ($Step + ".stderr.raw.log")
    Remove-Item -LiteralPath $OutPath, $ErrPath -Force -ErrorAction SilentlyContinue
    $ArgumentLine = (($Arguments | ForEach-Object { ConvertTo-CommandLineArgument $_ }) -join ' ')
    $Process = Start-Process -FilePath "docker" -ArgumentList $ArgumentLine -RedirectStandardOutput $OutPath -RedirectStandardError $ErrPath -WindowStyle Hidden -PassThru
    $TimedOut = -not $Process.WaitForExit($TimeoutSeconds * 1000)
    if ($TimedOut) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        $Process.WaitForExit()
    }
    $Stdout = if (Test-Path -LiteralPath $OutPath) { Get-Content -Raw -Encoding UTF8 -LiteralPath $OutPath } else { "" }
    $Stderr = if (Test-Path -LiteralPath $ErrPath) { Get-Content -Raw -Encoding UTF8 -LiteralPath $ErrPath } else { "" }
    $SafeStdout = Protect-Message $Stdout
    $SafeStderr = Protect-Message $Stderr
    Write-Utf8NoBom $OutPath $SafeStdout
    Write-Utf8NoBom $ErrPath $SafeStderr
    [System.IO.File]::AppendAllText($RawPath, ("`r`n===== " + $Step + " =====`r`n" + $SafeStdout + "`n" + $SafeStderr + "`n"), (New-Object System.Text.UTF8Encoding($false)))
    if ($TimedOut) { throw "$Step timed out after $TimeoutSeconds seconds." }
    if ($Process.ExitCode -ne 0) { throw "$Step failed with exit code $($Process.ExitCode)." }
}

function Get-ExpectedLabels {
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

function Get-ExpectedContainerLabels {
    param([string]$ProjectName, [string]$Commit, [string]$Service)
    return [ordered]@{
        "com.docker.compose.project" = $ProjectName
        "com.docker.compose.service" = $Service
        "dssc.semantic-treehouse.project" = $ProjectName
        "dssc.semantic-treehouse.upstream-commit" = $Commit
        "dssc.semantic-treehouse.runtime-contract" = "v1"
    }
}

function Test-ContainerLabels {
    param($Actual, $Expected)
    if ($null -eq $Actual) { return $false }
    $ActualProperties = @($Actual.PSObject.Properties)
    $ActualNames = @($ActualProperties | ForEach-Object { [string]$_.Name })
    $ExpectedNames = @($Expected.Keys | ForEach-Object { [string]$_ })
    if ($ExpectedNames.Count -ne 5) { return $false }
    foreach ($Key in $ExpectedNames) {
        $Matches = @($ActualProperties | Where-Object { ([string]$_.Name) -ceq $Key })
        if (($Matches.Count -ne 1) -or (-not ($Matches[0].Value -is [string])) -or ([string]$Matches[0].Value -cne [string]$Expected[$Key])) { return $false }
    }
    $ActualDsscNames = @($ActualNames | Where-Object { $_.StartsWith("dssc.semantic-treehouse.", [System.StringComparison]::OrdinalIgnoreCase) } | Sort-Object)
    $ExpectedDsscNames = @($ExpectedNames | Where-Object { $_.StartsWith("dssc.semantic-treehouse.", [System.StringComparison]::Ordinal) } | Sort-Object)
    $ManagedKey = "dssc.semantic-treehouse.managed"
    foreach ($ActualDsscName in $ActualDsscNames) {
        if ((-not ($ExpectedDsscNames -ccontains $ActualDsscName)) -and ($ActualDsscName -cne $ManagedKey)) { return $false }
    }
    $ManagedMatches = @($ActualProperties | Where-Object { ([string]$_.Name) -ceq $ManagedKey })
    if (($ManagedMatches.Count -eq 1) -and ((-not ($ManagedMatches[0].Value -is [string])) -or ([string]$ManagedMatches[0].Value -cne "true"))) { return $false }
    return (($ManagedMatches.Count -le 1) -and ($ActualDsscNames.Count -eq ($ExpectedDsscNames.Count + $ManagedMatches.Count)))
}

function Get-VolumeState {
    param($Context, [string]$Name, [string]$LogicalName)
    $Inspect = Invoke-NativeCapture "docker" @("volume", "inspect", "--format", "{{json .Labels}}", $Name) ("volume-" + $LogicalName) -AllowFailure -NoLog
    if ($Inspect.ExitCode -ne 0) { return [ordered]@{ name = $Name; logical_name = $LogicalName; present = $false; labels_match = $false; labels_sha256 = $null } }
    $Actual = $Inspect.Text | ConvertFrom-Json
    Assert-True ($null -ne $Actual) "Volume label projection is null: $Name"
    $Expected = Get-ExpectedLabels $Context $LogicalName
    $Match = (@($Actual.PSObject.Properties | ForEach-Object { $_.Name }).Count -eq $Expected.Count)
    foreach ($Key in $Expected.Keys) {
        if ((-not ($Actual.PSObject.Properties.Name -contains $Key)) -or ([string]$Actual.$Key -cne [string]$Expected[$Key])) { $Match = $false }
    }
    return [ordered]@{ name = $Name; logical_name = $LogicalName; present = $true; labels_match = $Match; labels_sha256 = Get-StringSha256 $Inspect.Text }
}

function Get-ProjectVolumeNames {
    param([string]$ProjectName)
    return @((Invoke-NativeCapture "docker" @("volume", "ls", "--filter", ("label=com.docker.compose.project=" + $ProjectName), "--format", "{{.Name}}") "project-volumes").Text -split "`r?`n" | Where-Object { $_ } | Sort-Object)
}

function Get-PropertyNames {
    param($Value)
    if ($null -eq $Value) { return @() }
    return @($Value.PSObject.Properties | ForEach-Object { $_.Name })
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
        $Name = Protect-Message ([string]$Property.Name)
        $Projection[$Name] = Protect-Message ([string]$Property.Value)
    }
    return $Projection
}

function Get-NetworkState {
    param($Context, [string]$Name, [bool]$ExpectedInternal, [string]$Role)
    $Inspect = Invoke-NativeCapture "docker" @("network", "inspect", "--format", "{{json .Internal}}|{{.Driver}}|{{json .Options}}|{{json .Labels}}", $Name) ("network-" + $Role) -AllowFailure -NoLog
    if ($Inspect.ExitCode -ne 0) {
        return [ordered]@{ name = $Name; role = $Role; present = $false; internal = $null; driver = $null; options = $null; options_match = $false; labels_match = $false; boundary_match = $false }
    }
    $Parts = @($Inspect.Text.Split([char[]]@('|'), 4))
    Assert-True ($Parts.Count -eq 4) "Runtime network safe projection is malformed."
    $Internal = [bool]($Parts[0] | ConvertFrom-Json)
    $Driver = [string]$Parts[1]
    $Options = $Parts[2] | ConvertFrom-Json
    $Labels = $Parts[3] | ConvertFrom-Json
    $SafeOptions = ConvertTo-SafeRuntimeNetworkOptions $Options
    $OptionsMatch = Test-ExactRuntimeNetworkOptions $Options $Context.ExpectedNetworkOptions
    $LabelsMatch = (
        ($null -ne $Labels) -and
        ([string]$Labels.'com.docker.compose.project' -ceq $Context.ProjectName) -and
        ([string]$Labels.'dssc.semantic-treehouse.project' -ceq $Context.ProjectName) -and
        ([string]$Labels.'dssc.semantic-treehouse.upstream-commit' -ceq $Context.Commit) -and
        ([string]$Labels.'dssc.semantic-treehouse.runtime-contract' -ceq "v1") -and
        ([string]$Labels.'dssc.semantic-treehouse.network-role' -ceq $Role)
    )
    $BoundaryMatch = (($Internal -eq $ExpectedInternal) -and ($Driver -ceq "bridge") -and $OptionsMatch -and $LabelsMatch)
    return [ordered]@{ name = $Name; role = $Role; present = $true; internal = $Internal; driver = $Driver; options = $SafeOptions; options_match = $OptionsMatch; labels_match = $LabelsMatch; boundary_match = $BoundaryMatch }
}

function Protect-Message {
    param([string]$Message)
    if ($null -eq $Message) { return "" }
    $Safe = $Message
    foreach ($Sensitive in @($RootDir, $RuntimeDir, $env:USERPROFILE, $env:HOME)) {
        if (($null -ne $Sensitive) -and ([string]$Sensitive).Length -gt 0) { $Safe = $Safe.Replace([string]$Sensitive, "<redacted-path>") }
    }
    foreach ($Name in @($env:USERNAME, $env:USER)) {
        if (($null -ne $Name) -and ([string]$Name).Length -ge 3) { $Safe = $Safe.Replace([string]$Name, "<redacted-user>") }
    }
    if (Test-Path -LiteralPath $EnvPath -PathType Leaf) {
        foreach ($Line in (Get-Content -Encoding UTF8 -LiteralPath $EnvPath)) {
            $Index = $Line.IndexOf('=')
            if ($Index -gt 0) {
                $Key = $Line.Substring(0, $Index)
                $Value = $Line.Substring($Index + 1)
                if (($Key -match '(?:SECRET|PASSWORD|API_KEY)') -and ($Value.Length -gt 0)) { $Safe = $Safe.Replace($Value, "<redacted-secret>") }
            }
        }
    }
    $Safe = [regex]::Replace($Safe, '(?im)^(APP_SECRET|DB2_PASSWORD|DB2_ROOT_PASSWORD|DB2_TEST_DB_PASSWORD|STH_AI_GATEWAY_DEFAULT_API_KEY)=.*$', '$1=<redacted-secret>')
    $Safe = [regex]::Replace($Safe, '(?i)[A-Z]:\\Users\\[^\\\s"'']+', '<redacted-home>')
    return [regex]::Replace($Safe, '(?i)/(?:home/[^/\s"'']+|root)(?:/[^\s"'']*)?', '<redacted-home>')
}

function Set-IsolatedComposeEnvironment {
    $Map = @{}
    foreach ($Line in (Get-Content -Encoding UTF8 -LiteralPath $EnvPath)) {
        if ($Line.Length -eq 0) { continue }
        $Index = $Line.IndexOf('=')
        Assert-True ($Index -gt 0) "Malformed synthetic env line."
        $Key = $Line.Substring(0, $Index)
        Assert-True ($Key -cmatch '^[A-Z][A-Z0-9_]*$') "Invalid synthetic env key."
        Assert-True (-not $Map.ContainsKey($Key)) "Duplicate synthetic env key."
        $Map[$Key] = $Line.Substring($Index + 1)
    }
    $Allowed = @("APP_ENV","APP_DEBUG","APP_SECRET","DB2_DBNAME","DB2_USER","DB2_PASSWORD","DB2_ROOT_PASSWORD","DB2_TEST_DB_PASSWORD","MAILER_DSN","SERVER_HOST_NAME","STH_FRONTEND_CONFIG","STH_GCS_PATH_PREFIX","STH_NOTIFICATIONS_ENABLED","STH_VALIDATOR_ENDPOINT","STH_JSON_VALIDATOR_ENDPOINT","STH_SHACL_VALIDATOR_ENDPOINT","STH_AI_GATEWAY_ENABLED","STH_AI_GATEWAY_ENDPOINT","STH_AI_GATEWAY_DEFAULT_MODEL_PROVIDER","STH_AI_GATEWAY_DEFAULT_MODEL","STH_AI_GATEWAY_DEFAULT_API_KEY")
    $Unexpected = @($Map.Keys | Where-Object { $_ -notin $Allowed })
    Assert-True (($Map.Count -eq $Allowed.Count) -and ($Unexpected.Count -eq 0)) "Synthetic env differs from its exact allowlist."
    foreach ($Control in @("COMPOSE_FILE","COMPOSE_PROFILES","COMPOSE_PROJECT_NAME","COMPOSE_PATH_SEPARATOR","COMPOSE_ENV_FILES","COMPOSE_DISABLE_ENV_FILE","DOCKER_DEFAULT_PLATFORM")) { [System.Environment]::SetEnvironmentVariable($Control, $null, "Process") }
    foreach ($Key in $Map.Keys) { [System.Environment]::SetEnvironmentVariable([string]$Key, [string]$Map[$Key], "Process") }
}

function Assert-EvidenceSafe {
    param([string]$Path)
    $Text = Get-Content -Raw -Encoding UTF8 -LiteralPath $Path
    foreach ($Sensitive in @($RootDir, $RuntimeDir, $env:USERPROFILE, $env:HOME)) {
        if (($null -ne $Sensitive) -and ([string]$Sensitive).Length -gt 0) { Assert-True (-not $Text.Contains([string]$Sensitive)) "Down evidence contains an absolute private path." }
    }
    if (Test-Path -LiteralPath $EnvPath -PathType Leaf) {
        foreach ($Line in (Get-Content -Encoding UTF8 -LiteralPath $EnvPath)) {
            $Index = $Line.IndexOf('=')
            if ($Index -gt 0) {
                $Key = $Line.Substring(0, $Index)
                $Value = $Line.Substring($Index + 1)
                if (($Key -match '(?:SECRET|PASSWORD|API_KEY)') -and ($Value.Length -gt 0)) { Assert-True (-not $Text.Contains($Value)) "Down evidence contains a synthetic secret." }
            }
        }
    }
    Assert-True (-not [regex]::IsMatch($Text, '(?m)^(?:APP_SECRET|DB2_PASSWORD|DB2_ROOT_PASSWORD|DB2_TEST_DB_PASSWORD|STH_AI_GATEWAY_DEFAULT_API_KEY)=')) "Down evidence contains env assignments."
    Assert-True (-not [regex]::IsMatch($Text, '(?i)[A-Z]:\\Users\\|/(?:home/[^/\s"'']+|root)(?:/|\b)')) "Down evidence contains a home/root absolute path."
}

New-Item -ItemType Directory -Force -Path $RuntimeDir, $EvidenceDir | Out-Null
Write-Utf8NoBom $RawPath "Semantic Treehouse exact-project down raw log.`n"
$ContainerRows = @()
$NamedContainerRows = @()
$ProjectNetworkRows = @()
$NetworksBefore = @()
$Before = @()
$AppPortBoundary = $null
$SuccessStateMarkerDetected = $false
$SuccessStateMarkerContextValid = $true
$SuccessStateMarkerValidationError = $null

try {
    Assert-True (Test-Path -LiteralPath $LockPath -PathType Leaf) "Upstream lock is missing."
    $Lock = Get-Content -Raw -Encoding UTF8 -LiteralPath $LockPath | ConvertFrom-Json
    Assert-True ($Lock.schema -eq "dssc.semantic-treehouse.upstream-lock.v1") "Unexpected upstream lock schema."
    $Commit = [string]$Lock.upstream.commit
    $ProjectName = [string]$Lock.compose.project_name
    Assert-True ($Commit -cmatch '^[0-9a-f]{40}$') "Invalid locked commit."
    $InternalNetworkName = [string]$Lock.runtime.network_name
    $IngressNetworkName = [string]$Lock.runtime.ingress_network_name
    $IngressServices = @($Lock.runtime.ingress_services)
    Assert-True ([string]$Lock.runtime.network_topology -ceq "dual-network-app-ingress") "Unexpected runtime network topology."
    Assert-True (($InternalNetworkName -cmatch '^[a-z0-9][a-z0-9_-]+$') -and ($IngressNetworkName -cmatch '^[a-z0-9][a-z0-9_-]+$') -and ($InternalNetworkName -cne $IngressNetworkName)) "Invalid locked dual-network names."
    Assert-True (($Lock.runtime.internal_network -is [bool]) -and $Lock.runtime.internal_network -and ($Lock.runtime.ingress_network_internal -is [bool]) -and (-not $Lock.runtime.ingress_network_internal) -and ($Lock.runtime.app_outbound_access -is [bool]) -and $Lock.runtime.app_outbound_access) "Invalid locked dual-network policy."
    Assert-True (($IngressServices.Count -eq 1) -and ([string]$IngressServices[0] -ceq "sth")) "Only sth may attach to the ingress network."
    $ExpectedNetworkOptions = Get-ExpectedRuntimeNetworkOptions $Lock
    $AppVolumeName = [string]$Lock.runtime.volume_names.'sth-app-data'
    $DbVolumeName = [string]$Lock.runtime.volume_names.'sth-db2-data'
    Assert-True (($AppVolumeName -cmatch '^[a-z0-9][a-z0-9_.-]+$') -and ($DbVolumeName -cmatch '^[a-z0-9][a-z0-9_.-]+$') -and ($AppVolumeName -cne $DbVolumeName)) "Invalid locked volume names."
    $Context = [PSCustomObject]@{
        ProjectName = $ProjectName
        Commit = $Commit
        InternalNetworkName = $InternalNetworkName
        IngressNetworkName = $IngressNetworkName
        ExpectedNetworkOptions = $ExpectedNetworkOptions
    }
    $UpstreamDir = Resolve-ChildPath $RootDir ([string]$Lock.checkout.path)
    $ComposePath = Resolve-ChildPath $UpstreamDir ([string]$Lock.compose.path)
    Assert-True (Test-Path -LiteralPath $ComposePath -PathType Leaf) "Locked Compose file is absent."
    Assert-True (-not (Test-Path -LiteralPath (Join-Path $UpstreamDir ".env"))) "Forbidden upstream .env exists."
    $Head = (Invoke-NativeCapture "git" @("-C", $UpstreamDir, "rev-parse", "HEAD") "git-head").Text.Trim()
    Assert-True ($Head -ceq $Commit) "Upstream HEAD differs from lock."
    $Status = (Invoke-NativeCapture "git" @("-C", $UpstreamDir, "status", "--porcelain=v1", "--untracked-files=all") "git-status").Text.Trim()
    Assert-True ($Status.Length -eq 0) "Upstream worktree is not clean."
    $AutoCrlf = (Invoke-NativeCapture "git" @("-C", $UpstreamDir, "config", "--local", "--get", "core.autocrlf") "git-core-autocrlf").Text.Trim()
    Assert-True ($AutoCrlf -ceq "false") "Upstream core.autocrlf must be false."

    foreach ($DockerEnvKey in @("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH")) { Assert-True ([string]::IsNullOrWhiteSpace([System.Environment]::GetEnvironmentVariable($DockerEnvKey, "Process"))) "$DockerEnvKey override is forbidden." }
    $ContextName = (Invoke-NativeCapture "docker" @("context", "show") "docker-context-show").Text.Trim()
    $DaemonHost = (Invoke-NativeCapture "docker" @("context", "inspect", "--format", "{{.Endpoints.docker.Host}}", $ContextName) "docker-context-endpoint" -NoLog).Text.Trim()
    Assert-True ($DaemonHost -match '^(?:npipe|unix)://') "Remote Docker context is forbidden."
    $ExpectedAppNetworks = @(@($IngressNetworkName, $InternalNetworkName) | Sort-Object)
    $ExpectedVolumes = @(@($AppVolumeName, $DbVolumeName) | Sort-Object)
    $ExpectedContainerNames = @(@(($ProjectName + "-sth"), ($ProjectName + "-sth-db2")) | Sort-Object)

    foreach ($ExpectedContainerName in $ExpectedContainerNames) {
        $NamedInspect = Invoke-NativeCapture "docker" @("container", "inspect", "--format", "{{.Id}}", $ExpectedContainerName) ("named-container-" + $ExpectedContainerName) -AllowFailure -NoLog
        $NamedContainerRows += [PSCustomObject][ordered]@{ name = $ExpectedContainerName; present = ($NamedInspect.ExitCode -eq 0) }
    }
    $PresentNamedContainerNames = @($NamedContainerRows | Where-Object { $_.present } | ForEach-Object { $_.name } | Sort-Object)

    $ContainerRows = @((Invoke-NativeCapture "docker" @("ps", "-a", "--filter", ("label=com.docker.compose.project=" + $ProjectName), "--format", "{{.ID}}|{{.Names}}") "down-container-set").Text -split "`r?`n" | Where-Object { $_ })
    Assert-True ($ContainerRows.Count -le 2) "Unexpected container count in the locked Compose project."
    $ObservedNames = New-Object System.Collections.Generic.List[string]
    foreach ($Row in $ContainerRows) {
        $Parts = @($Row.Split('|'))
        Assert-True ($Parts.Count -eq 2) "Container safe projection is malformed."
        $ContainerId = $Parts[0]
        $ContainerName = $Parts[1]
        $ExpectedService = if ($ContainerName -ceq ($ProjectName + "-sth")) { "sth" } elseif ($ContainerName -ceq ($ProjectName + "-sth-db2")) { "sth-db2" } else { $null }
        Assert-True ($null -ne $ExpectedService) "Unexpected container name in the locked Compose project."
        Assert-True (-not $ObservedNames.Contains($ContainerName)) "Duplicate target container name is forbidden."
        $ObservedNames.Add($ContainerName)
        $ContainerLabels = ((Invoke-NativeCapture "docker" @("inspect", "--format", "{{json .Config.Labels}}", $ContainerId) ("down-labels-" + $ExpectedService) -NoLog).Text | ConvertFrom-Json)
        $ExpectedContainerLabels = Get-ExpectedContainerLabels $ProjectName $Commit $ExpectedService
        Assert-True (Test-ContainerLabels $ContainerLabels $ExpectedContainerLabels) "Container ownership labels differ from the locked runtime."
        $NetworkMap = ((Invoke-NativeCapture "docker" @("inspect", "--format", "{{json .NetworkSettings.Networks}}", $ContainerId) ("down-networks-" + $ExpectedService) -NoLog).Text | ConvertFrom-Json)
        Assert-True ($null -ne $NetworkMap) "Container network projection is null."
        $AttachedNetworks = @($NetworkMap.PSObject.Properties.Name | Sort-Object)
        $ExpectedContainerNetworks = @(if ($ExpectedService -ceq "sth") { $ExpectedAppNetworks } else { $InternalNetworkName })
        Assert-True (($AttachedNetworks.Count -eq $ExpectedContainerNetworks.Count) -and (($AttachedNetworks -join '|') -ceq ($ExpectedContainerNetworks -join '|'))) "Container network attachments differ from the dual-network contract: $ContainerName"
        $Ports = ((Invoke-NativeCapture "docker" @("inspect", "--format", "{{json .NetworkSettings.Ports}}", $ContainerId) ("down-ports-" + $ExpectedService) -NoLog).Text | ConvertFrom-Json)
        $HostBindings = ((Invoke-NativeCapture "docker" @("inspect", "--format", "{{json .HostConfig.PortBindings}}", $ContainerId) ("down-host-bindings-" + $ExpectedService) -NoLog).Text | ConvertFrom-Json)
        if ($ExpectedService -ceq "sth") {
            Assert-True (((Get-PropertyNames $Ports) -contains "80/tcp") -and ((Get-PropertyNames $HostBindings) -contains "80/tcp")) "Application port binding is absent during down."
            $RealizedBindings = @($Ports.PSObject.Properties["80/tcp"].Value)
            $RequestedBindings = @($HostBindings.PSObject.Properties["80/tcp"].Value)
            Assert-True (($RealizedBindings.Count -eq 1) -and ($RequestedBindings.Count -eq 1)) "Application port binding cardinality differs from one during down."
            Assert-True (([string]$RealizedBindings[0].HostIp -ceq "127.0.0.1") -and ([string]$RequestedBindings[0].HostIp -ceq "127.0.0.1") -and ([string]$RealizedBindings[0].HostPort -ceq [string]$RequestedBindings[0].HostPort)) "Application port binding differs from the loopback contract during down."
            $AppPortBoundary = [int]$RealizedBindings[0].HostPort
            Assert-True (($AppPortBoundary -ge 1024) -and ($AppPortBoundary -le 65535)) "Application port is outside the approved range during down."
        } else {
            Assert-True (((Get-PublishedHostBindingCount $Ports) -eq 0) -and ((Get-PublishedHostBindingCount $HostBindings) -eq 0)) "Database host port publication is forbidden during down."
        }
    }

    $ObservedContainerNames = @($ObservedNames | Sort-Object)
    $ExactContainerSet = (($ObservedContainerNames.Count -eq 2) -and (($ObservedContainerNames -join '|') -ceq ($ExpectedContainerNames -join '|')))
    $NamedContainerSetExact = (($PresentNamedContainerNames.Count -eq 2) -and (($PresentNamedContainerNames -join '|') -ceq ($ExpectedContainerNames -join '|')))

    $ProjectNetworkRows = @((Invoke-NativeCapture "docker" @("network", "ls", "--filter", ("label=com.docker.compose.project=" + $ProjectName), "--format", "{{.Name}}") "project-networks").Text -split "`r?`n" | Where-Object { $_ } | Sort-Object)
    Assert-True (@($ProjectNetworkRows | Select-Object -Unique).Count -eq $ProjectNetworkRows.Count) "Duplicate project network projection is forbidden."
    foreach ($ObservedNetworkName in $ProjectNetworkRows) {
        Assert-True ($ExpectedAppNetworks -ccontains $ObservedNetworkName) "Unexpected third project-labeled network exists: $ObservedNetworkName"
    }
    $NetworksBefore = @(
        (Get-NetworkState $Context $InternalNetworkName $true "internal"),
        (Get-NetworkState $Context $IngressNetworkName $false "ingress")
    )
    $PresentNetworksBefore = @($NetworksBefore | Where-Object { $_.present })
    $ZeroProjectRuntime = (($ContainerRows.Count -eq 0) -and ($PresentNamedContainerNames.Count -eq 0) -and ($ProjectNetworkRows.Count -eq 0) -and ($PresentNetworksBefore.Count -eq 0))
    $ExactActiveRuntime = ($ExactContainerSet -and $NamedContainerSetExact -and ($ProjectNetworkRows.Count -eq 2) -and (($ProjectNetworkRows -join '|') -ceq ($ExpectedAppNetworks -join '|')) -and ($PresentNetworksBefore.Count -eq 2) -and (@($PresentNetworksBefore | Where-Object { -not $_.boundary_match }).Count -eq 0))
    Assert-True ($ZeroProjectRuntime -or $ExactActiveRuntime) "Refusing down because project containers or networks are partial or outside the dual-network contract."

    $ProjectVolumeNamesBefore = @(Get-ProjectVolumeNames $ProjectName)
    Assert-True (@($ProjectVolumeNamesBefore | Select-Object -Unique).Count -eq $ProjectVolumeNamesBefore.Count) "Duplicate project volume projection is forbidden."
    foreach ($ObservedVolumeName in $ProjectVolumeNamesBefore) {
        Assert-True ($ExpectedVolumes -ccontains $ObservedVolumeName) "Unexpected project-labeled volume exists: $ObservedVolumeName"
    }
    $Before = @(
        (Get-VolumeState $Context $AppVolumeName "sth-app-data"),
        (Get-VolumeState $Context $DbVolumeName "sth-db2-data")
    )
    foreach ($Volume in $Before) {
        if ($Volume.present) { Assert-True ([bool]$Volume.labels_match) "Refusing down because a target volume has mismatched labels: $($Volume.name)" }
    }
    $PresentVolumesBefore = @($Before | Where-Object { $_.present })
    $NoVolumes = (($ProjectVolumeNamesBefore.Count -eq 0) -and ($PresentVolumesBefore.Count -eq 0))
    $ExactVolumes = (($ProjectVolumeNamesBefore.Count -eq 2) -and (($ProjectVolumeNamesBefore -join '|') -ceq ($ExpectedVolumes -join '|')) -and ($PresentVolumesBefore.Count -eq 2) -and (@($Before | Where-Object { -not $_.labels_match }).Count -eq 0))
    Assert-True ($NoVolumes -or $ExactVolumes) "Project volumes must be either absent or the exact two label-matched locked volumes."
    if ($ExactActiveRuntime) { Assert-True $ExactVolumes "An active successful runtime must have both locked project volumes." }

    if (Test-Path -LiteralPath $StatePath -PathType Leaf) {
        $StateMarker = $null
        try { $StateMarker = Get-Content -Raw -Encoding UTF8 -LiteralPath $StatePath | ConvertFrom-Json } catch { $StateMarker = $null }
        if (($null -ne $StateMarker) -and ($StateMarker.PSObject.Properties.Name -ccontains "success_state") -and ($StateMarker.success_state -is [bool]) -and $StateMarker.success_state) {
            $SuccessStateMarkerDetected = $true
            try {
                Assert-True (Test-Path -LiteralPath $BoundaryPath -PathType Leaf) "A successful state marker requires runtime boundary evidence."
                $MarkerBoundary = Get-Content -Raw -Encoding UTF8 -LiteralPath $BoundaryPath | ConvertFrom-Json
                Assert-True (([string]$StateMarker.runtime_boundary_sha256 -ceq (Get-Sha256 $BoundaryPath)) -and ($MarkerBoundary.schema -ceq "dssc.semantic-treehouse.runtime-boundary.v1") -and ($MarkerBoundary.status -ceq "PASS") -and ([string]$MarkerBoundary.docker.context -ceq $ContextName)) "Successful state marker Docker context binding differs from the current context."
            } catch {
                $SuccessStateMarkerContextValid = $false
                $SuccessStateMarkerValidationError = Protect-Message $_.Exception.Message
            }
        }
    }
    Assert-True $SuccessStateMarkerContextValid "Refusing down because a successful state marker is not bound to the current Docker context."

    if ($ZeroProjectRuntime) {
        $StateSha256 = if (Test-Path -LiteralPath $StatePath -PathType Leaf) { Get-Sha256 $StatePath } else { $null }
        $Evidence = [ordered]@{
            schema = "dssc.semantic-treehouse.runtime-down.v1"
            status = "PASS"
            upstream_commit = $Commit
            project_name = $ProjectName
            operation = "SAFE_NO_OP_ALREADY_STOPPED"
            compose_down_invoked = $false
            post_smoke_success_state_validated = $false
            runtime_state_disposition = "NOT_REQUIRED_FOR_ZERO_PROJECT_RUNTIME"
            exact_config = [ordered]@{
                lock_sha256 = Get-Sha256 $LockPath
                runtime_state_sha256 = $StateSha256
            }
            named_containers_before = $NamedContainerRows
            success_state_marker_detected = $SuccessStateMarkerDetected
            success_state_marker_context_valid = $SuccessStateMarkerContextValid
            success_state_marker_validation_error = $SuccessStateMarkerValidationError
            containers_remaining = 0
            network_remaining = $false
            networks_remaining = 0
            networks_before = $NetworksBefore
            networks_after = $NetworksBefore
            volumes_before = $Before
            volumes_after = $Before
            volumes_removed = 0
            raw_log_path = "build/phase-08/treehouse-runtime/down.raw.log"
        }
        Write-JsonFile $EvidencePath $Evidence
        Assert-EvidenceSafe $EvidencePath
        Write-Output ("Treehouse down PASS (safe no-op): " + $EvidencePath)
        exit 0
    }

    Assert-True (Test-Path -LiteralPath $OverlayPath -PathType Leaf) "Runtime overlay is absent; exact-config down is refused."
    Assert-True (Test-Path -LiteralPath $EnvPath -PathType Leaf) "Synthetic env is absent; exact-config down is refused."
    Set-IsolatedComposeEnvironment
    Assert-True (Test-Path -LiteralPath $BoundaryPath -PathType Leaf) "Runtime boundary evidence is absent; exact-config down is refused."
    Assert-True (Test-Path -LiteralPath $StatePath -PathType Leaf) "Successful runtime state is absent; public down is refused."
    $Boundary = Get-Content -Raw -Encoding UTF8 -LiteralPath $BoundaryPath | ConvertFrom-Json
    Assert-True (($Boundary.schema -ceq "dssc.semantic-treehouse.runtime-boundary.v1") -and ($Boundary.status -ceq "PASS") -and ($Boundary.prepare_only -is [bool]) -and (-not $Boundary.prepare_only) -and ($Boundary.upstream_commit -ceq $Commit)) "Runtime boundary evidence is incompatible."
    Assert-True (([string]$Boundary.lock_sha256 -ceq (Get-Sha256 $LockPath)) -and ([string]$Boundary.compose_sha256 -ceq (Get-Sha256 $ComposePath)) -and ([string]$Boundary.overlay_sha256 -ceq (Get-Sha256 $OverlayPath)) -and ([string]$Boundary.synthetic_env_sha256 -ceq (Get-Sha256 $EnvPath))) "Exact runtime config hashes differ from boundary evidence."
    Assert-True ([string]$Boundary.docker.context -ceq $ContextName) "Runtime boundary Docker context differs from the current context."
    $BoundaryFields = @(Get-PropertyNames $Boundary.boundary)
    $BoundaryConfiguredDriverOptions = if ($BoundaryFields -ccontains "configured_driver_options") { $Boundary.boundary.configured_driver_options } else { $null }
    Assert-True (($BoundaryFields -ccontains "network_topology") -and ([string]$Boundary.boundary.network_topology -ceq "dual-network-app-ingress")) "Runtime boundary network topology projection differs from the lock."
    Assert-True (($BoundaryFields -ccontains "configured_driver_options") -and ($null -ne $BoundaryConfiguredDriverOptions) -and (@(Get-PropertyNames $BoundaryConfiguredDriverOptions).Count -eq 0)) "Runtime boundary configured network driver options must be empty."
    Assert-True (($BoundaryFields -ccontains "expected_realized_network_options") -and (Test-ExactRuntimeNetworkOptions $Boundary.boundary.expected_realized_network_options $ExpectedNetworkOptions)) "Runtime boundary expected realized network options differ from the lock."
    $BoundaryAppNetworks = @($Boundary.boundary.application_networks | Sort-Object)
    $BoundaryDbNetworks = @($Boundary.boundary.database_networks | Sort-Object)
    $BoundaryVolumes = @($Boundary.boundary.volumes | Sort-Object)
    Assert-True (([string]$Boundary.boundary.internal_network -ceq $InternalNetworkName) -and ([string]$Boundary.boundary.ingress_network -ceq $IngressNetworkName) -and ($Boundary.boundary.app_outbound_access -is [bool]) -and $Boundary.boundary.app_outbound_access) "Runtime boundary does not bind the approved dual-network topology."
    Assert-True (($BoundaryAppNetworks.Count -eq 2) -and (($BoundaryAppNetworks -join '|') -ceq ($ExpectedAppNetworks -join '|'))) "Runtime boundary application networks differ from the lock."
    Assert-True (($BoundaryDbNetworks.Count -eq 1) -and ([string]$BoundaryDbNetworks[0] -ceq $InternalNetworkName)) "Runtime boundary database networks differ from the lock."
    Assert-True (($BoundaryVolumes.Count -eq 2) -and (($BoundaryVolumes -join '|') -ceq ($ExpectedVolumes -join '|'))) "Runtime boundary volumes differ from the lock."
    $State = Get-Content -Raw -Encoding UTF8 -LiteralPath $StatePath | ConvertFrom-Json
    $StateSha256 = Get-Sha256 $StatePath
    $StateVolumes = @($State.volumes | Sort-Object)
    Assert-True (($State.schema -ceq "dssc.semantic-treehouse.runtime-state.v1") -and ($State.upstream_commit -ceq $Commit) -and ($State.project_name -ceq $ProjectName)) "Runtime state differs from the locked deployment."
    Assert-True (([string]$State.lock_sha256 -ceq (Get-Sha256 $LockPath)) -and ([string]$State.runtime_boundary_sha256 -ceq (Get-Sha256 $BoundaryPath)) -and ([string]$State.compose_sha256 -ceq (Get-Sha256 $ComposePath)) -and ([string]$State.overlay_sha256 -ceq (Get-Sha256 $OverlayPath)) -and ([string]$State.synthetic_env_sha256 -ceq (Get-Sha256 $EnvPath))) "Runtime state hashes differ from current exact config."
    $StateNetworkRows = @($State.realized_ingress.networks)
    $StateNetworkNames = @($StateNetworkRows | ForEach-Object { [string]$_.name } | Sort-Object)
    $StateNetworkOptionsValid = (($StateNetworkRows.Count -eq 2) -and (($StateNetworkNames -join '|') -ceq ($ExpectedAppNetworks -join '|')) -and (@($StateNetworkRows | Where-Object { (-not [bool]$_.options_match) -or (-not (Test-ExactRuntimeNetworkOptions $_.options $ExpectedNetworkOptions)) }).Count -eq 0))
    $StateNetworkEvidenceValid = ((Test-Path -LiteralPath $NetworkOptionsEvidencePath -PathType Leaf) -and ([string]$State.realized_ingress.realized_network_options_evidence_sha256 -ceq (Get-Sha256 $NetworkOptionsEvidencePath)))
    Assert-True (([string]$State.network_topology -ceq "dual-network-app-ingress") -and ([string]$State.internal_network -ceq $InternalNetworkName) -and ([string]$State.ingress_network -ceq $IngressNetworkName) -and ([string]$State.bind_address -ceq "127.0.0.1") -and ([int]$State.http_port -ge 1024) -and ([int]$State.http_port -le 65535) -and ([int]$State.http_port -eq [int]$AppPortBoundary) -and ($State.application_outbound_access -is [bool]) -and $State.application_outbound_access -and $StateNetworkOptionsValid -and $StateNetworkEvidenceValid) "Runtime state network boundary differs from the lock."
    Assert-True (($StateVolumes.Count -eq 2) -and (($StateVolumes -join '|') -ceq ($ExpectedVolumes -join '|'))) "Runtime state volume set differs from the lock."
    Assert-True (($State.deployment -ceq "PASS") -and ($State.first_migration -ceq "PASS") -and ($State.production_migration -ceq "PASS") -and ($State.smoke -ceq "PASS") -and ($State.root_smoke -ceq "PASS") -and ($State.api_smoke -ceq "PASS") -and ($State.success_state -is [bool]) -and $State.success_state) "Public down requires a post-smoke successful runtime state."

    $ComposeArgs = @(
        "compose", "--project-name", $ProjectName,
        "--project-directory", $UpstreamDir,
        "--env-file", $EnvPath,
        "-f", $ComposePath,
        "-f", $OverlayPath
    )
    Assert-True (-not ($ComposeArgs -contains "--volumes")) "Down must preserve project volumes."
    $ComposeDownInvoked = $false
    if ($ExactActiveRuntime) {
        Invoke-BoundedDocker ($ComposeArgs + @("down")) "compose-down" 180
        $ComposeDownInvoked = $true
    }

    $RemainingContainers = @((Invoke-NativeCapture "docker" @("ps", "-a", "--filter", ("label=com.docker.compose.project=" + $ProjectName), "--format", "{{.ID}}") "remaining-containers").Text -split "`r?`n" | Where-Object { $_ })
    Assert-True ($RemainingContainers.Count -eq 0) "Project containers remain after down."
    $NamedContainersAfter = @()
    foreach ($ExpectedContainerName in $ExpectedContainerNames) {
        $NamedInspectAfter = Invoke-NativeCapture "docker" @("container", "inspect", "--format", "{{.Id}}", $ExpectedContainerName) ("remaining-named-container-" + $ExpectedContainerName) -AllowFailure -NoLog
        $NamedContainersAfter += [PSCustomObject][ordered]@{ name = $ExpectedContainerName; present = ($NamedInspectAfter.ExitCode -eq 0) }
    }
    Assert-True (@($NamedContainersAfter | Where-Object { $_.present }).Count -eq 0) "A locked container name remains after down."
    $RemainingProjectNetworks = @((Invoke-NativeCapture "docker" @("network", "ls", "--filter", ("label=com.docker.compose.project=" + $ProjectName), "--format", "{{.Name}}") "remaining-project-networks").Text -split "`r?`n" | Where-Object { $_ })
    Assert-True ($RemainingProjectNetworks.Count -eq 0) "Project-labeled networks remain after down."
    $NetworksAfter = @(
        (Get-NetworkState $Context $InternalNetworkName $true "internal"),
        (Get-NetworkState $Context $IngressNetworkName $false "ingress")
    )
    Assert-True (@($NetworksAfter | Where-Object { $_.present }).Count -eq 0) "An internal or ingress project network remains after down."

    $ProjectVolumeNamesAfter = @(Get-ProjectVolumeNames $ProjectName)
    Assert-True (($ProjectVolumeNamesAfter.Count -eq $ProjectVolumeNamesBefore.Count) -and (($ProjectVolumeNamesAfter -join '|') -ceq ($ProjectVolumeNamesBefore -join '|'))) "Project volume name set changed during down."
    $After = @(
        (Get-VolumeState $Context $AppVolumeName "sth-app-data"),
        (Get-VolumeState $Context $DbVolumeName "sth-db2-data")
    )
    for ($Index = 0; $Index -lt $Before.Count; $Index++) {
        if ($Before[$Index].present) {
            Assert-True ($After[$Index].present -and $After[$Index].labels_match -and ([string]$After[$Index].labels_sha256 -ceq [string]$Before[$Index].labels_sha256)) "A labeled project volume was not precisely preserved by down."
        } else {
            Assert-True (-not $After[$Index].present) "A previously absent project volume appeared during down."
        }
    }
    Assert-True ((Test-Path -LiteralPath $StatePath -PathType Leaf) -and ((Get-Sha256 $StatePath) -ceq $StateSha256)) "Post-smoke runtime state changed during down."

    $Evidence = [ordered]@{
        schema = "dssc.semantic-treehouse.runtime-down.v1"
        status = "PASS"
        upstream_commit = $Commit
        project_name = $ProjectName
        operation = if ($ComposeDownInvoked) { "COMPOSE_DOWN" } else { "SAFE_NO_OP_ALREADY_STOPPED" }
        compose_down_invoked = $ComposeDownInvoked
        post_smoke_success_state_validated = $true
        exact_config = [ordered]@{
            lock_sha256 = Get-Sha256 $LockPath
            compose_sha256 = Get-Sha256 $ComposePath
            overlay_sha256 = Get-Sha256 $OverlayPath
            synthetic_env_sha256 = Get-Sha256 $EnvPath
            runtime_state_sha256 = $StateSha256
        }
        named_containers_before = $NamedContainerRows
        named_containers_after = $NamedContainersAfter
        success_state_marker_detected = $SuccessStateMarkerDetected
        success_state_marker_context_valid = $SuccessStateMarkerContextValid
        success_state_marker_validation_error = $SuccessStateMarkerValidationError
        containers_remaining = 0
        network_remaining = $false
        networks_remaining = 0
        networks_before = $NetworksBefore
        networks_after = $NetworksAfter
        volumes_before = $Before
        volumes_after = $After
        volumes_removed = 0
        raw_log_path = "build/phase-08/treehouse-runtime/down.raw.log"
    }
    Write-JsonFile $EvidencePath $Evidence
    Assert-EvidenceSafe $EvidencePath
    Write-Output ("Treehouse down PASS: " + $EvidencePath)
    exit 0
} catch {
    $SafeMessage = Protect-Message $_.Exception.Message
    $Evidence = [ordered]@{
        schema = "dssc.semantic-treehouse.runtime-down.v1"
        status = "ERROR"
        first_error = $SafeMessage
        containers_observed = @($ContainerRows).Count
        named_containers_before = @($NamedContainerRows)
        success_state_marker_detected = $SuccessStateMarkerDetected
        success_state_marker_context_valid = $SuccessStateMarkerContextValid
        success_state_marker_validation_error = $SuccessStateMarkerValidationError
        project_networks_observed = @($ProjectNetworkRows)
        networks_before = @($NetworksBefore)
        app_http_port_observed = $AppPortBoundary
        volumes_before = @($Before)
        volumes_removed = 0
        raw_log_path = "build/phase-08/treehouse-runtime/down.raw.log"
    }
    Write-JsonFile $EvidencePath $Evidence
    Assert-EvidenceSafe $EvidencePath
    Write-Error $SafeMessage
    exit 1
}
