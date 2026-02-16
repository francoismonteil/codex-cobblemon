$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\\..")
Set-Location $repoRoot

$out = "datapacks/acm_pokemon_worldgen/data/acm/structure"

if (Get-Command py -ErrorAction SilentlyContinue) {
  & py -3 tools/structgen/compile.py --out $out --include-entities @args
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  & python tools/structgen/compile.py --out $out --include-entities @args
} else {
  throw "Missing Python interpreter (py -3 or python)."
}

Write-Output "OK: regenerated structures under $out"
