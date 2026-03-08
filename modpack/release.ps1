param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$tool = Join-Path $repoRoot "tools\\modpack_release.py"

if (-not (Test-Path $tool)) {
  Write-Error "Missing tool: $tool"
}

if (Get-Command py -ErrorAction SilentlyContinue) {
  & py $tool @Args
  exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
  & python $tool @Args
  exit $LASTEXITCODE
}

Write-Error "Python launcher not found. Install Python or run with py."
