# Assembles the SafeLayer engine package from a CMake install tree.
#
#   pwsh safelayer/package.ps1 -InstallDir stage -Version 1.5.4 -OutDir dist
#
# The package holds only what SafeLayer AV runs, plus everything the licences
# require to travel with the binaries. A missing required file stops the build.
param(
    [Parameter(Mandatory = $true)][string]$InstallDir,
    [Parameter(Mandatory = $true)][string]$Version,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [string]$SourceUrl = "https://github.com/porhong/SafeLayerAVEngin",
    [string]$SourceRef = "",
    [string]$SourceCommit = ""
)

$ErrorActionPreference = "Stop"

$install = (Resolve-Path $InstallDir).Path
$packageName = "safelayer-engine-$Version.win.x64"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$out = (Resolve-Path $OutDir).Path
$stage = Join-Path $out $packageName
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force $stage | Out-Null

# Programs SafeLayer AV starts. Names are set in the CMake files of this fork.
$programs = @("slengine.exe", "slscan.exe", "slscanc.exe", "slupdate.exe")
# Licence material that must ship with the binaries (GPLv2 section 1 and 3).
$required = $programs + @("COPYING.txt", "COPYING", "certs")

foreach ($name in $required) {
    $path = Join-Path $install $name
    if (-not (Test-Path $path)) {
        throw "Required item is missing from the install tree: $name"
    }
    Copy-Item -Recurse -Force $path $stage
}

# Every DLL: the engine libraries and the third-party runtime they load.
$dlls = Get-ChildItem -Path $install -Filter *.dll -File
if ($dlls.Count -eq 0) { throw "No DLLs found in the install tree." }
$dlls | Copy-Item -Destination $stage -Force

# Upstream tool names must not appear; that would mean the rename did not apply.
foreach ($old in @("clamd.exe", "clamscan.exe", "clamdscan.exe", "freshclam.exe")) {
    if (Test-Path (Join-Path $install $old)) {
        throw "Found $old in the install tree: the SafeLayer file names were not applied."
    }
}

if ((Get-ChildItem -Path (Join-Path $stage "COPYING") -File).Count -eq 0) {
    throw "The COPYING folder is empty."
}

$source = @"
SafeLayer AV Engine $Version

This is a modified build of ClamAV $Version. ClamAV is Copyright (C) Cisco
Systems, Inc. and/or its affiliates, and is licensed under the GNU General
Public License, version 2. See COPYING.txt and the COPYING folder.

Changes from ClamAV $($Version): the program file names and the Windows version
resources. Scanning, signature verification and updating are unchanged.

Complete corresponding source code for this exact build:

  Repository: $SourceUrl
  Ref:        $SourceRef
  Commit:     $SourceCommit

ClamAV is a trademark of Cisco Systems, Inc. This build is not affiliated with,
sponsored by, or endorsed by Cisco.
"@
Set-Content -Path (Join-Path $stage "SOURCE.txt") -Value $source -Encoding utf8

$zip = Join-Path $out "$packageName.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
# Files sit at the top of the archive; SafeLayer AV searches the extracted tree.
Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zip -CompressionLevel Optimal

$hash = (Get-FileHash -Algorithm SHA256 $zip).Hash.ToLower()
Set-Content -Path "$zip.sha256" -Value "$hash  $packageName.zip" -Encoding ascii

Write-Host "Package: $zip"
Write-Host "SHA-256: $hash"
Get-ChildItem $stage | Select-Object Name, Length | Format-Table -AutoSize
