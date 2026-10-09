cmake_minimum_required(VERSION 3.20)
project(DoomBrowser LANGUAGES C)
if(NOT EMSCRIPTEN)
  message(FATAL_ERROR "Use scripts/build.ps1 (Emscripten required)")
endif()
set(ENABLE_SDL2_NET OFF CACHE BOOL "No networking" FORCE)
set(ENABLE_SDL2_MIXER ON CACHE BOOL "SDL2 audio" FORCE)
set(CMAKE_DISABLE_FIND_PACKAGE_SampleRate ON)
set(CMAKE_DISABLE_FIND_PACKAGE_PNG ON)
set(CMAKE_DISABLE_FIND_PACKAGE_FluidSynth ON)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/dist")
add_subdirectory(vendor/chocolate-doom chocolate EXCLUDE_FROM_ALL)
# Override upstream's obsolete EXPORTED_FUNCTIONS setting.
set_target_properties(chocolate-doom PROPERTIES
  LINK_FLAGS ""
  SUFFIX ".js"
  OUTPUT_NAME "doom")
target_sources(chocolate-doom PRIVATE port/browser.c)
target_link_options(chocolate-doom PRIVATE
  -sUSE_SDL=2 -sUSE_SDL_MIXER=2
  -sASYNCIFY=1 -sASYNCIFY_STACK_SIZE=131072
  -sALLOW_MEMORY_GROWTH=1 -sINITIAL_MEMORY=67108864
  -sSTACK_SIZE=2097152 -sMODULARIZE=1 -sEXPORT_NAME=createDoom
  -sINVOKE_RUN=0 -sEXIT_RUNTIME=0 -sENVIRONMENT=web
  -sEXPORTED_FUNCTIONS=_main,_M_SaveDefaults
  -sEXPORTED_RUNTIME_METHODS=callMain,FS
  -lidbfs.js
  "--pre-js=${CMAKE_SOURCE_DIR}/web/persistence.js"
  --preload-file "${CMAKE_SOURCE_DIR}/assets/freedoom-0.13.0/freedoom2.wad@/freedoom2.wad")
