@echo off
rem User-approved temporary child-only architecture verification, executed 2026-10-01.
setlocal
cd /d "D:\FPGACompetitionProject\tools\mcp-validation"
echo PROCESSOR_ARCHITECTURE=%PROCESSOR_ARCHITECTURE%>"D:\FPGACompetitionProject\tools\mcp-validation\vivado-architecture-before.txt"
echo PROCESSOR_ARCHITEW6432=%PROCESSOR_ARCHITEW6432%>>"D:\FPGACompetitionProject\tools\mcp-validation\vivado-architecture-before.txt"
set "PROCESSOR_ARCHITECTURE=AMD64"
call "D:\Xilinx\Vivado\2019.1\bin\vivado.bat" %*
exit /b %errorlevel%
