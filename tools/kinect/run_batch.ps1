param([Parameter(Mandatory=$true)][string]$Work)
$ErrorActionPreference='Stop'
$batchWork=(Resolve-Path -LiteralPath $Work).Path
$batchError=$null;$batchExit=$null
try{
    $batchRule='KinectCSI-Direct-'+(Split-Path -Leaf $batchWork).Replace('kinect-csi-direct-','')
    & (Join-Path $PSScriptRoot 'pc_capture_network.ps1') -Action enable -Work $batchWork -RuleName $batchRule
    $batchPanel=Join-Path $PSScriptRoot '../../.local/kinect-check-20261028-r1/bin/CollectionPanel.exe'
    $batchPython='C:/Users/cenyongdong/miniconda3/envs/torch_gpu/python.exe'
    $batchCollector=Join-Path $PSScriptRoot 'collect_direct.py'
    $batchPanelArgs=@(('"'+$batchWork+'"'),('"'+$batchPython+'"'),('"'+$batchCollector+'"'))
    $batchProcess=Start-Process -FilePath $batchPanel -ArgumentList $batchPanelArgs -WindowStyle Normal -Wait -PassThru
    $batchExit=$batchProcess.ExitCode
}catch{$batchError=$_.Exception.ToString();$batchError|Set-Content -LiteralPath (Join-Path $batchWork 'run-error.txt')}
finally{
    if(Test-Path -LiteralPath (Join-Path $batchWork 'pc-network.json')){& (Join-Path $PSScriptRoot 'pc_capture_network.ps1') -Action disable -Work $batchWork}
    @{panel_exit=$batchExit;error=$batchError;finished_utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $batchWork 'run-result.json') -Encoding UTF8
}
if($batchError -or $batchExit -ne 0){exit 1}
