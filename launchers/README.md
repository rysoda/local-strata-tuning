# Windows launchers

[Campaign index](../README.md) · [Shared launch utility](../tools/README.md)

- **[Run-P100-1080Ti-X8.cmd](Run-P100-1080Ti-X8.cmd)**: x8/x8 recommendation, engine/Control 0.1.55, now starts with **262144 context** by user request. Applies a runtime override; archived 128K profiles remain unchanged. [Two quick capacity screens](../campaigns/2026-11-02-p100-1080ti-x8-x8/QUICK_CONTEXT_CHECK.md) found little short-workload speed difference; full 256K recall/quality is not validated.
- [Run-1080Ti.cmd](Run-1080Ti.cmd): historical single-card recommendation. Requires original Control 0.1.51, which is no longer installed locally. No silent substitution.

The `Run-*.cmd` launchers resolve the repository relative to their own location and can be invoked from another working directory. Pass `--check` to validate profile, credentials and installed paths without writing runtime files or starting a server. Actual launch uses localhost:8080 and refuses an existing server rather than stopping it. Credential-bearing runtime configs remain inside the campaign's ignored `configs/private/` directory.

## Current Windows Startup deployment

[Startup-Strata-P100-X16-1080Ti-X4-256K.bat](Startup-Strata-P100-X16-1080Ti-X4-256K.bat) is a versioned copy of the user's `shell:startup/strata-start.bat`: P100 CPU x16 / 1080 Ti chipset x4, **36/12 split**, trim, **256K**, reserves **1400/2304 MiB**. It preserves the installed preset's credentials/network behavior, terminal monitor and **experimental speed projection** (scale 1, layers 4–44, project/per-layer) at the user's explicit request. That projection-enabled combination was **not** benchmarked or covered by the campaign's smoke checks. The CLI uses the active installation, unlike the benchmark's explicitly pinned component paths.

This Startup script is not a `Run-*.cmd` recommendation launcher: it waits 30 seconds and launches the normal installed terminal preset, does not accept `--check`, and should not be run alongside a test queue. Copying it to Startup affects the next sign-in; it does not launch now. Original deployed script backup remains ignored/private.

Machine-specific paths are deliberately not guessed when an installation or model has moved. Adapt a private profile deliberately, or restore the validated installation; changed software should be benchmarked as a new comparison.
