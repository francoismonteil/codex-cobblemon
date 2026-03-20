param(
    [Parameter(Mandatory = $true)]
    [string]$Schematic,
    [string]$Player,
    [int[]]$At,
    [int]$Dx = 20,
    [int]$Dy = 0,
    [int]$Dz = 0,
    [ValidateSet('none', 'y90', 'y180', 'y270')]
    [string]$Rotate = 'none',
    [switch]$NoClear,
    [switch]$NoWeOffset,
    [switch]$SkipDeploy
)

$ErrorActionPreference = 'Stop'

function Get-SiteContext {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Missing site context: $Path"
    }

    $ctx = @{}
    foreach ($line in Get-Content $Path) {
        if ($line -match '^\s*#') { continue }
        if ($line -match '^\s*$') { continue }
        if ($line -match '^\s*([A-Z0-9_]+)=(.+?)\s*$') {
            $ctx[$matches[1]] = $matches[2]
        }
    }
    return $ctx
}

function Assert-Tool {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $Name"
    }
}

function Get-BashSingleQuoted {
    param([string]$Value)
    return "'" + ($Value -replace "'", "'""'""'") + "'"
}

function Invoke-Native {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $FilePath $($Arguments -join ' ')"
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir '..')).Path
Set-Location $repoRoot

if ($Player -and $At) {
    throw "Use either -Player or -At, not both."
}

if ($At -and $At.Count -ne 3) {
    throw "-At expects exactly 3 integers: x y z"
}

$schematicPath = (Resolve-Path $Schematic).Path
if (-not (Test-Path $schematicPath -PathType Leaf)) {
    throw "Missing schematic: $Schematic"
}

$siteLocal = Join-Path $repoRoot 'runbooks/site.local.md'
$ctx = Get-SiteContext -Path $siteLocal

$required = @('MC_SERVER_HOST', 'MC_SSH_USER', 'MC_PROJECT_DIR', 'SSH_KEY_MAIN')
foreach ($key in $required) {
    if (-not $ctx.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($ctx[$key])) {
        throw "Missing required key in runbooks/site.local.md: $key"
    }
}

Assert-Tool ssh
Assert-Tool scp

$sshKey = $ctx['SSH_KEY_MAIN']
$serverHost = $ctx['MC_SERVER_HOST']
$sshUser = $ctx['MC_SSH_USER']
$projectDir = $ctx['MC_PROJECT_DIR']

if (-not (Test-Path $sshKey)) {
    throw "SSH key not found: $sshKey"
}

if (-not $SkipDeploy) {
    & (Join-Path $repoRoot 'infra/deploy-server.ps1')
    if ($LASTEXITCODE -ne 0) {
        throw "deploy-server.ps1 failed"
    }
}

$remoteBase = "$sshUser@$serverHost"
$remoteDownloads = "$projectDir/downloads"
$remoteName = [System.IO.Path]::GetFileName($schematicPath)
$remoteSchematic = "$remoteDownloads/$remoteName"

Invoke-Native -FilePath ssh -Arguments @(
    '-i', $sshKey,
    '-o', 'BatchMode=yes',
    '-o', 'StrictHostKeyChecking=accept-new',
    $remoteBase,
    "mkdir -p $(Get-BashSingleQuoted $remoteDownloads)"
)

Invoke-Native -FilePath scp -Arguments @(
    '-i', $sshKey,
    '-o', 'BatchMode=yes',
    '-o', 'StrictHostKeyChecking=accept-new',
    $schematicPath,
    "${remoteBase}:$remoteSchematic"
)

$remoteArgs = New-Object System.Collections.Generic.List[string]
$remoteArgs.Add('./infra/spawn-schematic-mcedit.sh')
$remoteArgs.Add('--schematic')
$remoteArgs.Add("downloads/$remoteName")
if ($Player) {
    $remoteArgs.Add('--player')
    $remoteArgs.Add($Player)
}
if ($At) {
    $remoteArgs.Add('--at')
    foreach ($value in $At) {
        $remoteArgs.Add([string]$value)
    }
}
$remoteArgs.Add('--dx')
$remoteArgs.Add([string]$Dx)
$remoteArgs.Add('--dy')
$remoteArgs.Add([string]$Dy)
$remoteArgs.Add('--dz')
$remoteArgs.Add([string]$Dz)
$remoteArgs.Add('--rotate')
$remoteArgs.Add($Rotate)
if ($NoClear) {
    $remoteArgs.Add('--no-clear')
}
if ($NoWeOffset) {
    $remoteArgs.Add('--no-we-offset')
}

$quotedRemoteArgs = ($remoteArgs | ForEach-Object { Get-BashSingleQuoted $_ }) -join ' '
$remoteCommand = "cd $(Get-BashSingleQuoted $projectDir) && $quotedRemoteArgs"

Invoke-Native -FilePath ssh -Arguments @(
    '-i', $sshKey,
    '-o', 'BatchMode=yes',
    '-o', 'StrictHostKeyChecking=accept-new',
    $remoteBase,
    $remoteCommand
)
