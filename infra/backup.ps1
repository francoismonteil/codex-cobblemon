$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$DataDir = Join-Path $RepoRoot "data"
$BackupDir = Join-Path $RepoRoot "backups"
$StagingRoot = Join-Path $BackupDir "_staging"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ArchiveName = "backup-$Timestamp.zip"
$ArchivePath = Join-Path $BackupDir $ArchiveName
$StagingDir = Join-Path $StagingRoot $Timestamp
$Targets = @(
    "world",
    "config",
    "mods",
    "kubejs",
    "server.properties",
    "whitelist.json",
    "ops.json",
    "banned-ips.json",
    "banned-players.json",
    "allowed_symlinks.txt"
)

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
New-Item -ItemType Directory -Force -Path $StagingDir | Out-Null

$found = $false
foreach ($target in $Targets) {
    $src = Join-Path $DataDir $target
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $StagingDir -Recurse -Force
        $found = $true
    } else {
        Write-Host "Skip missing: $src"
    }
}

if (-not $found) {
    Remove-Item -Path $StagingDir -Recurse -Force
    Write-Host "No data found to back up. Skipping."
    exit 0
}

$files = Get-ChildItem -Path $StagingDir -Recurse -File
$manifest = foreach ($file in $files) {
    [PSCustomObject]@{
        Path = $file.FullName.Substring($StagingDir.Length + 1)
        Hash = (Get-FileHash -Algorithm SHA256 -Path $file.FullName).Hash
        Algorithm = "SHA256"
    }
}
$manifest | ConvertTo-Json -Depth 3 | Set-Content -Path (Join-Path $StagingDir "manifest.json") -Encoding ASCII

Compress-Archive -Path (Join-Path $StagingDir "*") -DestinationPath $ArchivePath -Force
Remove-Item -Path $StagingDir -Recurse -Force

Write-Host "Backup created: $ArchivePath"
