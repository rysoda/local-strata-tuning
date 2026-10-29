@echo off
setlocal
title Strata - validated IQ3_S 128K tuning
set "STRATA_NO_PRESET=1"
set "PYTHONIOENCODING=utf-8"
cd /d "%LOCALAPPDATA%\Strata\components\control\0.1.51"
"%LOCALAPPDATA%\Strata\components\control\0.1.51\python\python.exe" "%~dp0scripts\run_recommended.py"
if errorlevel 1 pause
