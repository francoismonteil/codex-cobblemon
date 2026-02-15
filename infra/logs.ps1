$ErrorActionPreference = 'Stop'

Set-Location $PSScriptRoot\..\

docker compose logs -f --tail=200