$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RequirementsFile = Join-Path $ScriptDir "backend\requirements.txt"

if (-not (Test-Path $RequirementsFile)) {
    Write-Error "Requirements file not found: $RequirementsFile"
    exit 1
}

$PythonExe = "C:\Users\gm_mi\AppData\Local\Programs\Python\Python312\python.exe"
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r "$RequirementsFile"
