param()

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Pythonw = Join-Path $ProjectDir '.venv\Scripts\pythonw.exe'
$App = Join-Path $ProjectDir 'src\codex_traffic_light.py'

if (-not (Test-Path -LiteralPath $Pythonw)) {
    throw "Python environment is missing. Run $ProjectDir\start.ps1 once first."
}

if (-not (Test-Path -LiteralPath $App)) {
    throw "Traffic-light program is missing: $App"
}

$Existing = @(
    Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe'" |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine.IndexOf($App, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
        }
)

if ($Existing.Count -gt 0) {
    Write-Output "Codex physical traffic light is already active (PID $($Existing[0].ProcessId))."
    exit 0
}

Start-Process -FilePath $Pythonw -ArgumentList @($App) -WorkingDirectory $ProjectDir -WindowStyle Hidden
Start-Sleep -Seconds 2

$Started = @(
    Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe'" |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine.IndexOf($App, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
        }
)

if ($Started.Count -eq 0) {
    throw 'The traffic-light listener exited during startup. Run start.ps1 to see the error.'
}

Write-Output "Codex physical traffic light is active on COM8 (PID $($Started[0].ProcessId))."
