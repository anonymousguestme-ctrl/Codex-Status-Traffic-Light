param(
    [switch]$DryRun,
    [switch]$Once
)

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectDir '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $VenvPython)) {
    $PythonCommand = Get-Command python -ErrorAction Stop
    & $PythonCommand.Source -m venv (Join-Path $ProjectDir '.venv')
    & $VenvPython -m pip install -r (Join-Path $ProjectDir 'requirements.txt')
}

$arguments = @(Join-Path $ProjectDir 'src\run_direct.py')
if ($DryRun) { $arguments += '--dry-run' }
if ($Once) { $arguments += '--once' }
& $VenvPython @arguments
