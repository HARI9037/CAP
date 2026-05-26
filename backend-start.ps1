$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ProjectRoot "backend"
$PreferredVenvActivate = Join-Path $BackendDir ".venv\Scripts\Activate.ps1"
$LegacyVenvActivate = Join-Path $BackendDir "venv\Scripts\Activate.ps1"
$BackendUrl = "http://localhost:8000"
$HealthUrl = "$BackendUrl/health"
$HealthTimeoutSeconds = 10

function Stop-WithMessage {
    param([string]$Message)

    Write-Host $Message -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

function Get-VenvActivatePath {
    if (Test-Path -LiteralPath $PreferredVenvActivate) {
        return $PreferredVenvActivate
    }

    if (Test-Path -LiteralPath $LegacyVenvActivate) {
        Write-Host "Warning: backend\.venv was not found; using existing backend\venv." -ForegroundColor Yellow
        return $LegacyVenvActivate
    }

    Stop-WithMessage "Backend failed to start: missing backend\.venv\Scripts\Activate.ps1"
}

function Test-BackendHealth {
    try {
        $Response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 1
        return ($Response.StatusCode -ge 200 -and $Response.StatusCode -lt 300)
    } catch {
        $script:LastHealthError = $_.Exception.Message
        return $false
    }
}

if (-not (Test-Path -LiteralPath $BackendDir)) {
    Stop-WithMessage "Backend failed to start: backend directory not found."
}

Set-Location -LiteralPath $BackendDir
if (-not $env:CORS_ORIGINS) {
    $env:CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
}

Write-Host "Backend starting..." -ForegroundColor Cyan

$LastHealthError = ""
if (Test-BackendHealth) {
    Write-Host "Backend is LIVE at $BackendUrl" -ForegroundColor Green
    Write-Host "Existing backend responded successfully; no duplicate uvicorn process was started." -ForegroundColor Yellow
    Read-Host "Press Enter to close"
    exit 0
}

$VenvActivate = Get-VenvActivatePath
. $VenvActivate

$UvicornCommand = Get-Command "uvicorn" -ErrorAction SilentlyContinue
if ($null -eq $UvicornCommand) {
    Stop-WithMessage "Backend failed to start: uvicorn was not found in the active virtual environment."
}

try {
    $BackendProcess = Start-Process `
        -FilePath $UvicornCommand.Source `
        -ArgumentList @("main:app", "--reload", "--port", "8000") `
        -WorkingDirectory $BackendDir `
        -NoNewWindow `
        -PassThru
} catch {
    Stop-WithMessage "Backend failed to start: $($_.Exception.Message)"
}

$Deadline = (Get-Date).AddSeconds($HealthTimeoutSeconds)
$IsHealthy = $false

while ((Get-Date) -lt $Deadline) {
    if ($BackendProcess.HasExited) {
        Stop-WithMessage "Backend failed to start or /health not reachable. uvicorn exited with code $($BackendProcess.ExitCode)."
    }

    if (Test-BackendHealth) {
        $IsHealthy = $true
        break
    }

    Start-Sleep -Seconds 1
}

if (-not $IsHealthy) {
    Write-Host "Backend failed to start or /health not reachable" -ForegroundColor Red
    if ($LastHealthError) {
        Write-Host "Last health check error: $LastHealthError" -ForegroundColor Red
    }
    if (-not $BackendProcess.HasExited) {
        Write-Host "Stopping backend process after failed health check." -ForegroundColor Yellow
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host "Backend is LIVE at $BackendUrl" -ForegroundColor Green

Wait-Process -Id $BackendProcess.Id
$BackendProcess.Refresh()

if ($BackendProcess.ExitCode -ne 0 -and $null -ne $BackendProcess.ExitCode) {
    Write-Host "Backend process exited with code $($BackendProcess.ExitCode)." -ForegroundColor Red
} else {
    Write-Host "Backend process stopped." -ForegroundColor Yellow
}

Read-Host "Press Enter to close"
