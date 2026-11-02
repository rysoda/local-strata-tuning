@echo off
setlocal
title Strata - P100 + GTX 1080 Ti x8/x8
"%LOCALAPPDATA%\Strata\components\control\0.1.55\python\python.exe" "%~dp0scripts\run_gpu_tuned.py"
if errorlevel 1 pause
