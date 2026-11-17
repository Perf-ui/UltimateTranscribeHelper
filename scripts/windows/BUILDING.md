# Building the Windows package

The installer is a single x64 `.exe`; it installs a multi-file application for
the current Windows user. It needs no Docker, Python or compiler on the target
machine. GPU support uses DirectML for UVR separation only. Python and native
build tools are required on the build machine.

**Release gate:** read [the model inventory](../../docs/WINDOWS_MODELS.md).
The current bundle contains model files with noncommercial or unconfirmed
redistribution terms. Do not publish it until those rights and the third-party
licence/source obligations have been resolved. The installer is unsigned.

## Known working build environment

This workspace contains `.runtime311`, a Python 3.11 x64 environment with the
versions in `requirements-windows.lock`, CPU PyTorch 2.5.1 and torchaudio
2.5.1, plus ONNX Runtime DirectML 1.20.1. It also has the model weights, the
NNLS Chroma DLL and source trees listed below. `build_portable.py` checks for
these prerequisites; it does not install them.

Recreating that environment from a clean machine is **not yet automated or
verified**. In particular, `madmom`, `vamp` and `ncls` required local Windows
native builds; merely running `pip install -r requirements-windows.lock` is
not a verified bootstrap. Preserve a known-good runtime and the local source
archives until a clean bootstrap is implemented. The lock is a version
inventory, not a hash-locked reproducible build.

For reconstruction, use 64-bit Python 3.11, MSVC v143 x64 C++ tools, a
Windows SDK, and the CPU PyTorch wheels from the official PyTorch index. Install
the versions in the lock; do not install CPU `onnxruntime` alongside
`onnxruntime-directml` because both provide the same Python module. The helper
scripts `build_native.cmd`, `build_transkun.cmd` and `build_chroma.cmd` show
the native build commands, but expect local source archives and build paths;
set `VCROOT`, `SDKROOT`, `SDKVER` and `MADMOM_SOURCE` for the machine. NNLS
Chroma additionally needs Boost 1.85 headers. See
`omnizart/resource/vamp/BUILD.md` for upstream source revisions and licence.
Inno Setup 7's `ISCC.exe` is needed for the installer.

## Models and plugin source

The source tree needs the full Omnizart checkpoints in `omnizart/checkpoints`,
including the accompanying configuration and SavedModel files. The upstream
weight assets are listed in `omnizart/cli/cli.py` and can be downloaded with
the application's `download-checkpoints` command once its runtime works.
The [model inventory](../../docs/WINDOWS_MODELS.md) lists the other model
sources and locations. The UVR checkpoint must be placed at
`omnizart/checkpoints/vocal/UVR-MDX-NET-Inst_HQ_3.onnx`; its expected SHA-256
is `317554b07fe1ea5279a77f2b1520a41ea4b93432560c4ffd08792c30fddf9adc`.
The Spleeter ONNX archive must be extracted to the directory described in the
inventory. The Transkun and Basic Pitch checkpoints come with their packages.

Place the NNLS Chroma and Vamp SDK source checkouts at
`windows-wheel-check/nnls-chroma-src` and `windows-wheel-check/vamp-plugin-sdk`;
the portable builder includes them to accompany the GPL plugin. Install the
compiled plugin at `omnizart/resource/vamp/nnls-chroma.dll`.

## Build and validate from the prepared workspace

From the repository root in PowerShell, with all prerequisites above present:

```powershell
.\.runtime311\python.exe -m pip check
.\.runtime311\python.exe scripts\windows\build_portable.py .runtime311 Omnizart-Windows-Release
powershell -ExecutionPolicy Bypass -File scripts\windows\build_installer.ps1 -PortableFolder dist\Omnizart-Windows-Release
```

The portable builder refuses to overwrite an existing destination. The
installer builder refuses to overwrite an existing EXE; pass `-OutputBaseName`
for another name, or `-Compiler` for an Inno Setup compiler outside its search
paths. The default installer is `dist\Omnizart-Windows-Setup-2.7.exe`.

Run the unit tests and test the portable GUI with CPU and, when available,
GPU. Test a fresh install, upgrade from a previous version, uninstall, and the
installed GUI in a Windows test account before distributing. The app ID must
remain unchanged for future upgrades. The setup preserves the previous install
directory and per-user settings in `%LOCALAPPDATA%\Omnizart`; close the app
before upgrading. It does not migrate arbitrary manually modified runtime files.
