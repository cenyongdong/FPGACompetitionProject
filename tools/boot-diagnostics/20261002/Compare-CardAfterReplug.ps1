$ErrorActionPreference='Stop'
$disks=@(Get-CimInstance Win32_DiskDrive | Where-Object { $_.SerialNumber -and $_.SerialNumber.Trim() -eq '121220160204' })
if($disks.Count -ne 1){throw 'Expected USB reader absent or ambiguous; no files read'}
$disk=$disks[0]
$part=Get-Partition -DiskNumber $disk.Index -PartitionNumber 1
if($part.Offset -ne 1048576 -or $part.Size -ne 1073741824 -or [int][char]$part.DriveLetter -eq 0){throw 'Unexpected FAT partition identity'}
$cardRoot=([string]$part.DriveLetter)+':\'
$diagDir='D:\FPGACompetitionProject\tools\boot-diagnostics\20261002'
$manifest=Get-Content -LiteralPath (Join-Path $diagDir 'source-boot-manifest.json') -Raw | ConvertFrom-Json
$results=@()
foreach($file in Get-ChildItem -LiteralPath $cardRoot -File){
 $hash=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
 $source=@($manifest.files | Where-Object {$_.size -eq $file.Length -and $_.sha256 -eq $hash})
 $results+=[ordered]@{name=$file.Name;size=$file.Length;sha256=$hash;matches_source=($source.Count -gt 0)}
}
if($results.Count -ne 9){throw 'Unexpected boot file count'}
$report=[ordered]@{timestamp=(Get-Date).ToString('o');after_user_safe_eject_and_usb_replug=$true;reader_serial=$disk.SerialNumber.Trim();disk_number=$disk.Index;card_root=$cardRoot;files=$results}
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $diagDir 'card-after-replug.json') -Encoding utf8
$report | ConvertTo-Json -Depth 5
