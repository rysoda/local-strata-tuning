@echo off
setlocal
title Strata - validated GTX 1080 Ti IQ3_S 128K
"%LOCALAPPDATA%\Strata\components\control\0.1.51\python\python.exe" "%~dp0..\tools\launch.py" 2026-10-28-1080ti-tuning %*
if errorlevel 1 pause
