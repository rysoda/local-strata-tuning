@echo off
setlocal
title Strata - P100 + GTX 1080 Ti x8/x8
"%LOCALAPPDATA%\Strata\components\control\0.1.55\python\python.exe" "%~dp0..\tools\launch.py" 2026-11-02-p100-1080ti-x8-x8 %*
if errorlevel 1 pause
