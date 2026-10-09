$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
New-Item -ItemType Directory -Force tools,vendor,downloads | Out-Null
if (!(Test-Path tools/emsdk/emsdk.py)) {
    git clone --depth 1 https://github.com/emscripten-core/emsdk.git tools/emsdk
    if ($LASTEXITCODE) { throw 'emsdk download failed' }
}
python tools/emsdk/emsdk.py install 6.0.12
if ($LASTEXITCODE) { throw 'emsdk install failed' }
python tools/emsdk/emsdk.py activate 6.0.12
if ($LASTEXITCODE) { throw 'emsdk activation failed' }
python -m pip install --target tools/python-packages 'cmake==4.4.4' 'ninja==1.13.2' 'playwright==1.63.0'
if ($LASTEXITCODE) { throw 'Build tools install failed' }
if (!(Test-Path vendor/chocolate-doom/CMakeLists.txt)) {
    git clone --depth 1 https://github.com/chocolate-doom/chocolate-doom.git vendor/chocolate-doom
    if ($LASTEXITCODE) { throw 'Chocolate Doom download failed' }
    git -C vendor/chocolate-doom fetch --depth 1 origin 895f581c5d91497bdda0516612da803fe5843e28
    if ($LASTEXITCODE) { throw 'Pinned engine revision unavailable' }
    git -C vendor/chocolate-doom checkout --detach 895f581c5d91497bdda0516612da803fe5843e28
    if ($LASTEXITCODE) { throw 'Engine checkout failed' }
}
if (!(Test-Path assets/freedoom-0.13.0/freedoom2.wad)) {
    Invoke-WebRequest https://github.com/freedoom/freedoom/releases/download/v0.13.0/freedoom-0.13.0.zip -OutFile downloads/freedoom.zip
    Expand-Archive downloads/freedoom.zip -DestinationPath assets -Force
}
& ./tools/emsdk/upstream/emscripten/emcc.exe --version
if ($LASTEXITCODE) { throw 'emcc check failed' }
Write-Host 'Setup complete. Run ./scripts/build.ps1'
