# Read-only inventory for the known MT7922 transmitter; run after SSH is available.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
if ($env:COMPUTERNAME -ne 'DESKTOP-V4Q9HC6') {
    throw 'Unexpected computer; no transmitter operations permitted'
}
$taskAdapters = @(Get-NetAdapter | Where-Object {
    $_.InterfaceDescription -eq 'MediaTek Wi-Fi 6E MT7922 160MHz Wireless LAN Card'
})
if ($taskAdapters.Count -ne 1) { throw 'Expected one physical MT7922 adapter' }
$taskAdapter = $taskAdapters[0]
$taskDriver = @(Get-CimInstance Win32_PnPSignedDriver -Filter "DeviceName LIKE '%MT7922%'" |
    Select-Object DeviceID, DeviceName, DriverVersion, DriverDate)
if ($taskDriver.Count -ne 1 -or $taskDriver[0].DeviceID -notlike 'PCI\VEN_14C3&DEV_7922&SUBSYS_59111A3B*') {
    throw 'MT7922 PCI identity differs from the verified laptop'
}
$taskPrincipal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
$taskResult = [ordered]@{
    computer_name = $env:COMPUTERNAME
    identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    administrator = $taskPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    os = Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber
    adapter = $taskAdapter | Select-Object Name, InterfaceDescription, InterfaceGuid, InterfaceIndex, MacAddress, Status, LinkSpeed
    driver = $taskDriver
    ipv4 = @(Get-NetIPAddress -InterfaceIndex $taskAdapter.InterfaceIndex -AddressFamily IPv4 |
        Select-Object IPAddress, PrefixLength, AddressState)
    wifi = @(netsh wlan show interfaces)
    advanced_properties = @(Get-NetAdapterAdvancedProperty -Name $taskAdapter.Name -AllProperties |
        Where-Object { $_.DisplayName -or $_.RegistryKeyword -eq 'WirelessMode' } |
        Select-Object DisplayName, DisplayValue, RegistryKeyword, RegistryValue, ValidDisplayValues, ValidRegistryValues)
}
$taskResult | ConvertTo-Json -Depth 8
