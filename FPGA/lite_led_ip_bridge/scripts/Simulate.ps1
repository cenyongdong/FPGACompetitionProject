[CmdletBinding()]
param([string]$VivadoRoot = 'D:\Xilinx\Vivado\2019.1')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $projectRoot ('runs\sim_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + [Guid]::NewGuid().ToString('N').Substring(0, 6))
New-Item -ItemType Directory -Path $runDir | Out-Null
. (Join-Path $PSScriptRoot 'Stage-Sources.ps1')
Copy-VerifiedDesignSources $projectRoot $runDir
Copy-Item -LiteralPath (Join-Path $projectRoot 'sim\tb_lite_led_chaser.sv'), (Join-Path $PSScriptRoot 'sim.tcl') -Destination $runDir
Push-Location -LiteralPath $runDir
try {
    # Compile the real generated SYNTHESIS wrapper, not the separate sim model.
    & (Join-Path $VivadoRoot 'bin\xvlog.bat') --sv xlconcat_v2_1_vl_rfs.v led_state_concat.v lite_led_chaser.v tb_lite_led_chaser.sv *> compile.stdout.log
    if ($LASTEXITCODE -ne 0) { throw 'XSim compilation failed.' }
    & (Join-Path $VivadoRoot 'bin\xelab.bat') tb_lite_led_chaser -s led_ip_bridge_tb *> elaborate.stdout.log
    if ($LASTEXITCODE -ne 0) { throw 'XSim elaboration failed.' }
    & (Join-Path $VivadoRoot 'bin\xsim.bat') led_ip_bridge_tb -tclbatch sim.tcl *> simulate.stdout.log
    if ($LASTEXITCODE -ne 0) { throw 'XSim simulation failed.' }
    $simulationLog = Get-Content -LiteralPath 'simulate.stdout.log' -Raw
    if ($simulationLog -notmatch 'PASS: initialization' -or
        $simulationLog -notmatch 'PASS: xlconcat all 16 input combinations' -or
        $simulationLog -match 'FAIL|Fatal:|ERROR:') { throw 'Self-checking IP/LED simulation did not pass.' }
    Write-Output 'SIMULATION_PASS'
    Write-Output "Simulation directory: $runDir"
    Get-Content -LiteralPath 'simulate.stdout.log'
} finally { Pop-Location }
