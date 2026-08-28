param(
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectDir '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $VenvPython)) {
    $PythonCommand = Get-Command python -ErrorAction Stop
    & $PythonCommand.Source -m venv (Join-Path $ProjectDir '.venv')
    & $VenvPython -m pip install -r (Join-Path $ProjectDir 'requirements.txt')
}

$arguments = @(Join-Path $ProjectDir 'src\install_hooks.py')
if ($Uninstall) { $arguments += '--uninstall' }
& $VenvPython @arguments
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not $Uninstall) {
    Write-Host ''
    Write-Host '下一步：完全退出所有 Codex CLI 窗口，再重新运行 codex。'
    Write-Host 'Codex 首次加载 hook 时会要求审查和信任，请核对路径后选择信任。'
}
