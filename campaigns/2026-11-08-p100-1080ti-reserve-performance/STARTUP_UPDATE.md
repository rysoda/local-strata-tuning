# Startup update — 2026-11-08

After reviewing the completed results, user authorized deploying reserve640/896 MiB (P100/1080 Ti).

Updated actual Windows Startup `strata-start.bat` and matching repository copy `../../launchers/Startup-Strata-P100-X16-1080Ti-X4-256K.bat`: only the two reserve values and explanatory reserve/report comments changed. Previous actual launcher preserved in ignored `configs/private/startup-before-reserve-update-20261108-170504.snapshot`.

Retained256K context,36/12 trimmed split, int8 KV/resident32768, full routing, MTP/reasoning, visionCPU, API/network settings, terminal monitor, presets-disabled/tuning-skip behavior and existing experimental projection. Installed profiles untouched. This is a reserve-only Startup update, not replacement with the localhost scientific launcher.

The scientific benchmark used no projection; retaining the existing projection does not validate its quality or guarantee the same measured gains. No server was launched, stopped or restarted. Changes take effect on the next Startup launch (or manual execution of the batch file).

Checked actual launcher matches repository copy and, relative to backup, only the intended replacements occurred. Campaign recommendation resolves with `tools/launch.py --check`; repository validation run without inference. Historical report statements that Startup was unchanged describe campaign completion before this separate user-authorized deployment.
