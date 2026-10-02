@echo off
rem User-approved temporary working-directory diagnosis, executed 2026-10-01.
setlocal
cd /d "D:\FPGACompetitionProject\tools\mcp-validation"
echo %CD%>"D:\FPGACompetitionProject\tools\mcp-validation\vivado-diagnostic-cwd.txt"
call "D:\Xilinx\Vivado\2019.1\bin\vivado.bat" %*
exit /b %errorlevel%
