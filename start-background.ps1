param()

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StartScript = Join-Path $ProjectDir 'start.ps1'
$Installer = Join-Path $ProjectDir 'src\install_hooks.py'
$VenvPython = Join-Path $ProjectDir '.venv\Scripts\python.exe'
$Pythonw = Join-Path $ProjectDir '.venv\Scripts\pythonw.exe'
$App = Join-Path $ProjectDir 'src\codex_traffic_light.py'

if (-not (Test-Path -LiteralPath $StartScript)) { throw "Missing startup script: $StartScript" }
if (-not (Test-Path -LiteralPath $VenvPython)) { & $StartScript -DryRun -Once }
if (-not (Test-Path -LiteralPath $VenvPython)) { throw "Python environment is missing: $VenvPython" }

# Install the project hooks on first launch. The installer preserves unrelated
# user hooks and refreshes the Codex trust definition when necessary.
$InstallMarker = Join-Path $ProjectDir 'runtime\hooks-installed.json'
if (-not (Test-Path -LiteralPath $InstallMarker)) {
    & $VenvPython $Installer
    if ($LASTEXITCODE -ne 0) { throw "Codex hook installation failed." }
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
