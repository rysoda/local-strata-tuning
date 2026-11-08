@echo off
rem Launch P100 CPU x16 + 1080 Ti chipset x4 IQ3_S at 256K after Windows sign-in.
rem Benchmark: C:\ai\tuning\campaigns\2026-11-08-p100-1080ti-reserve-performance\REPORT.md
rem GPU 0 P100: layers 0-35; GPU 1 1080 Ti: layers 36-47/Main.
rem Reserves: P100 640 MiB; 1080 Ti 896 MiB; trim duplicate dense stage weights.
rem User-requested experimental speed projection retained; not included in benchmark validation.
rem Preserve the preset's API key, network access and terminal monitor.
rem Prevent saved automatic tuning from overriding the measured settings.
set "STRATA_NO_PRESET=1"
set "PYTHONIOENCODING=utf-8"
timeout /t 30 /nobreak >nul
start "Strata" /D "%USERPROFILE%" "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoExit -ExecutionPolicy Bypass -File "%LOCALAPPDATA%\Strata\terminal\current\bin\strata.ps1" launch --preset "IQ3_S 128K" --yes --context 256k --kv int8 --vision cpu --mtp on --drafting mtp --tune skip --set prefill=auto --set kv-resident=32768 --set spec=4 --set spec-min-p=0.5 --set pool-tasks=36 --set adapt-every=1 --set STRATA_PCIE_BALANCE=1 --set STRATA_ROUTE_PRIOR=0 --set STRATA_ROUTE_TAIL_SKIP=0 --gpu 0,1 --set layer-split=36 --set trim-stage-weights=on --set vram-reserve-mib=640 --set vram-reserve-later-mib=896 --set "control-vector-scaled=%LOCALAPPDATA%\Strata\components\control\0.1.55\data\experimental-speed-projection\Qwen3.8-Flash-Next-experimental-speed-projection.gguf:1.0" --set "control-vector-layer-range=4,44" --set cvec-mode=project --set cvec-dir=per-layer