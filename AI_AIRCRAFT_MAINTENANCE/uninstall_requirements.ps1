$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RequirementsFile = Join-Path $ScriptDir "requirements.txt"

if (-not (Test-Path $RequirementsFile)) {
    Write-Error "Requirements file not found: $RequirementsFile"
    exit 1
}

Write-Host "Uninstalling libraries from $RequirementsFile..." -ForegroundColor Cyan

# Use pip uninstall -r to uninstall everything listed in the requirements file
# -y flag is used to automatically confirm uninstallation
python -m pip uninstall -r "$RequirementsFile" -y

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully uninstalled libraries." -ForegroundColor Green
} else {
    Write-Error "An error occurred during uninstallation."
}
