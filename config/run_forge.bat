@echo off
REM ============================================================================
REM Forge launcher for this machine.
REM
REM This environment sets NoDefaultCurrentDirectoryInExePath=1, which stops cmd
REM from finding webui-user.bat / webui.bat by relative name (you'd get a
REM "'webui-user.bat' is not recognized" error even while standing in the
REM folder). Clearing it here makes Forge's relative batch calls resolve
REM normally. Also cd into this script's own directory so launch location
REM never matters. Just run this file to start Forge.
REM ============================================================================
set "NoDefaultCurrentDirectoryInExePath="
cd /d "%~dp0."
call webui-user.bat
