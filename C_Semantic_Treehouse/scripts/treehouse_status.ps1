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
$RawPath = Join-Path $RuntimeDir "status.raw.log"
$EvidencePath = Join-Path $EvidenceDir "runtime-status.json"
$NetworkOptionsEvidencePath = Join-Path $EvidenceDir "runtime-network-options.json"

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Get-Sha256 {
    param([string]$Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
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

function Protect-Text {
    param([string]$Text)
    if ($null -eq $Text) { return "" }
    $Safe = $Text
    foreach ($SensitivePath in @($RootDir, $RuntimeDir, $env:USERPROFILE, $env:HOME)) {
        if (($null -ne $SensitivePath) -and ([string]$SensitivePath).Length -gt 0) { $Safe = $Safe.Replace([string]$SensitivePath, "<redacted-path>") }
    }
    foreach ($UserName in @($env:USERNAME, $env:USER)) {
        if (($null -ne $UserName) -and ([string]$UserName).Length -ge 3) { $Safe = $Safe.Replace([string]$UserName, "<redacted-user>") }
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

function Invoke-DockerSafe {
    param([string[]]$Arguments, [string]$Step, [switch]$AllowFailure, [switch]$NoLog)
    $PreviousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $Lines = & docker @Arguments 2>&1
        $Code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $PreviousPreference }
    $Text = (($Lines | ForEach-Object { $_.ToString() }) -join "`n").Trim()
    if (-not $NoLog) { [System.IO.File]::AppendAllText($RawPath, ("`r`n===== " + $Step + " =====`r`n" + (Protect-Text $Text) + "`n"), (New-Object System.Text.UTF8Encoding($false))) }
    if (($Code -ne 0) -and (-not $AllowFailure)) { throw "$Step failed with exit code $Code." }
    return [PSCustomObject]@{ ExitCode = $Code; Text = $Text }
}

function Resolve-ChildPath {
    param([string]$Parent, [string]$Relative)
    Assert-True (-not [System.IO.Path]::IsPathRooted($Relative)) "Locked checkout path must be relative."
    Assert-True ($Relative -notmatch '(^|[\\/])\.\.([\\/]|$)') "Locked checkout path contains traversal."
    $ParentFull = [System.IO.Path]::GetFullPath($Parent).TrimEnd('\', '/')
    $Candidate = [System.IO.Path]::GetFullPath((Join-Path $Parent $Relative))
    Assert-True ($Candidate.StartsWith($ParentFull + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) "Locked path escapes repository."
    return $Candidate
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
        $Name = Protect-Text ([string]$Property.Name)
        $Projection[$Name] = Protect-Text ([string]$Property.Value)
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

function Test-Labels {
    param($Actual, $Expected)
    if ($null -eq $Actual) { return $false }
    if (@($Actual.PSObject.Properties | ForEach-Object { $_.Name }).Count -ne $Expected.Count) { return $false }
    foreach ($Key in $Expected.Keys) {
        if (-not ($Actual.PSObject.Properties.Name -contains $Key)) { return $false }
        if ([string]$Actual.$Key -cne [string]$Expected[$Key]) { return $false }
    }
    return $true
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

function Assert-EvidenceSafe {
    param([string]$Path)
    $Text = Get-Content -Raw -Encoding UTF8 -LiteralPath $Path
    foreach ($SensitivePath in @($RootDir, $RuntimeDir, $env:USERPROFILE, $env:HOME)) {
        if (($null -ne $SensitivePath) -and ([string]$SensitivePath).Length -gt 0) {
            Assert-True (-not $Text.Contains([string]$SensitivePath)) "Status evidence contains a repository/home absolute path."
        }
    }
    foreach ($UserName in @($env:USERNAME, $env:USER)) {
        if (($null -ne $UserName) -and ([string]$UserName).Length -ge 3) {
            Assert-True (-not $Text.Contains([string]$UserName)) "Status evidence contains the local username."
        }
    }
    if (Test-Path -LiteralPath $EnvPath -PathType Leaf) {
        foreach ($Line in (Get-Content -Encoding UTF8 -LiteralPath $EnvPath)) {
            $Index = $Line.IndexOf('=')
            if ($Index -gt 0) {
                $Key = $Line.Substring(0, $Index)
                $Value = $Line.Substring($Index + 1)
                if (($Key -match '(?:SECRET|PASSWORD|API_KEY)') -and ($Value.Length -gt 0)) {
                    Assert-True (-not $Text.Contains($Value)) "Status evidence contains a synthetic secret value."
                }
            }
        }
    }
    Assert-True (-not [regex]::IsMatch($Text, '(?m)^(?:APP_SECRET|DB2_PASSWORD|DB2_ROOT_PASSWORD|DB2_TEST_DB_PASSWORD|STH_AI_GATEWAY_DEFAULT_API_KEY)=')) "Status evidence contains env assignments."
    Assert-True (-not [regex]::IsMatch($Text, '(?i)[A-Z]:\\Users\\|/(?:home/[^/\s"'']+|root)(?:/|\b)')) "Status evidence contains a home/root absolute path."
}

New-Item -ItemType Directory -Force -Path $RuntimeDir, $EvidenceDir | Out-Null
Write-Utf8NoBom $RawPath "Semantic Treehouse status raw safe projection; Config.Env is never queried.`n"
$NamedContainerRows = @()
$ObservedProjectContainerNames = @()
$Containers = @()
$Volumes = @()
$Networks = @()
$ObservedRuntimePort = $null
$SuccessStateMarkerDetected = $false
$SuccessStateMarkerContextValid = $true
$SuccessStateMarkerValidationError = $null

try {
    Assert-True (Test-Path -LiteralPath $LockPath -PathType Leaf) "Upstream lock is missing."
    $Lock = Get-Content -Raw -Encoding UTF8 -LiteralPath $LockPath | ConvertFrom-Json
    Assert-True ($Lock.schema -eq "dssc.semantic-treehouse.upstream-lock.v1") "Unexpected upstream lock schema."
    $Commit = [string]$Lock.upstream.commit
    Assert-True ($Commit -cmatch '^[0-9a-f]{40}$') "Invalid locked commit."
    $ProjectName = [string]$Lock.compose.project_name
    $InternalNetworkName = [string]$Lock.runtime.network_name
    $IngressNetworkName = [string]$Lock.runtime.ingress_network_name
    Assert-True ([string]$Lock.runtime.network_topology -ceq "dual-network-app-ingress") "Unexpected runtime network topology."
    Assert-True (($InternalNetworkName -cne $IngressNetworkName) -and ([bool]$Lock.runtime.internal_network) -and (-not [bool]$Lock.runtime.ingress_network_internal) -and ([bool]$Lock.runtime.app_outbound_access)) "Invalid dual-network runtime lock."
    $IngressServices = @($Lock.runtime.ingress_services | ForEach-Object { [string]$_ })
    Assert-True (($IngressServices.Count -eq 1) -and ($IngressServices[0] -ceq "sth")) "Only sth may attach to the ingress network."
    $ExpectedNetworkOptions = Get-ExpectedRuntimeNetworkOptions $Lock
    $UpstreamDir = Resolve-ChildPath $RootDir ([string]$Lock.checkout.path)
    Assert-True (-not (Test-Path -LiteralPath (Join-Path $UpstreamDir ".env"))) "Forbidden upstream .env exists."
    foreach ($DockerEnvKey in @("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH")) { Assert-True ([string]::IsNullOrWhiteSpace([System.Environment]::GetEnvironmentVariable($DockerEnvKey, "Process"))) "$DockerEnvKey override is forbidden." }
    $HeadResult = Invoke-DockerSafe @("context", "show") "docker-context-show"
    $ContextName = $HeadResult.Text.Trim()
    $DaemonHost = (Invoke-DockerSafe @("context", "inspect", "--format", "{{.Endpoints.docker.Host}}", $ContextName) "docker-context-endpoint" -NoLog).Text.Trim()
    Assert-True ($DaemonHost -match '^(?:npipe|unix)://') "Remote Docker context is forbidden."

    $GitPrevious = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $Head = (& git -C $UpstreamDir rev-parse HEAD 2>&1 | ForEach-Object { $_.ToString() }) -join "`n"
        $GitCode = $LASTEXITCODE
    } finally { $ErrorActionPreference = $GitPrevious }
    Assert-True (($GitCode -eq 0) -and ($Head.Trim() -ceq $Commit)) "Upstream HEAD differs from lock."

    $ExpectedContainerNames = @(@(($ProjectName + "-sth"), ($ProjectName + "-sth-db2")) | Sort-Object)
    foreach ($ExpectedContainerName in $ExpectedContainerNames) {
        $NamedInspect = Invoke-DockerSafe @("container", "inspect", "--format", "{{.Id}}", $ExpectedContainerName) ("named-container-" + $ExpectedContainerName) -AllowFailure -NoLog
        $NamedContainerRows += [PSCustomObject][ordered]@{ name = $ExpectedContainerName; present = ($NamedInspect.ExitCode -eq 0) }
    }
    $PresentNamedContainerNames = @($NamedContainerRows | Where-Object { $_.present } | ForEach-Object { $_.name } | Sort-Object)

    $ContainerLines = (Invoke-DockerSafe @("ps", "-a", "--filter", ("label=com.docker.compose.project=" + $ProjectName), "--format", "{{json .}}") "project-containers" -NoLog).Text -split "`r?`n" | Where-Object { $_ }
    foreach ($Line in $ContainerLines) {
        $Row = $Line | ConvertFrom-Json
        $ObservedName = Protect-Text ([string]$Row.Names)
        $ObservedProjectContainerNames += $ObservedName
        Assert-True ($ExpectedContainerNames -ccontains ([string]$Row.Names)) "Unexpected container in project status."
        $ExpectedService = if ([string]$Row.Names -ceq ($ProjectName + "-sth")) { "sth" } else { "sth-db2" }
        $ContainerLabels = ((Invoke-DockerSafe @("inspect", "--format", "{{json .Config.Labels}}", [string]$Row.ID) ("labels-" + [string]$Row.Names) -NoLog).Text | ConvertFrom-Json)
        $ExpectedContainerLabels = Get-ExpectedContainerLabels $ProjectName $Commit $ExpectedService
        Assert-True (Test-ContainerLabels $ContainerLabels $ExpectedContainerLabels) "Container ownership labels differ from the runtime contract."
        $HealthResult = Invoke-DockerSafe @("inspect", "--format", "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}", [string]$Row.ID) ("health-" + [string]$Row.Names)
        $NetworkMap = ((Invoke-DockerSafe @("inspect", "--format", "{{json .NetworkSettings.Networks}}", [string]$Row.ID) ("networks-" + [string]$Row.Names) -NoLog).Text | ConvertFrom-Json)
        $AttachedNetworks = @($NetworkMap.PSObject.Properties.Name | Sort-Object)
        $ExpectedNetworks = @(if ($ExpectedService -ceq "sth") { @($IngressNetworkName, $InternalNetworkName) | Sort-Object } else { $InternalNetworkName })
        Assert-True (($AttachedNetworks.Count -eq $ExpectedNetworks.Count) -and (($AttachedNetworks -join "|") -ceq ($ExpectedNetworks -join "|"))) "Container network attachments differ from the dual-network contract."
        $Ports = ((Invoke-DockerSafe @("inspect", "--format", "{{json .NetworkSettings.Ports}}", [string]$Row.ID) ("ports-" + [string]$Row.Names) -NoLog).Text | ConvertFrom-Json)
        $HostBindings = ((Invoke-DockerSafe @("inspect", "--format", "{{json .HostConfig.PortBindings}}", [string]$Row.ID) ("host-bindings-" + [string]$Row.Names) -NoLog).Text | ConvertFrom-Json)
        $PortProjection = $null
        if ($ExpectedService -ceq "sth") {
            Assert-True (((Get-PropertyNames $Ports) -contains "80/tcp") -and ((Get-PropertyNames $HostBindings) -contains "80/tcp")) "Application port binding is not realized."
            $Realized = @($Ports.PSObject.Properties["80/tcp"].Value)
            $Requested = @($HostBindings.PSObject.Properties["80/tcp"].Value)
            Assert-True (($Realized.Count -eq 1) -and ($Requested.Count -eq 1)) "Application port binding cardinality differs from one."
            foreach ($Binding in @($Realized[0], $Requested[0])) {
                Assert-True ([string]$Binding.HostIp -ceq "127.0.0.1") "Application port binding leaves loopback."
            }
            $RealizedPortText = [string]$Realized[0].HostPort
            $RequestedPortText = [string]$Requested[0].HostPort
            Assert-True (($RealizedPortText -cmatch '^[0-9]+$') -and ($RealizedPortText -ceq $RequestedPortText)) "Realized and requested application ports differ."
            $ObservedRuntimePort = [int]$RealizedPortText
            Assert-True (($ObservedRuntimePort -ge 1024) -and ($ObservedRuntimePort -le 65535)) "Observed runtime port is outside the approved range."
            $PortProjection = "127.0.0.1:{0}:80" -f $ObservedRuntimePort
        } else {
            Assert-True (((Get-PublishedHostBindingCount $Ports) -eq 0) -and ((Get-PublishedHostBindingCount $HostBindings) -eq 0)) "Database host port publication is forbidden."
        }
        $Containers += [PSCustomObject][ordered]@{
            name = [string]$Row.Names
            service = $ExpectedService
            image = [string]$Row.Image
            state = [string]$Row.State
            status = [string]$Row.Status
            health = $HealthResult.Text.Trim()
            ports = [string]$Row.Ports
            network_names = $AttachedNetworks
            realized_port_binding = $PortProjection
            labels_match = $true
        }
    }

    $VolumeSpecs = @(
        @([string]$Lock.runtime.volume_names.'sth-app-data', "sth-app-data"),
        @([string]$Lock.runtime.volume_names.'sth-db2-data', "sth-db2-data")
    )
    foreach ($Spec in $VolumeSpecs) {
        $Inspect = Invoke-DockerSafe @("volume", "inspect", "--format", "{{json .Labels}}", $Spec[0]) ("volume-" + $Spec[1]) -AllowFailure -NoLog
        if ($Inspect.ExitCode -eq 0) {
            $ActualLabels = $Inspect.Text | ConvertFrom-Json
            $Volumes += [PSCustomObject][ordered]@{ name = $Spec[0]; present = $true; labels_match = (Test-Labels $ActualLabels (Get-ExpectedLabels ([PSCustomObject]@{ ProjectName=$ProjectName; Commit=$Commit }) $Spec[1])) }
        } else {
            $Volumes += [PSCustomObject][ordered]@{ name = $Spec[0]; present = $false; labels_match = $false }
        }
    }
    $ExpectedVolumeNames = @($VolumeSpecs | ForEach-Object { [string]$_[0] } | Sort-Object)
    $ProjectVolumeNames = @((Invoke-DockerSafe @("volume", "ls", "--filter", ("label=com.docker.compose.project=" + $ProjectName), "--format", "{{.Name}}") "project-volumes").Text -split "`r?`n" | Where-Object { $_ } | Sort-Object)
    Assert-True (@($ProjectVolumeNames | Select-Object -Unique).Count -eq $ProjectVolumeNames.Count) "Duplicate project volume projection is forbidden."
    foreach ($ObservedVolumeName in $ProjectVolumeNames) { Assert-True ($ExpectedVolumeNames -ccontains $ObservedVolumeName) "Unexpected project-labeled volume exists." }

    $ProjectNetworkRows = @((Invoke-DockerSafe @("network", "ls", "--filter", ("label=com.docker.compose.project=" + $ProjectName), "--format", "{{.Name}}") "project-networks").Text -split "`r?`n" | Where-Object { $_ })
    $AllowedNetworkNames = @(@($IngressNetworkName, $InternalNetworkName) | Sort-Object)
    foreach ($ObservedName in $ProjectNetworkRows) { Assert-True ($AllowedNetworkNames -ccontains $ObservedName) "Unexpected project-labeled network exists." }
    Assert-True (@($ProjectNetworkRows | Select-Object -Unique).Count -eq $ProjectNetworkRows.Count) "Duplicate project network projection is forbidden."
    foreach ($Spec in @(@($InternalNetworkName, $true, "internal"), @($IngressNetworkName, $false, "ingress"))) {
        $NetworkInspect = Invoke-DockerSafe @("network", "inspect", "--format", "{{json .Internal}}|{{.Driver}}|{{json .Options}}|{{json .Labels}}", [string]$Spec[0]) ("runtime-network-" + [string]$Spec[2]) -AllowFailure -NoLog
        $Network = [ordered]@{ name = [string]$Spec[0]; role = [string]$Spec[2]; present = $false; internal = $null; driver = $null; options = $null; options_match = $false; labels_match = $false; boundary_match = $false }
        if ($NetworkInspect.ExitCode -eq 0) {
            $NetworkParts = $NetworkInspect.Text.Split([char[]]@('|'), 4)
            Assert-True ($NetworkParts.Count -eq 4) "Runtime network safe projection is malformed."
            $NetworkLabels = $NetworkParts[3] | ConvertFrom-Json
            $NetworkOptions = $NetworkParts[2] | ConvertFrom-Json
            $Network.present = $true
            $Network.internal = [bool]($NetworkParts[0] | ConvertFrom-Json)
            $Network.driver = $NetworkParts[1]
            $Network.options = ConvertTo-SafeRuntimeNetworkOptions $NetworkOptions
            $Network.options_match = Test-ExactRuntimeNetworkOptions $NetworkOptions $ExpectedNetworkOptions
            $Network.labels_match = (($null -ne $NetworkLabels) -and ($NetworkLabels.'com.docker.compose.project' -ceq $ProjectName) -and ($NetworkLabels.'dssc.semantic-treehouse.project' -ceq $ProjectName) -and ($NetworkLabels.'dssc.semantic-treehouse.upstream-commit' -ceq $Commit) -and ($NetworkLabels.'dssc.semantic-treehouse.runtime-contract' -ceq "v1") -and ($NetworkLabels.'dssc.semantic-treehouse.network-role' -ceq [string]$Spec[2]))
            $Network.boundary_match = (($Network.internal -eq [bool]$Spec[1]) -and ($Network.driver -ceq "bridge") -and $Network.options_match -and $Network.labels_match)
        }
        $Networks += [PSCustomObject]$Network
    }

    $ContainerCount = @($Containers).Count
    $Names = @($Containers | ForEach-Object { $_.name } | Sort-Object)
    $ExactContainers = (($Names.Count -eq 2) -and (($Names -join "|") -ceq ($ExpectedContainerNames -join "|")))
    $NamedContainerSetExact = (($PresentNamedContainerNames.Count -eq 2) -and (($PresentNamedContainerNames -join "|") -ceq ($ExpectedContainerNames -join "|")))
    $NonRunningContainers = @($Containers | Where-Object { $_.state -cne "running" })
    $AllRunning = ($NonRunningContainers.Count -eq 0)
    $DbHealthy = (@($Containers | Where-Object { ($_.service -ceq "sth-db2") -and ($_.health -ceq "healthy") }).Count -eq 1)
    $PresentVolumes = @($Volumes | Where-Object { $_.present })
    $NoVolumes = (($ProjectVolumeNames.Count -eq 0) -and ($PresentVolumes.Count -eq 0))
    $ExactVolumes = (($ProjectVolumeNames.Count -eq 2) -and (($ProjectVolumeNames -join "|") -ceq ($ExpectedVolumeNames -join "|")) -and ($PresentVolumes.Count -eq 2) -and (@($PresentVolumes | Where-Object { -not $_.labels_match }).Count -eq 0))
    $VolumesSafe = ($NoVolumes -or $ExactVolumes)

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
                $SuccessStateMarkerValidationError = Protect-Text $_.Exception.Message
            }
        }
    }

    $RuntimeStateValid = $false
    $RuntimeStateValidationError = $null
    if (($ContainerCount -gt 0) -and (Test-Path -LiteralPath $StatePath -PathType Leaf)) {
        try {
            $State = Get-Content -Raw -Encoding UTF8 -LiteralPath $StatePath | ConvertFrom-Json
            $ComposePath = Resolve-ChildPath $UpstreamDir ([string]$Lock.compose.path)
            Assert-True (Test-Path -LiteralPath $BoundaryPath -PathType Leaf) "Runtime boundary evidence is absent."
            $Boundary = Get-Content -Raw -Encoding UTF8 -LiteralPath $BoundaryPath | ConvertFrom-Json
            $BoundaryFields = @(Get-PropertyNames $Boundary.boundary)
            $BoundaryConfiguredDriverOptions = if ($BoundaryFields -ccontains "configured_driver_options") { $Boundary.boundary.configured_driver_options } else { $null }
            $BoundaryStaticNetworkValid = (
                ($Boundary.schema -ceq "dssc.semantic-treehouse.runtime-boundary.v1") -and
                ($Boundary.status -ceq "PASS") -and
                ($Boundary.prepare_only -is [bool]) -and (-not $Boundary.prepare_only) -and
                ($Boundary.upstream_commit -ceq $Commit) -and
                ([string]$Boundary.lock_sha256 -ceq (Get-Sha256 $LockPath)) -and
                ([string]$Boundary.docker.context -ceq $ContextName) -and
                ($BoundaryFields -ccontains "network_topology") -and
                ([string]$Boundary.boundary.network_topology -ceq "dual-network-app-ingress") -and
                ($BoundaryFields -ccontains "configured_driver_options") -and
                ($null -ne $BoundaryConfiguredDriverOptions) -and
                (@(Get-PropertyNames $BoundaryConfiguredDriverOptions).Count -eq 0) -and
                ($BoundaryFields -ccontains "expected_realized_network_options") -and
                (Test-ExactRuntimeNetworkOptions $Boundary.boundary.expected_realized_network_options $ExpectedNetworkOptions)
            )
            $StateNetworks = @($State.realized_ingress.networks)
            $StateNetworkNames = @($StateNetworks | ForEach-Object { [string]$_.name } | Sort-Object)
            $StateNetworkOptionsValid = (($StateNetworks.Count -eq 2) -and (($StateNetworkNames -join "|") -ceq ($AllowedNetworkNames -join "|")) -and (@($StateNetworks | Where-Object { (-not [bool]$_.options_match) -or (-not (Test-ExactRuntimeNetworkOptions $_.options $ExpectedNetworkOptions)) }).Count -eq 0))
            $StateNetworkEvidenceValid = ((Test-Path -LiteralPath $NetworkOptionsEvidencePath -PathType Leaf) -and ([string]$State.realized_ingress.realized_network_options_evidence_sha256 -ceq (Get-Sha256 $NetworkOptionsEvidencePath)))
            $StateVolumes = @($State.volumes | ForEach-Object { [string]$_ } | Sort-Object)
            $StateAppNetworks = @($State.realized_ingress.application_networks | ForEach-Object { [string]$_ } | Sort-Object)
            $StateDbNetworks = @($State.realized_ingress.database_networks | ForEach-Object { [string]$_ } | Sort-Object)
            $StateIngressValid = (($State.realized_ingress.status -ceq "PASS") -and ([string]$State.realized_ingress.binding -ceq ("127.0.0.1:" + [int]$State.http_port + ":80")) -and ($State.realized_ingress.network_settings_ports_programmed -is [bool]) -and $State.realized_ingress.network_settings_ports_programmed -and ($State.realized_ingress.host_config_binding_matches -is [bool]) -and $State.realized_ingress.host_config_binding_matches -and ($StateAppNetworks.Count -eq 2) -and (($StateAppNetworks -join "|") -ceq ($AllowedNetworkNames -join "|")) -and ($StateDbNetworks.Count -eq 1) -and ($StateDbNetworks[0] -ceq $InternalNetworkName) -and ([int]$State.realized_ingress.database_published_ports -eq 0) -and ($State.realized_ingress.application_outbound_access -is [bool]) -and $State.realized_ingress.application_outbound_access)
            $RuntimeStateValid = (
                $BoundaryStaticNetworkValid -and
                ($State.schema -ceq "dssc.semantic-treehouse.runtime-state.v1") -and
                ($State.upstream_commit -ceq $Commit) -and
                ($State.project_name -ceq $ProjectName) -and
                ($State.lock_sha256 -ceq (Get-Sha256 $LockPath)) -and
                ($State.runtime_boundary_sha256 -ceq (Get-Sha256 $BoundaryPath)) -and
                ($State.compose_sha256 -ceq (Get-Sha256 $ComposePath)) -and
                ($State.overlay_sha256 -ceq (Get-Sha256 $OverlayPath)) -and
                ($State.synthetic_env_sha256 -ceq (Get-Sha256 $EnvPath)) -and
                ($State.network_topology -ceq "dual-network-app-ingress") -and
                ($State.internal_network -ceq $InternalNetworkName) -and
                ($State.ingress_network -ceq $IngressNetworkName) -and
                ($State.bind_address -ceq "127.0.0.1") -and
                ($State.application_outbound_access -is [bool]) -and $State.application_outbound_access -and
                ([int]$State.http_port -ge 1024) -and ([int]$State.http_port -le 65535) -and
                ($null -ne $ObservedRuntimePort) -and ([int]$State.http_port -eq [int]$ObservedRuntimePort) -and
                ($StateVolumes.Count -eq 2) -and (($StateVolumes -join "|") -ceq ($ExpectedVolumeNames -join "|")) -and
                $StateIngressValid -and $StateNetworkOptionsValid -and $StateNetworkEvidenceValid -and
                ($State.deployment -ceq "PASS") -and ($State.first_migration -ceq "PASS") -and
                ($State.production_migration -ceq "PASS") -and ($State.smoke -ceq "PASS") -and
                ($State.root_smoke -ceq "PASS") -and ($State.api_smoke -ceq "PASS") -and
                ($State.success_state -is [bool]) -and $State.success_state
            )
        } catch {
            $RuntimeStateValid = $false
            $RuntimeStateValidationError = Protect-Text $_.Exception.Message
        }
    }
    $NetworksPresent = @($Networks | Where-Object { $_.present })
    $SortedProjectNetworkRows = @($ProjectNetworkRows | Sort-Object)
    $NetworkSetValid = (($NetworksPresent.Count -eq 2) -and ($SortedProjectNetworkRows.Count -eq 2) -and (($SortedProjectNetworkRows -join "|") -ceq ($AllowedNetworkNames -join "|")) -and (@($NetworksPresent | Where-Object { -not $_.boundary_match }).Count -eq 0))
    $Status = if (($ContainerCount -eq 0) -and ($PresentNamedContainerNames.Count -eq 0) -and ($ProjectNetworkRows.Count -eq 0) -and ($NetworksPresent.Count -eq 0) -and $VolumesSafe -and $SuccessStateMarkerContextValid) { "STOPPED" } elseif ($ExactContainers -and $NamedContainerSetExact -and $AllRunning -and $DbHealthy -and $ExactVolumes -and $NetworkSetValid -and $RuntimeStateValid) { "RUNNING" } else { "REVIEW_REQUIRED" }
    $Evidence = [ordered]@{
        schema = "dssc.semantic-treehouse.runtime-status.v1"
        status = $Status
        upstream_commit = $Commit
        project_name = $ProjectName
        lock_sha256 = Get-Sha256 $LockPath
        docker = [ordered]@{ context = $ContextName; endpoint_scheme = $DaemonHost.Split(':')[0]; remote_daemon = $false }
        containers = $Containers
        observed_project_container_names = @($ObservedProjectContainerNames | Sort-Object)
        named_containers = $NamedContainerRows
        volumes = $Volumes
        networks = $Networks
        realized_network_options_expected = $ExpectedNetworkOptions
        runtime_state_valid = $RuntimeStateValid
        runtime_state_validation_error = $RuntimeStateValidationError
        success_state_marker_detected = $SuccessStateMarkerDetected
        success_state_marker_context_valid = $SuccessStateMarkerContextValid
        success_state_marker_validation_error = $SuccessStateMarkerValidationError
        synthetic_env_present = (Test-Path -LiteralPath $EnvPath -PathType Leaf)
        synthetic_env_sha256 = if (Test-Path -LiteralPath $EnvPath -PathType Leaf) { Get-Sha256 $EnvPath } else { $null }
        runtime_state_present = (Test-Path -LiteralPath $StatePath -PathType Leaf)
        runtime_state_sha256 = if (Test-Path -LiteralPath $StatePath -PathType Leaf) { Get-Sha256 $StatePath } else { $null }
        observed_http_port = $ObservedRuntimePort
        config_env_queried = $false
        raw_log_path = "build/phase-08/treehouse-runtime/status.raw.log"
    }
    Write-JsonFile $EvidencePath $Evidence
    Assert-EvidenceSafe $EvidencePath
    Write-Output ($Evidence | ConvertTo-Json -Depth 20)
    if ($Status -eq "REVIEW_REQUIRED") { exit 1 }
    exit 0
} catch {
    $SafeMessage = Protect-Text $_.Exception.Message
    $Evidence = [ordered]@{
        schema = "dssc.semantic-treehouse.runtime-status.v1"
        status = "ERROR"
        error = $SafeMessage
        containers = @($Containers)
        observed_project_container_names = @($ObservedProjectContainerNames | Sort-Object)
        named_containers = @($NamedContainerRows)
        volumes = @($Volumes)
        networks = @($Networks)
        observed_http_port = $ObservedRuntimePort
        success_state_marker_detected = $SuccessStateMarkerDetected
        success_state_marker_context_valid = $SuccessStateMarkerContextValid
        success_state_marker_validation_error = $SuccessStateMarkerValidationError
        config_env_queried = $false
        raw_log_path = "build/phase-08/treehouse-runtime/status.raw.log"
    }
    Write-JsonFile $EvidencePath $Evidence
    Assert-EvidenceSafe $EvidencePath
    Write-Error $SafeMessage
    exit 1
}
