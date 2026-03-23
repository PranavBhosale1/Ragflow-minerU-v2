# RAGFlow + MinerU - run from repo root (Ragflow-minerU-v2).
# Loads ragflow/docker/.env so COMPOSE_PROFILES (elasticsearch,cpu, etc.) applies.
# Use -MineruGpu to merge docker-compose.mineru-gpu.yml (CUDA MinerU + GPU; faster VLM).
#
# Default is "up -d" only (no --build) so you do not re-download image layers every run.
# After changing a Dockerfile or first-time local image build, run:
#   .\start-ragflow-mineru.ps1 -ComposeArgs up,-d,--build
# Or: .\start-ragflow-mineru.ps1 -Build
param(
    [switch]$MineruGpu,
    [switch]$Build,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ComposeArgs = @("up", "-d")
)
$envFile = Join-Path $PSScriptRoot "ragflow\docker\.env"
if (-not (Test-Path $envFile)) {
    Write-Error "Missing $envFile - copy or create ragflow/docker/.env first."
    exit 1
}
Set-Location $PSScriptRoot
$dc = @("compose", "--env-file", $envFile)
if ($MineruGpu) {
    $dc += @(
        "-f", (Join-Path $PSScriptRoot "docker-compose.yml"),
        "-f", (Join-Path $PSScriptRoot "docker-compose.mineru-gpu.yml")
    )
}
if ($Build) {
    $dc += @("up", "-d", "--build")
} else {
    $dc += $ComposeArgs
}
& docker @dc
