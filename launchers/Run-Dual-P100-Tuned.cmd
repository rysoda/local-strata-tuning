@echo off
setlocal
title Strata - Dual P100 tuned - 256K
"%LOCALAPPDATA%\Strata\components\control\0.1.57\python\python.exe" "%~dp0..\tools\launch.py" 2026-11-13-dual-p100-decode-tuning %*
if errorlevel 1 pause
