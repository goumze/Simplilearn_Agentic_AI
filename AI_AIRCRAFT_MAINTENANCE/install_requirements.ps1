$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RequirementsFile = Join-Path $ScriptDir "requirements.txt"

if (-not (Test-Path $RequirementsFile)) {
    Write-Error "Requirements file not found: $RequirementsFile"
    exit 1
}

python -m pip install --upgrade pip
python -m pip install -r "$RequirementsFile"
