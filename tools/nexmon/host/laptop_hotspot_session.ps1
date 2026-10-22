# Existing WinRT API only. Session band selection never persists a passphrase.
param(
 [ValidateSet('Probe','Start','Stop','Status','RestoreBand')][string]$Action='Probe',
 [string]$PublicAdapterId='2c8bfa20-71d6-4d35-bfc6-a8c4e53cff33',
 [ValidateSet('Auto','TwoPointFourGigahertz','FiveGigahertz','SixGigahertz')][string]$OriginalBand
)
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null=[Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]
$null=[Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]
$null=[Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]
$null=[Windows.Networking.NetworkOperators.NetworkOperatorTetheringSessionAccessPointConfiguration,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]
$profiles=@([Windows.Networking.Connectivity.NetworkInformation]::GetConnectionProfiles()|Where-Object {$_.NetworkAdapter.NetworkAdapterId.ToString() -eq $PublicAdapterId})
if($profiles.Count -ne 1){throw 'Expected wired public profile is unavailable or ambiguous'}
$manager=[Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::CreateFromConnectionProfile($profiles[0])
$configuration=$manager.GetCurrentAccessPointConfiguration()
$taskMethod=@([System.WindowsRuntimeSystemExtensions].GetMethods()|Where-Object {$_.Name -eq 'AsTask' -and $_.IsGenericMethodDefinition -and $_.GetParameters().Count -eq 1 -and $_.GetGenericArguments().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'})[0]
function Wait-Tethering($Operation){
 $task=$taskMethod.MakeGenericMethod([Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult]).Invoke($null,@($Operation))
 if(-not $task.Wait(20000)){throw 'WinRT operation still pending; inspect actual state before another operation'}
 return $task.Result
}
$operation=$null
if($Action -eq 'Start'){
 if($manager.TetheringOperationalState.ToString() -ne 'Off'){throw 'A hotspot is already active; do not replace it'}
 if(-not $configuration.IsBandSupported([Windows.Networking.NetworkOperators.TetheringWiFiBand]::FiveGigahertz)){throw '5GHz unsupported'}
 $session=[Windows.Networking.NetworkOperators.NetworkOperatorTetheringSessionAccessPointConfiguration]::new()
 $session.Ssid=$configuration.Ssid
 $session.Passphrase=$configuration.Passphrase
 $session.Band=[Windows.Networking.NetworkOperators.TetheringWiFiBand]::FiveGigahertz
 $session.AuthenticationKind=$configuration.AuthenticationKind
 $operation=Wait-Tethering ($manager.StartTetheringAsync($session))
 $session=$null
}elseif($Action -eq 'Stop' -and $manager.TetheringOperationalState.ToString() -ne 'Off'){
 $operation=Wait-Tethering ($manager.StopTetheringAsync())
}elseif($Action -eq 'RestoreBand'){
 if(-not $OriginalBand){throw 'Restoration needs the recorded original band'}
 if($manager.TetheringOperationalState.ToString() -ne 'Off'){throw 'Stop the owned test hotspot before restoring its band'}
 if($configuration.Band.ToString() -ne $OriginalBand){
  # Preserve SSID/authentication/passphrase inside the existing WinRT object.
  # Some driver/adapter restarts expose a changed saved band even after a
  # session-only start; restore the observed original instead of assuming it.
  $configuration.Band=[Enum]::Parse([Windows.Networking.NetworkOperators.TetheringWiFiBand],$OriginalBand)
  $method=@([System.WindowsRuntimeSystemExtensions].GetMethods()|Where-Object {$_.Name -eq 'AsTask' -and -not $_.IsGenericMethodDefinition -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'})[0]
  $task=$method.Invoke($null,@($manager.ConfigureAccessPointAsync($configuration)))
  if(-not $task.Wait(20000)){throw 'Band restore still pending; inspect actual state before another operation'}
  $task.GetAwaiter().GetResult()
 }
}
$current=$manager.GetCurrentAccessPointConfiguration()
@{action=$Action;operation_status=if($operation){$operation.Status.ToString()}else{$null};operation_message=if($operation){$operation.AdditionalErrorMessage}else{$null};state=$manager.TetheringOperationalState.ToString();ssid=$current.Ssid;reported_band=$current.Band.ToString();clients=@($manager.GetTetheringClients()|ForEach-Object {@{mac=$_.MacAddress;hosts=@($_.HostNames|ForEach-Object {$_.CanonicalName})}});adapters=@(Get-NetAdapter -IncludeHidden|Where-Object {$_.InterfaceDescription -like '*Wi-Fi Direct*' -or $_.Name -eq 'WLAN'}|Select-Object Name,InterfaceGuid,InterfaceDescription,ifIndex,MacAddress,Status);ipv4=@(Get-NetIPAddress -AddressFamily IPv4|Where-Object {$_.IPAddress -like '192.168.137.*' -or $_.InterfaceAlias -eq 'WLAN'}|Select-Object InterfaceAlias,InterfaceIndex,IPAddress,AddressState)}|ConvertTo-Json -Depth 6
if($operation -and $operation.Status.ToString() -ne 'Success'){exit 2}
