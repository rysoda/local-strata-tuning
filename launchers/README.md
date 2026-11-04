# Windows launchers

[Campaign index](../README.md) · [Shared launch utility](../tools/README.md)

- **[Run-P100-1080Ti-X8.cmd](Run-P100-1080Ti-X8.cmd)**: x8/x8 recommendation, engine/Control 0.1.55, now starts with **262144 context** by user request. Applies a runtime override; archived 128K profiles remain unchanged. [Two quick capacity screens](../campaigns/2026-11-02-p100-1080ti-x8-x8/QUICK_CONTEXT_CHECK.md) found little short-workload speed difference; full 256K recall/quality is not validated.
- [Run-1080Ti.cmd](Run-1080Ti.cmd): historical single-card recommendation. Requires original Control 0.1.51, which is no longer installed locally. No silent substitution.

Launchers resolve the repository relative to their own location and can be invoked from another working directory. Pass `--check` to validate profile, credentials and installed paths without writing runtime files or starting a server. Actual launch uses localhost:8080 and refuses an existing server rather than stopping it. Credential-bearing runtime configs remain inside the campaign's ignored `configs/private/` directory.

Machine-specific paths are deliberately not guessed when an installation or model has moved. Adapt a private profile deliberately, or restore the validated installation; changed software should be benchmarked as a new comparison.
