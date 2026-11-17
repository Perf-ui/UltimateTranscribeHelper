# Windows release checklist

Do not publish the current bundle until the open model and dependency rights
in [WINDOWS_MODELS.md](WINDOWS_MODELS.md) have been resolved. The existing
2.7 installer predates the latest licence-document correction and must be
rebuilt after this review.

## Installer and upgrade

- Use the same Inno Setup `AppId` for future releases. Changing it creates a
  separate installation instead of upgrading the existing one.
- Close Omnizart before running setup. Confirm the existing per-user install is
  detected, the previous custom installation directory is selected, and an
  upgrade does not create a second uninstall entry.
- In a disposable Windows user or VM, install version 2.5, save test preferences
  and an unrelated marker file, then upgrade to the new installer. Check the
  preferences and marker survive, the previous installation directory is
  retained, the old `onnxruntime-1.20.1.dist-info` is removed, and the DirectML
  runtime and CPU fallback both work. Test uninstall afterward.
- The upgrade test changes the Windows uninstall registry; do not run it in a
  user account with a real Omnizart installation unless it is intentionally
  being upgraded. The current workspace contains an isolated test installation
  in `windows-wheel-check/upgrade-test`; uninstall it before conducting a new
  test or relying on that account's Omnizart installation record.
- Check a fresh install, GUI launch, a CPU transcription, optional GPU UVR
  separation, and upgrading from another supported installer version.

## Release files

- Rebuild from the prepared prerequisites following
  [BUILDING.md](../scripts/windows/BUILDING.md), and verify the installer and
  portable tree both contain `MODEL-LICENSES.md`, package notices and the
  required NNLS Chroma source and licence.
- Independently review model redistribution permissions, GPL source and
  notices, and all other bundled dependencies. The version inventory is not a
  complete legal review or a hash-locked reproducible build.
- Publish the corresponding source and licences, and consider signing the
  installer. Check that source archives, build instructions, and model downloads
  are available to the recipient, and create release checksums.
- Record the exact Windows version, hardware, tests and remaining limitations.
