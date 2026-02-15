param([string]$Archive)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$DataDir = Join-Path $RepoRoot "data"
$BackupDir = Join-Path $RepoRoot "backups"
$RestoreRoot = Join-Path $BackupDir "_restore"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ExtractDir = Join-Path $RestoreRoot $Timestamp

if ([string]::IsNullOrWhiteSpace($Archive)) {
    Write-Error "Archive is required."
    exit 1
}

$ArchivePath = Resolve-Path -Path $Archive -ErrorAction SilentlyContinue
if (-not $ArchivePath) {
    Write-Error "Archive not found: $Archive"
    exit 1
}

New-Item -ItemType Directory -Force -Path $ExtractDir | Out-Null
Expand-Archive -Path $ArchivePath -DestinationPath $ExtractDir -Force

$ManifestPath = Join-Path $ExtractDir "manifest.json"
if (Test-Path $ManifestPath) {
    $manifest = Get-Content -Path $ManifestPath -Raw | ConvertFrom-Json
    foreach ($entry in $manifest) {
        $filePath = Join-Path $ExtractDir $entry.Path
        if (-not (Test-Path $filePath)) {
            throw "Missing file: $($entry.Path)"
        }
        $hash = (Get-FileHash -Algorithm $entry.Algorithm -Path $filePath).Hash
        if ($hash -ne $entry.Hash) {
            throw "Hash mismatch: $($entry.Path)"
        }
    }
} else {
    Write-Host "Manifest not found, skipping hash verification."
}

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
$items = Get-ChildItem -Path $ExtractDir -Force
foreach ($item in $items) {
    if ($item.Name -eq "manifest.json") {
        continue
    }
    Copy-Item -Path $item.FullName -Destination $DataDir -Recurse -Force
}

Remove-Item -Path $ExtractDir -Recurse -Force
Write-Host "Restore completed from: $ArchivePath"
