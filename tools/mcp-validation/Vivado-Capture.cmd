@echo off
rem User-approved temporary startup capture, executed 2026-10-01.
setlocal
cd /d "D:\FPGACompetitionProject\tools\mcp-validation"
call "D:\Xilinx\Vivado\2019.1\bin\vivado.bat" %* -source "D:/FPGACompetitionProject/tools/mcp-validation/vivado_probe_exit.tcl" 1>"D:\FPGACompetitionProject\tools\mcp-validation\vivado-from-codex.stdout.log" 2>"D:\FPGACompetitionProject\tools\mcp-validation\vivado-from-codex.stderr.log"
set "vivadoProbeExit=%errorlevel%"
type "D:\FPGACompetitionProject\tools\mcp-validation\vivado-from-codex.stdout.log"
type "D:\FPGACompetitionProject\tools\mcp-validation\vivado-from-codex.stderr.log" 1>&2
exit /b %vivadoProbeExit%
