param(
    [string]$SdkDirectory = 'C:/Program Files/Microsoft SDKs/Kinect/v2.0_1409',
    [string]$OutputDirectory = (Join-Path $PSScriptRoot '../../.local/kinect-check-20261028-r1/bin')
)
$ErrorActionPreference = 'Stop'
$kinectAssembly = Join-Path $SdkDirectory 'Assemblies/Microsoft.Kinect.dll'
$kinectCompiler = 'C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe'
if (!(Test-Path -LiteralPath $kinectAssembly)) { throw "Kinect v2 SDK assembly not found: $kinectAssembly" }
if (!(Test-Path -LiteralPath $kinectCompiler)) { throw 'The .NET Framework x64 C# compiler is unavailable.' }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$kinectExe = Join-Path $OutputDirectory 'ExportBodies.exe'
& $kinectCompiler /nologo /target:exe /platform:x64 /optimize+ /r:System.Web.Extensions.dll "/r:$kinectAssembly" "/out:$kinectExe" (Join-Path $PSScriptRoot 'ExportBodies.cs')
if ($LASTEXITCODE -ne 0) { throw "C# compilation failed: $LASTEXITCODE" }
Copy-Item -LiteralPath $kinectAssembly -Destination (Join-Path $OutputDirectory 'Microsoft.Kinect.dll') -Force
Get-Item -LiteralPath $kinectExe | Select-Object FullName,Length
$kinectSnapshotSource = Join-Path $PSScriptRoot 'Snapshot.cs'
if (Test-Path -LiteralPath $kinectSnapshotSource) {
    $kinectSnapshotExe = Join-Path $OutputDirectory 'Snapshot.exe'
    & $kinectCompiler /nologo /target:exe /platform:x64 /optimize+ /r:System.Drawing.dll "/r:$kinectAssembly" "/out:$kinectSnapshotExe" $kinectSnapshotSource
    if ($LASTEXITCODE -ne 0) { throw "Snapshot compilation failed: $LASTEXITCODE" }
}
