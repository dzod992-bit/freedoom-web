param([int]$Jobs = 4)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
$sdkRoot = Join-Path $projectRoot 'tools/emsdk'
$env:EM_CONFIG = Join-Path $sdkRoot '.emscripten'
$env:PYTHONPATH = Join-Path $projectRoot 'tools/python-packages'
$cmake = Join-Path $env:PYTHONPATH 'cmake/data/bin/cmake.exe'
$ninja = Join-Path $env:PYTHONPATH 'bin/ninja.exe'
if (!(Test-Path $cmake) -or !(Test-Path "$sdkRoot/upstream/emscripten/emcc.exe")) {
    throw 'Missing local tools. See README.md for setup.'
}
python scripts/patch_engine.py
if ($LASTEXITCODE) { throw 'Engine patch failed' }
New-Item -ItemType Directory -Force dist,dist/licenses,dist/source | Out-Null
& $cmake -S . -B build -G Ninja "-DCMAKE_MAKE_PROGRAM=$ninja" "-DCMAKE_TOOLCHAIN_FILE=$sdkRoot/upstream/emscripten/cmake/Modules/Platform/Emscripten.cmake" -DCMAKE_BUILD_TYPE=Release
if ($LASTEXITCODE) { throw 'CMake configure failed' }
& $cmake --build build --target chocolate-doom --parallel $Jobs
if ($LASTEXITCODE) { throw 'Compilation failed' }
Copy-Item web/index.html,web/app.js,web/style.css dist -Force
New-Item -ItemType File -Force dist/.nojekyll | Out-Null
Copy-Item vendor/chocolate-doom/COPYING.md dist/licenses/Chocolate-Doom-GPL.txt -Force
Copy-Item assets/freedoom-0.13.0/COPYING.txt dist/licenses/Freedoom-BSD.txt -Force
Copy-Item assets/freedoom-0.13.0/CREDITS*.txt dist/licenses -Force
$portCache = Join-Path $sdkRoot 'upstream/emscripten/cache/ports'
Copy-Item "$portCache/sdl2/SDL-release-2.32.10/LICENSE.txt" dist/licenses/SDL2.txt -Force
Copy-Item "$portCache/sdl2_mixer/SDL_mixer-release-2.8.0/LICENSE.txt" dist/licenses/SDL2_mixer.txt -Force
Copy-Item "$portCache/ogg/libogg-1.3.5/COPYING" dist/licenses/Ogg.txt -Force
Copy-Item "$portCache/vorbis/libvorbis-1.3.7/COPYING" dist/licenses/Vorbis.txt -Force
Copy-Item "$sdkRoot/upstream/emscripten/LICENSE" dist/licenses/Emscripten.txt -Force
# Corresponding source for the shipped GPL binary, including our build glue.
git -C vendor/chocolate-doom archive --format=tar -o "$projectRoot/dist/source/chocolate-doom.tar" HEAD
if ($LASTEXITCODE) { throw 'Source archive failed' }
git -C vendor/chocolate-doom diff --output="$projectRoot/dist/source/browser.patch"
Copy-Item CMakeLists.txt dist/source -Force
Copy-Item README.md dist/source -Force
Copy-Item web/source.html dist/source/index.html -Force
foreach ($dir in @('port','scripts','web')) {
    New-Item -ItemType Directory -Force "dist/source/$dir" | Out-Null
    Get-ChildItem $dir -File | Copy-Item -Destination "dist/source/$dir" -Force
}
$engineCommit = git -C vendor/chocolate-doom rev-parse HEAD
$wadHash = (Get-FileHash assets/freedoom-0.13.0/freedoom2.wad -Algorithm SHA256).Hash.ToLower()
@{ engine_commit=$engineCommit; freedoom='0.13.0'; wad_sha256=$wadHash; emscripten='6.0.12' } | ConvertTo-Json | Set-Content dist/build-info.json
Write-Host 'Ready: dist/index.html. Run python scripts/serve.py'
