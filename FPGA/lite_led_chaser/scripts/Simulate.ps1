[CmdletBinding()]
param([string]$VivadoRoot = 'D:\Xilinx\Vivado\2019.1')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $projectRoot ('runs\sim_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + [Guid]::NewGuid().ToString('N').Substring(0, 6))
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot 'rtl\lite_led_chaser.v'), (Join-Path $projectRoot 'sim\tb_lite_led_chaser.sv'), (Join-Path $PSScriptRoot 'sim.tcl') -Destination $runDir
Push-Location -LiteralPath $runDir
try {
    & (Join-Path $VivadoRoot 'bin\xvlog.bat') --sv lite_led_chaser.v tb_lite_led_chaser.sv *> compile.stdout.log
    if ($LASTEXITCODE -ne 0) { throw 'XSim compilation failed.' }
    & (Join-Path $VivadoRoot 'bin\xelab.bat') tb_lite_led_chaser -s led_chaser_tb *> elaborate.stdout.log
    if ($LASTEXITCODE -ne 0) { throw 'XSim elaboration failed.' }
    & (Join-Path $VivadoRoot 'bin\xsim.bat') led_chaser_tb -tclbatch sim.tcl *> simulate.stdout.log
    if ($LASTEXITCODE -ne 0) { throw 'XSim simulation failed.' }
    $simulationLog = Get-Content -LiteralPath 'simulate.stdout.log' -Raw
    if ($simulationLog -notmatch 'PASS: initialization' -or $simulationLog -match 'FAIL|Fatal:|ERROR:') {
        throw 'Self-checking testbench did not pass.'
    }
    Write-Output 'SIMULATION_PASS'
    Write-Output "Simulation directory: $runDir"
    Get-Content -LiteralPath 'simulate.stdout.log'
} finally { Pop-Location }
