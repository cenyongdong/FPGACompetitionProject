param([int]$Seconds=0,[string]$OutputFile,[string]$StopFile,[switch]$DisableAutoconf,[switch]$DisableBackgroundScan,[switch]$RequestScan,
 [string]$InterfaceId='9b5dab9a-e153-4c95-90f6-8a58e821254e')
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
Add-Type -Path (Join-Path $PSScriptRoot 'WlanDiagnostics.cs')
if($RequestScan){@{scan_request_error=[WlanDiagnostics]::RequestScan($InterfaceId)}|ConvertTo-Json;return}
$result=[WlanDiagnostics]::Run($InterfaceId,$Seconds,$StopFile,[bool]$DisableAutoconf,[bool]$DisableBackgroundScan)|ConvertTo-Json -Depth 9
if($OutputFile){[IO.File]::WriteAllText($OutputFile,$result,[Text.UTF8Encoding]::new($false))}else{$result}
