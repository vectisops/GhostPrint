$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Push-Location $repositoryRoot

try {
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        python -m PyInstaller --clean --noconfirm --onefile --windowed --name GhostPrint gui.py 2>&1
        $guiBuildExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($guiBuildExitCode -ne 0) {
        throw "PyInstaller failed while packaging GhostPrint."
    }

    $ErrorActionPreference = "Continue"
    try {
        $entrypointText = & python -c "from importlib.metadata import distribution; print(next(ep.value for ep in distribution('mvt').entry_points if ep.name == 'mvt-ios'))" 2>&1
        $entrypointExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($entrypointExitCode -ne 0 -or -not $entrypointText) {
        throw "Could not locate the installed mvt-ios entry point."
    }
    $entrypointParts = $entrypointText -split ":", 2
    if ($entrypointParts.Length -ne 2) {
        throw "The mvt-ios entry point has an unsupported format."
    }
    $entryModule = $entrypointParts[0]
    $entryFunction = ($entrypointParts[1] -split "\[", 2)[0]
    $buildDirectory = Join-Path $repositoryRoot "build"
    New-Item -ItemType Directory -Force -Path $buildDirectory | Out-Null
    $entryScriptPath = Join-Path $buildDirectory "mvt-ios-entrypoint.py"
    $entryScript = "import sys`nfrom $entryModule import $entryFunction`nsys.exit($entryFunction())`n"
    Set-Content -Path $entryScriptPath -Value $entryScript -Encoding utf8

    $ErrorActionPreference = "Continue"
    try {
        python -m PyInstaller --clean --noconfirm --onefile --name mvt-ios --collect-all mvt --copy-metadata mvt $entryScriptPath 2>&1
        $mvtBuildExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($mvtBuildExitCode -ne 0) {
        throw "PyInstaller failed while packaging MVT."
    }
}
finally {
    Pop-Location
}
