$ErrorActionPreference = 'Stop'

irm https://astral.sh/uv/install.ps1 | iex

$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCommand) {
    & $uvCommand.Source add -r requirements.txt
} else {
    $uvPath = Join-Path $HOME '.local\bin\uv.exe'
    if (-not (Test-Path $uvPath)) {
        throw 'uv was installed, but its executable could not be found.'
    }

    & $uvPath add -r requirements.txt
}
