@echo off
setlocal
if not defined VCROOT set "VCROOT=C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.44.35207"
if not defined SDKROOT set "SDKROOT=C:\Program Files (x86)\Windows Kits\10"
if not defined SDKVER set "SDKVER=10.0.26100.0"
set "PATH=%VCROOT%\bin\HostX64\x64;%SDKROOT%\bin\%SDKVER%\x64;%PATH%"
set "INCLUDE=%VCROOT%\include;%SDKROOT%\Include\%SDKVER%\ucrt;%SDKROOT%\Include\%SDKVER%\shared;%SDKROOT%\Include\%SDKVER%\um"
set "LIB=%VCROOT%\lib\x64;%SDKROOT%\Lib\%SDKVER%\ucrt\x64;%SDKROOT%\Lib\%SDKVER%\um\x64"
if not exist windows-wheel-check\chroma-build mkdir windows-wheel-check\chroma-build
pushd windows-wheel-check\chroma-build
cl.exe /nologo /LD /EHsc /O2 /DNDEBUG /D_USE_MATH_DEFINES /I..\vamp-plugin-sdk /I..\nnls-chroma-src /I..\..\.runtime\Library\include ^
 ..\nnls-chroma-src\nnls.c ^
 ..\vamp-plugin-sdk\src\vamp-sdk\FFT.cpp ..\vamp-plugin-sdk\src\vamp-sdk\PluginAdapter.cpp ..\vamp-plugin-sdk\src\vamp-sdk\RealTime.cpp ^
 ..\nnls-chroma-src\NNLSBase.cpp ..\nnls-chroma-src\NNLSChroma.cpp ..\nnls-chroma-src\Chordino.cpp ..\nnls-chroma-src\Tuning.cpp ..\nnls-chroma-src\chromamethods.cpp ..\nnls-chroma-src\viterbi.cpp ..\nnls-chroma-src\plugins.cpp ^
 /link /OUT:nnls-chroma.dll /EXPORT:vampGetPluginDescriptor
set "RESULT=%errorlevel%"
popd
exit /b %RESULT%
