$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$distributionDirectory = Join-Path $repositoryRoot "dist"
$installerPath = Join-Path $distributionDirectory "GhostPrint-Setup.exe"
$guidePath = Join-Path $PSScriptRoot "INSTALLATION.txt"
$packagePath = Join-Path $distributionDirectory "GhostPrint-Windows-Download.zip"

if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
    throw "Installer not found. Compile platforms\windows\GhostPrint.iss first."
}
if (-not (Test-Path -LiteralPath $guidePath -PathType Leaf)) {
    throw "Windows installation guide not found."
}

New-Item -ItemType Directory -Force -Path $distributionDirectory | Out-Null
$stagingDirectory = Join-Path $distributionDirectory (".windows-package-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $stagingDirectory | Out-Null

try {
    Copy-Item -LiteralPath $installerPath -Destination (Join-Path $stagingDirectory "GhostPrint-Setup.exe")
    Copy-Item -LiteralPath $guidePath -Destination (Join-Path $stagingDirectory "Installation Guide.txt")
    if (Test-Path -LiteralPath $packagePath) {
        Remove-Item -LiteralPath $packagePath -Force
    }

    Compress-Archive `
        -Path (Join-Path $stagingDirectory "*") `
        -DestinationPath $packagePath `
        -CompressionLevel Optimal

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($packagePath)
    try {
        $entries = @($archive.Entries | ForEach-Object { $_.FullName } | Sort-Object)
        $expectedEntries = @("GhostPrint-Setup.exe", "Installation Guide.txt" | Sort-Object)
        if (($entries -join "`n") -ne ($expectedEntries -join "`n")) {
            throw "Download ZIP contents were not exactly the installer and installation guide."
        }
    }
    finally {
        $archive.Dispose()
    }

    $packageSize = (Get-Item -LiteralPath $packagePath).Length
    Write-Output "Package created: $packagePath ($packageSize bytes)"
}
finally {
    if (Test-Path -LiteralPath $stagingDirectory) {
        Remove-Item -LiteralPath $stagingDirectory -Recurse -Force
    }
}
