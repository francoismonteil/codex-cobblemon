param(
    [switch]$NoDeleteExtra,
    [switch]$DryRun
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

function Copy-ManagedFile {
    param(
        [string]$RepoRoot,
        [string]$StageRoot,
        [string]$RelativePath
    )

    $src = Join-Path $RepoRoot $RelativePath
    $dst = Join-Path $StageRoot $RelativePath
    $dstDir = Split-Path -Parent $dst
    if (-not (Test-Path $dstDir)) {
        New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
    }
    Copy-Item -Path $src -Destination $dst -Force
}

function Get-RelativeUnixPath {
    param(
        [string]$BasePath,
        [string]$ChildPath
    )

    $baseUri = [System.Uri]((Resolve-Path $BasePath).Path.TrimEnd('\') + '\')
    $childUri = [System.Uri](Resolve-Path $ChildPath).Path
    return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($childUri).ToString())
}

function Test-ExcludedRelativePath {
    param([string]$RelativePath)

    $normalized = $RelativePath.Replace('\', '/')
    $segments = $normalized.Split('/')

    if ($normalized.EndsWith('.pyc')) { return $true }
    if ($segments -contains '.venv') { return $true }
    if ($segments -contains '__pycache__') { return $true }
    if ($segments -contains '.pytest_cache') { return $true }
    if ($segments -contains 'node_modules') { return $true }
    if ($segments -contains '.mypy_cache') { return $true }
    if ($segments -contains '.ruff_cache') { return $true }
    if ($segments -contains '.coverage') { return $true }

    return $false
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir '..')).Path
$siteLocal = Join-Path $repoRoot 'runbooks/site.local.md'
$ctx = Get-SiteContext -Path $siteLocal

$required = @('MC_SERVER_HOST', 'MC_SSH_USER', 'MC_PROJECT_DIR', 'SSH_KEY_MAIN')
foreach ($key in $required) {
    if (-not $ctx.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($ctx[$key])) {
        throw "Missing required key in runbooks/site.local.md: $key"
    }
}

$sshKey = $ctx['SSH_KEY_MAIN']
$serverHost = $ctx['MC_SERVER_HOST']
$sshUser = $ctx['MC_SSH_USER']
$projectDir = $ctx['MC_PROJECT_DIR']

if (-not (Test-Path $sshKey)) {
    throw "SSH key not found: $sshKey"
}

Assert-Tool ssh
Assert-Tool scp
Assert-Tool tar

$managedFiles = @(
    'README.md',
    '.env.example',
    'AGENTS.md',
    'docker-compose.yml',
    'docker-compose.pregen.yml',
    'manifest.Lydu1ZNo.json'
)

$managedDirs = @(
    'infra',
    'runbooks',
    'datapacks',
    'tools',
    'admin-web',
    'modpack'
)

$excludedFiles = @(
    'runbooks/site.local.md'
)

$manifest = New-Object System.Collections.Generic.List[string]

foreach ($rel in $managedFiles) {
    $path = Join-Path $repoRoot $rel
    if (Test-Path $path) {
        $manifest.Add($rel)
    }
}

foreach ($dir in $managedDirs) {
    $fullDir = Join-Path $repoRoot $dir
    if (-not (Test-Path $fullDir)) {
        continue
    }

    Get-ChildItem -Path $fullDir -Recurse -File | ForEach-Object {
        $rel = Get-RelativeUnixPath -BasePath $repoRoot -ChildPath $_.FullName
        if ($excludedFiles -contains $rel) {
            return
        }
        if (Test-ExcludedRelativePath -RelativePath $rel) {
            return
        }
        $manifest.Add($rel)
    }
}

$manifest = $manifest | Sort-Object -Unique

if ($DryRun) {
    Write-Host "Deploy target: ${sshUser}@${serverHost}:$projectDir"
    Write-Host "Managed files: $($manifest.Count)"
    $manifest | ForEach-Object { Write-Host $_ }
    exit 0
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("codex-cobblemon-deploy-" + [guid]::NewGuid().ToString('N'))
$stageRoot = Join-Path $tempRoot 'stage'
$archivePath = Join-Path $tempRoot 'deploy.tar'
$manifestPath = Join-Path $tempRoot 'manifest.txt'
$remoteScriptPath = Join-Path $tempRoot 'apply.sh'

New-Item -ItemType Directory -Force -Path $stageRoot | Out-Null

foreach ($rel in $manifest) {
    Copy-ManagedFile -RepoRoot $repoRoot -StageRoot $stageRoot -RelativePath $rel
}

[System.IO.File]::WriteAllText(
    $manifestPath,
    (($manifest -join "`n") + "`n"),
    (New-Object System.Text.UTF8Encoding($false))
)

$projectDirQuoted = Get-BashSingleQuoted $projectDir

$remoteScript = @'
#!/usr/bin/env bash
set -euo pipefail

proj=__PROJECT_DIR__
tmp="$1"
delete_extra="$2"
manifest="$tmp/manifest.txt"
archive="$tmp/deploy.tar"

mkdir -p "$proj"
tar -xf "$archive" -C "$proj"
cp -f "$manifest" "$proj/.deploy-sync-last-manifest.txt"

if [[ "$delete_extra" == "true" ]]; then
  {
    for d in infra runbooks datapacks tools admin-web modpack; do
      if [[ -d "$proj/$d" ]]; then
        (cd "$proj" && find "$d" -type f | LC_ALL=C sort)
      fi
    done
    for f in README.md .env.example AGENTS.md docker-compose.yml docker-compose.pregen.yml manifest.Lydu1ZNo.json; do
      if [[ -f "$proj/$f" ]]; then
        echo "$f"
      fi
    done
  } | LC_ALL=C sort -u | while IFS= read -r rel; do
    grep -Fxq "$rel" "$manifest" || rm -f "$proj/$rel"
  done

  for d in infra runbooks datapacks tools admin-web modpack; do
    if [[ -d "$proj/$d" ]]; then
      find "$proj/$d" -depth -type d -empty -delete
    fi
  done
fi

rm -f "$proj/runbooks/site.local.md"
rm -rf "$tmp"
echo "DEPLOY_OK"
'@

$remoteScript = $remoteScript.Replace('__PROJECT_DIR__', $projectDirQuoted)

[System.IO.File]::WriteAllText(
    $remoteScriptPath,
    ($remoteScript -replace "`r`n", "`n"),
    (New-Object System.Text.UTF8Encoding($false))
)

Invoke-Native -FilePath tar -Arguments @('-cf', $archivePath, '-C', $stageRoot, '.')

$remoteBase = "$sshUser@$serverHost"
$remoteTmp = "$projectDir/.deploy-sync-" + (Get-Date -Format 'yyyyMMdd-HHmmss')

Invoke-Native -FilePath ssh -Arguments @('-i', $sshKey, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=accept-new', $remoteBase, "mkdir -p $(Get-BashSingleQuoted $remoteTmp)")
Invoke-Native -FilePath scp -Arguments @('-i', $sshKey, $archivePath, "${remoteBase}:$remoteTmp/deploy.tar")
Invoke-Native -FilePath scp -Arguments @('-i', $sshKey, $manifestPath, "${remoteBase}:$remoteTmp/manifest.txt")
Invoke-Native -FilePath scp -Arguments @('-i', $sshKey, $remoteScriptPath, "${remoteBase}:$remoteTmp/apply.sh")

$deleteFlag = if ($NoDeleteExtra) { 'false' } else { 'true' }
Invoke-Native -FilePath ssh -Arguments @(
    '-i', $sshKey,
    '-o', 'BatchMode=yes',
    '-o', 'StrictHostKeyChecking=accept-new',
    $remoteBase,
    "bash $(Get-BashSingleQuoted "$remoteTmp/apply.sh") $(Get-BashSingleQuoted $remoteTmp) $deleteFlag"
)

Remove-Item -Recurse -Force $tempRoot
Write-Host "Deploy complete: ${remoteBase}:$projectDir"
