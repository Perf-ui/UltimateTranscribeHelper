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
.runtime311\python.exe -m pip install windows-wheel-check\transkun-2.0.1-py3-none-any.whl
exit /b %errorlevel%
