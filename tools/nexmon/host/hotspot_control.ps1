param([ValidateSet('status','stop','start')][string]$Action='status')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Networking.Connectivity.NetworkInformation,Windows,ContentType=WindowsRuntime] | Out-Null
[Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows,ContentType=WindowsRuntime] | Out-Null
[Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult,Windows,ContentType=WindowsRuntime] | Out-Null
$taskProfile=[Windows.Networking.Connectivity.NetworkInformation]::GetConnectionProfiles() | Where-Object ProfileName -eq 'SZU_WLAN' | Select-Object -First 1
if ($null -eq $taskProfile) { throw 'Original SZU_WLAN connection profile unavailable' }
$taskManager=[Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::CreateFromConnectionProfile($taskProfile)
$taskResult=$null
if ($Action -ne 'status') {
    if ($Action -eq 'stop') { $taskOperation=$taskManager.StopTetheringAsync() }
    else { $taskOperation=$taskManager.StartTetheringAsync() }
    $taskBridge=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
    $taskAwait=$taskBridge.MakeGenericMethod([Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult]).Invoke($null,@($taskOperation))
    if (!$taskAwait.Wait(15000)) { throw 'Hotspot operation still pending after 15 seconds' }
    $taskResult=$taskAwait.Result.Status.ToString()
    if ($taskResult -ne 'Success') { throw "Hotspot operation result: $taskResult" }
}
[pscustomobject]@{action=$Action;state=$taskManager.TetheringOperationalState.ToString();result=$taskResult;client_count=$taskManager.ClientCount} | ConvertTo-Json -Compress
