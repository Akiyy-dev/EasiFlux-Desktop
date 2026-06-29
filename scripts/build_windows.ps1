param(
    [ValidateSet("onedir", "onefile")]
    [string]$Mode = "onedir",
    [switch]$Clean,
    [switch]$SkipSmokeTest
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

function Assert-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $Name"
    }
}

function Invoke-SmokeTest {
    param([string]$ExePath)
    Write-Host "Smoke testing $ExePath ..."
    $process = Start-Process -FilePath $ExePath -PassThru
    Start-Sleep -Seconds 8
    if ($process.HasExited) {
        if ($process.ExitCode -ne 0) {
            throw "Smoke test failed: process exited with code $($process.ExitCode)"
        }
        throw "Smoke test failed: process exited too early."
    }
    Stop-Process -Id $process.Id -Force
    Write-Host "Smoke test passed."
}

Assert-Command python

$buildArgs = @("scripts/build.py", "--mode", $Mode)
if ($Clean) {
    $buildArgs += "--clean"
}

Write-Host "Building EasiFlux Desktop ($Mode) ..."
python @buildArgs

if ($Mode -eq "onefile") {
    $exePath = Join-Path $Root "dist/EasiFlux.exe"
}
else {
    $exePath = Join-Path $Root "dist/EasiFlux/EasiFlux.exe"
}

if (-not (Test-Path $exePath)) {
    throw "Build output not found: $exePath"
}

if (-not $SkipSmokeTest) {
    Invoke-SmokeTest -ExePath (Resolve-Path $exePath)
}

Write-Host "Build completed: $exePath"
