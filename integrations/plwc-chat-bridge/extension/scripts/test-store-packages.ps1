[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Import-Module Microsoft.PowerShell.Utility -ErrorAction Stop

function Get-FileSha256 {
    param([Parameter(Mandatory = $true)][string] $Path)

    $hash = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try {
        return [BitConverter]::ToString($hash.ComputeHash($stream)).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $stream.Dispose()
        $hash.Dispose()
    }
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$builder = Join-Path $scriptRoot "build-store-packages.ps1"
$temporaryRoot = Join-Path ([IO.Path]::GetTempPath()) ("plwc-store-package-test-" + [Guid]::NewGuid().ToString("N"))
$temporaryRoot = [IO.Path]::GetFullPath($temporaryRoot)
$temporaryParent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (
    [IO.Path]::GetDirectoryName($temporaryRoot) -ne $temporaryParent -or
    [IO.Path]::GetFileName($temporaryRoot) -notmatch '^plwc-store-package-test-[0-9a-f]{32}$'
) {
    throw "Store package test temporary directory is outside the expected location."
}
$firstOutput = Join-Path $temporaryRoot "first"
$secondOutput = Join-Path $temporaryRoot "second"

try {
    & $builder -OutputDirectory $firstOutput | Out-Null
    & $builder -OutputDirectory $secondOutput -SkipBuild | Out-Null

    $firstFiles = @(Get-ChildItem -LiteralPath $firstOutput -File | Sort-Object Name)
    $secondFiles = @(Get-ChildItem -LiteralPath $secondOutput -File | Sort-Object Name)
    if ($firstFiles.Count -ne 4 -or $secondFiles.Count -ne 4) {
        throw "Store package test expected two ZIPs and two build-identity sidecars per build."
    }
    if ((ConvertTo-Json -Compress @($firstFiles.Name)) -ne (ConvertTo-Json -Compress @($secondFiles.Name))) {
        throw "Store package test builds produced different file inventories."
    }

    foreach ($firstFile in $firstFiles) {
        $secondFile = Join-Path $secondOutput $firstFile.Name
        $firstHash = Get-FileSha256 -Path $firstFile.FullName
        $secondHash = Get-FileSha256 -Path $secondFile
        if ($firstHash -ne $secondHash) {
            throw "Store package output is not reproducible: $($firstFile.Name)"
        }
    }

    $sidecars = @($firstFiles | Where-Object { $_.Name -like '*-build-identity.json' })
    $expectedTargets = @("chrome-brave", "edge")
    foreach ($sidecarFile in $sidecars) {
        $sidecar = Get-Content -LiteralPath $sidecarFile.FullName -Raw | ConvertFrom-Json
        if (
            $sidecar.schemaVersion -ne 2 -or
            $sidecar.product -ne "PLwC Personal Chat Bridge" -or
            $sidecar.releaseVersion -ne "1.0.0" -or
            $sidecar.extensionVersion -ne "2.0.0" -or
            $sidecar.buildId -ne "plwc-chat-bridge@1.0.0" -or
            $sidecar.target -notin $expectedTargets -or
            $sidecar.expectedExtensionId -notmatch '^[a-p]{32}$' -or
            $sidecar.expectedNativeMessagingOrigin -ne "chrome-extension://$($sidecar.expectedExtensionId)/" -or
            $sidecar.entries.Count -ne 12 -or
            $sidecar.entries -notcontains "manifest.json"
        ) {
            throw "Store package build-identity sidecar is invalid: $($sidecarFile.Name)"
        }
        $archivePath = Join-Path $firstOutput $sidecar.archive.fileName
        if (
            -not (Test-Path -LiteralPath $archivePath -PathType Leaf) -or
            $sidecar.archive.fileName -notlike "PLwC-Chat-Bridge-$($sidecar.extensionVersion)-*-store.zip" -or
            (Get-Item -LiteralPath $archivePath).Length -ne $sidecar.archive.bytes -or
            (Get-FileSha256 -Path $archivePath) -ne $sidecar.archive.sha256
        ) {
            throw "Store package sidecar does not bind its archive: $($sidecarFile.Name)"
        }
        $archive = [IO.Compression.ZipFile]::OpenRead($archivePath)
        try {
            $archiveEntries = @($archive.Entries | ForEach-Object { $_.FullName.Replace('\', '/') } | Sort-Object)
        }
        finally {
            $archive.Dispose()
        }
        if ((ConvertTo-Json -Compress $archiveEntries) -ne (ConvertTo-Json -Compress @($sidecar.entries | Sort-Object))) {
            throw "Store package sidecar entries do not match the ZIP: $($sidecarFile.Name)"
        }
    }

    Write-Output "Store package reproducibility, inventory, identity, and secret-scan tests passed."
}
finally {
    if (Test-Path -LiteralPath $temporaryRoot) {
        Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
    }
}
