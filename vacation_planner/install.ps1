$ErrorActionPreference = 'Stop'

irm https://astral.sh/uv/install.ps1 | iex

$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCommand) {
    $uvExe = $uvCommand.Source
} else {
    $uvExe = Join-Path $HOME '.local\bin\uv.exe'
    if (-not (Test-Path $uvExe)) {
        throw 'uv was installed, but its executable could not be found.'
    }
}

# Installs all requirements, including crewai (last entry).
& $uvExe add -r requirements.txt

& $uvExe tool install crewai

& $uvExe tool list
& $uvExe tool update-shell