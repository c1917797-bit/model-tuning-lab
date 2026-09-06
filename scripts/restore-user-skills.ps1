param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [string]$UserProfileRoot = $env:USERPROFILE
)

$ErrorActionPreference = 'Stop'

if (-not $UserProfileRoot) {
    throw 'USERPROFILE is not set; pass -UserProfileRoot explicitly.'
}

$codexSource = Join-Path $RepoRoot 'skills\codex-skills'
$agentsSource = Join-Path $RepoRoot 'skills\agents-skills'
$codexTarget = Join-Path $UserProfileRoot '.codex\skills'
$agentsTarget = Join-Path $UserProfileRoot '.agents\skills'

if (-not (Test-Path -LiteralPath $codexSource)) {
    throw "Missing codex skill source: $codexSource"
}
if (-not (Test-Path -LiteralPath $agentsSource)) {
    throw "Missing agents skill source: $agentsSource"
}

New-Item -ItemType Directory -Force -Path $codexTarget | Out-Null
New-Item -ItemType Directory -Force -Path $agentsTarget | Out-Null

Get-ChildItem -LiteralPath $codexSource -Force | Copy-Item -Destination $codexTarget -Recurse -Force
Get-ChildItem -LiteralPath $agentsSource -Force | Copy-Item -Destination $agentsTarget -Recurse -Force

Write-Host "Restored Codex skills to $codexTarget"
Write-Host "Restored agent skills to $agentsTarget"
Write-Host 'Restart Codex/ChatGPT if the newly restored skills do not appear immediately.'
