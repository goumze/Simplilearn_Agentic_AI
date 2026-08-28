param(
    [switch]$KeepUv
)

$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$requirementsPath = Join-Path $projectPath 'requirements.txt'

$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCommand) {
    $uvPath = $uvCommand.Source
} else {
    $uvPath = Join-Path $HOME '.local\bin\uv.exe'
}

if (-not (Test-Path $uvPath)) {
    throw 'uv could not be found. The project dependencies cannot be removed automatically.'
}

Push-Location $projectPath
try {
    $packages = Get-Content $requirementsPath |
        ForEach-Object { ($_ -split '#', 2)[0].Trim() } |
        Where-Object { $_ -and -not $_.StartsWith('-') } |
        ForEach-Object {
            if ($_ -match '^([A-Za-z0-9][A-Za-z0-9_.-]*)') {
                $matches[1]
            }
        } |
        Sort-Object -Unique

    if ($packages.Count -gt 0) {
        & $uvPath remove $packages
        if ($LASTEXITCODE -ne 0) {
            throw "uv could not remove the project dependencies (exit code $LASTEXITCODE)."
        }
    }
} finally {
    Pop-Location
}

if (-not $KeepUv) {
    $uvDirectory = Split-Path -Parent $uvPath
    Remove-Item $uvPath -Force

    $uvxPath = Join-Path $uvDirectory 'uvx.exe'
    if (Test-Path $uvxPath) {
        Remove-Item $uvxPath -Force
    }

    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    if ($userPath) {
        $pathEntries = $userPath -split ';' | Where-Object {
            $_ -and ([IO.Path]::GetFullPath($_).TrimEnd('\') -ine $uvDirectory.TrimEnd('\'))
        }
        [Environment]::SetEnvironmentVariable('Path', ($pathEntries -join ';'), 'User')
    }
}
