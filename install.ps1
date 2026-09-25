param(
  [Parameter(Mandatory=$true)]
  [string]$Target
)

$ErrorActionPreference = "Stop"
$Source = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"

if (-not (Test-Path $Target)) {
  New-Item -ItemType Directory -Force -Path $Target | Out-Null
}

foreach ($item in @("GEMINI.md", ".agents", "TALENTRA")) {
  $src = Join-Path $Source $item
  $dst = Join-Path $Target $item
  if (Test-Path $dst) {
    $backup = "$dst.backup-$Stamp"
    Write-Host "Backing up $dst -> $backup"
    Move-Item $dst $backup
  }
  Copy-Item $src $dst -Recurse -Force
}

Write-Host "TALENTRA Antigravity kit installed into $Target"
Write-Host "Reopen Antigravity and select 'talentra-orchestrator'."
