param([ValidateSet('enable','disable')][string]$Action,[Parameter(Mandatory=$true)][string]$Work,[string]$RuleName='KinectCSI-Direct-20261028-r1')
$ErrorActionPreference='Stop'
$kinectNetworkWork=(Resolve-Path -LiteralPath $Work).Path
$kinectNetworkState=Join-Path $kinectNetworkWork 'pc-network.json'
$kinectCaptureAddress='192.168.50.49'
$kinectFirewallName=$RuleName
if($Action -eq 'enable') {
    if(Test-Path -LiteralPath $kinectNetworkState){throw 'Inspect the existing network ownership record before enabling again.'}
    $kinectInterface=Get-NetIPAddress -AddressFamily IPv4 -IPAddress '192.168.50.102' -ErrorAction Stop
    if(@(Get-NetIPAddress -AddressFamily IPv4 -IPAddress $kinectCaptureAddress -ErrorAction SilentlyContinue).Count){throw 'Capture IP already exists; do not reuse it implicitly.'}
    if(Test-Connection -TargetName $kinectCaptureAddress -Count 1 -TimeoutSeconds 1 -Quiet -ErrorAction SilentlyContinue){throw 'Capture address responds; no address change.'}
    $kinectState=@{address=$kinectCaptureAddress;interface_index=$kinectInterface.InterfaceIndex;address_added=$false;firewall_rule=$kinectFirewallName;firewall_added=$false;active_store_only=$true;started_utc=[DateTime]::UtcNow.ToString('o')}
    $kinectState | ConvertTo-Json | Set-Content -LiteralPath $kinectNetworkState -Encoding UTF8
    try {
        New-NetIPAddress -InterfaceIndex $kinectInterface.InterfaceIndex -IPAddress $kinectCaptureAddress -PrefixLength 24 -SkipAsSource $true -PolicyStore ActiveStore | Out-Null
        $kinectState.address_added=$true;$kinectState | ConvertTo-Json | Set-Content -LiteralPath $kinectNetworkState -Encoding UTF8
        $kinectAddressDeadline=[System.Diagnostics.Stopwatch]::StartNew()
        do {
            $kinectAddressState=Get-NetIPAddress -InterfaceIndex $kinectInterface.InterfaceIndex -IPAddress $kinectCaptureAddress -ErrorAction Stop
            if($kinectAddressState.AddressState -eq 'Duplicate'){throw 'Temporary capture address conflict; no receiver started.'}
            if($kinectAddressState.AddressState -eq 'Preferred'){break}
            if($kinectAddressDeadline.Elapsed.TotalSeconds -ge 10){throw 'Temporary capture address did not become Preferred within 10 seconds.'}
            Start-Sleep -Milliseconds 200
        } while($true)
        New-NetFirewallRule -Name $kinectFirewallName -DisplayName 'Temporary Kinect CSI direct collection' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 39033 -LocalAddress $kinectCaptureAddress -RemoteAddress @('192.168.50.1','192.168.50.3','192.168.50.4') -Profile Any | Out-Null
        $kinectState.firewall_added=$true;$kinectState | ConvertTo-Json | Set-Content -LiteralPath $kinectNetworkState -Encoding UTF8
    }catch{$_ | Out-String | Set-Content -LiteralPath (Join-Path $kinectNetworkWork 'pc-network-error.txt');throw}
}else{
    $kinectState=Get-Content -LiteralPath $kinectNetworkState -Raw | ConvertFrom-Json
    if($kinectState.firewall_added){Remove-NetFirewallRule -Name $kinectState.firewall_rule -ErrorAction SilentlyContinue}
    if($kinectState.address_added){Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $kinectState.interface_index -IPAddress $kinectState.address -ErrorAction SilentlyContinue | Remove-NetIPAddress -Confirm:$false}
    @{finished_utc=[DateTime]::UtcNow.ToString('o');address_present=[bool](Get-NetIPAddress -IPAddress $kinectState.address -ErrorAction SilentlyContinue);firewall_present=[bool](Get-NetFirewallRule -Name $kinectState.firewall_rule -ErrorAction SilentlyContinue)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $kinectNetworkWork 'pc-network-restored.json') -Encoding UTF8
}
@{action=$Action;completed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $kinectNetworkWork ('pc-network-'+$Action+'-complete.json')) -Encoding UTF8
