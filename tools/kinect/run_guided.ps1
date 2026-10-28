param([Parameter(Mandatory=$true)][string]$Work,[switch]$Silent)
$ErrorActionPreference='Stop'
$guidedWork=(Resolve-Path -LiteralPath $Work).Path
$guidedPython='C:/Users/cenyongdong/miniconda3/envs/torch_gpu/python.exe'
$guidedEnabled=$false;$guidedExit=$null;$guidedError=$null
try{
    $guidedRuleName='KinectCSI-Direct-'+(Split-Path -Leaf $guidedWork).Replace('kinect-csi-direct-','')
    & (Join-Path $PSScriptRoot 'pc_capture_network.ps1') -Action enable -Work $guidedWork -RuleName $guidedRuleName
    $guidedEnabled=$true
    $guidedArguments=@('-B',(Join-Path $PSScriptRoot 'collect_direct.py'),'--output',(Join-Path $guidedWork 'long-01'),'--seconds','300')
    if(!$Silent){$guidedArguments+='--guided'}
    & $guidedPython @guidedArguments *> (Join-Path $guidedWork 'collection-console.log')
    $guidedExit=$LASTEXITCODE
}catch{$guidedError=$_.Exception.ToString();$guidedError|Set-Content -LiteralPath (Join-Path $guidedWork 'run-error.txt')}
finally{
    if($guidedEnabled -or (Test-Path -LiteralPath (Join-Path $guidedWork 'pc-network.json'))){
        & (Join-Path $PSScriptRoot 'pc_capture_network.ps1') -Action disable -Work $guidedWork
    }
    @{collection_exit=$guidedExit;error=$guidedError;finished_utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $guidedWork 'run-result.json') -Encoding UTF8
}
if($guidedError -or $guidedExit -ne 0){exit 1}
