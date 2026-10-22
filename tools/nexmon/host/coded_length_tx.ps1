# Bounded diagnostic on the owned c_iPhone link using installed PowerShell.
# Length coding changes airtime: keep this separate from normal CSI validation.
param(
 [ValidateSet(50,300)][int]$Hz=50,
 [ValidateSet(2,10)][int]$Seconds=2,
 [Parameter(Mandatory=$true)][Guid]$RunId,
 [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$nic=Get-NetAdapter -Name WLAN
if($nic.MacAddress -ne '50-BB-B5-DB-A5-02'){throw 'Unexpected transmitter'}
$addresses=@(Get-NetIPAddress -InterfaceAlias WLAN -AddressFamily IPv4|Where-Object IPAddress -like '172.20.10.*')
if($addresses.Count -ne 1){throw 'Owned phone hotspot IPv4 is required'}
$source=[Net.IPAddress]::Parse($addresses[0].IPAddress)
$target=[Net.IPEndPoint]::new([Net.IPAddress]::Parse('172.20.10.1'),39031)
New-Item -ItemType Directory -Path $OutputDirectory -ErrorAction Stop|Out-Null
$buffers=[Collections.Generic.List[byte[]]]::new()
for($k=0;$k -lt 16;$k++){
 $b=[byte[]]::new(256+8*$k)
 [Array]::Copy([Text.Encoding]::ASCII.GetBytes('CSILEN01'),$b,8)
 [Array]::Copy($RunId.ToByteArray(),0,$b,32,16)
 $buffers.Add($b)
}
$random=[Random]::new(134923)
$codes=[int[]]::new($Hz*$Seconds)
for($i=0;$i -lt $codes.Length;$i++){$codes[$i]=$random.Next(16)}
$rows=[Collections.Generic.List[object]]::new()
$frequency=[Diagnostics.Stopwatch]::Frequency
$origin=[Diagnostics.Stopwatch]::GetTimestamp()
$begin=$origin+[long]($frequency*.2)
$period=$frequency/[double]$Hz
$socket=[Net.Sockets.Socket]::new([Net.Sockets.AddressFamily]::InterNetwork,[Net.Sockets.SocketType]::Dgram,[Net.Sockets.ProtocolType]::Udp)
$socket.SendTimeout=1000
$socket.SetSocketOption([Net.Sockets.SocketOptionLevel]::IP,[Net.Sockets.SocketOptionName]31,[Net.IPAddress]::HostToNetworkOrder([int]$nic.ifIndex))
$socket.Bind([Net.IPEndPoint]::new($source,0))
$process=[Diagnostics.Process]::GetCurrentProcess()
$previous=$process.PriorityClass
$skipped=0;$errorText=$null
try {
 $process.PriorityClass=[Diagnostics.ProcessPriorityClass]::AboveNormal
 for($slot=0;$slot -lt $codes.Length;$slot++){
  $deadline=$begin+[long][Math]::Round($slot*$period)
  while([Diagnostics.Stopwatch]::GetTimestamp() -lt $deadline){[Threading.Thread]::SpinWait(10)}
  $before=[Diagnostics.Stopwatch]::GetTimestamp()
  if(($before-$begin)/$frequency -gt ($Seconds+2)){throw 'Bounded send runtime exceeded'}
  $due=[int][Math]::Floor(($before-$begin)/$period)
  if($due -gt $slot){$skipped += [Math]::Min($due,$codes.Length)-$slot;$slot=$due;if($slot -ge $codes.Length){break};$deadline=$begin+[long][Math]::Round($slot*$period)}
  $b=$buffers[$codes[$slot]]
  [Array]::Copy([BitConverter]::GetBytes([long]$slot),0,$b,8,8)
  $count=$socket.SendTo($b,$target)
  $after=[Diagnostics.Stopwatch]::GetTimestamp()
  $rows.Add(@([long]$slot,[long][Math]::Round(($deadline-$origin)*1e9/$frequency),[long][Math]::Round(($before-$origin)*1e9/$frequency),[long][Math]::Round(($after-$origin)*1e9/$frequency),[long]$count))
 }
} catch {$errorText=$_.Exception.Message}
finally {$process.PriorityClass=$previous;$socket.Dispose()}
@{schema=1;mode='coded_length_diagnostic';id=$RunId.ToString('N');hardware_test=$true;
 source=$source.ToString();destination='172.20.10.1';mac='50BBB5DBA502';requested_hz=$Hz;requested_seconds=$Seconds;
 scheduled_slots=$codes.Length;send_calls_succeeded=$rows.Count;skipped_late_slots=$skipped;error=$errorText;
 schedule_complete=($rows.Count -eq $codes.Length -and $skipped -eq 0 -and $null -eq $errorText);
 clock_origin_qpc=$origin;qpc_frequency=$frequency;clock='QPC nanoseconds relative to origin';
 columns=@('slot','target_ns','before_send_ns','after_send_ns','bytes');sends=@($rows.ToArray());
 limitation='Length coding changes airtime and PowerShell timing differs from the normal sender; not interchangeable with fixed-length captures.'
}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $OutputDirectory 'sender.json') -Encoding UTF8
if($errorText){exit 1}
