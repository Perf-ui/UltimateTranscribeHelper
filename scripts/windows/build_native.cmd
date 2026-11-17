@echo off
setlocal
if not defined VCROOT set "VCROOT=C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.44.35207"
if not defined SDKROOT set "SDKROOT=C:\Program Files (x86)\Windows Kits\10"
if not defined SDKVER set "SDKVER=10.0.26100.0"
set "PATH=%VCROOT%\bin\HostX64\x64;%SDKROOT%\bin\%SDKVER%\x64;%PATH%"
set "INCLUDE=%VCROOT%\include;%SDKROOT%\Include\%SDKVER%\ucrt;%SDKROOT%\Include\%SDKVER%\shared;%SDKROOT%\Include\%SDKVER%\um;%SDKROOT%\Include\%SDKVER%\winrt"
set "LIB=%VCROOT%\lib\x64;%SDKROOT%\Lib\%SDKVER%\ucrt\x64;%SDKROOT%\Lib\%SDKVER%\um\x64"
set DISTUTILS_USE_SDK=1
set MSSdk=1
set "PYTHON_RUNTIME=.runtime"
if not "%~1"=="" set "PYTHON_RUNTIME=%~1"
set "INCLUDE=%CD%\%PYTHON_RUNTIME%\include\cpython;%INCLUDE%"
if not defined MADMOM_SOURCE set "MADMOM_SOURCE=windows-wheel-check\madmom-0.16.1.tar.gz"
%PYTHON_RUNTIME%\python.exe -m pip install --no-cache-dir --no-deps --no-build-isolation %MADMOM_SOURCE%
if errorlevel 1 exit /b %errorlevel%
set "CL=/Dssize_t=__int64"
%PYTHON_RUNTIME%\python.exe -m pip install --no-cache-dir --no-deps --no-build-isolation windows-wheel-check\vamp-1.1.0.tar.gz
exit /b %errorlevel%
