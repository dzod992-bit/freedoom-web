"""Small, idempotent browser changes; fail loudly if upstream changes."""
from pathlib import Path

root = Path(__file__).resolve().parent.parent / "vendor/chocolate-doom"

def replace(relative, before, after):
    path = root / relative
    text = path.read_text(encoding="utf-8")
    if after in text:
        return
    if text.count(before) != 1:
        raise RuntimeError(f"Patch no longer applies: {relative}")
    path.write_text(text.replace(before, after), encoding="utf-8", newline="\n")

replace("src/i_timer.c", '#include "SDL.h"',
        '#include "SDL.h"\n#ifdef __EMSCRIPTEN__\n#include <emscripten.h>\n#endif')
replace("src/i_timer.c", '    SDL_Delay(ms);',
        '    #ifdef __EMSCRIPTEN__\n    emscripten_sleep(ms);\n    #else\n    SDL_Delay(ms);\n    #endif')
replace("src/doom/g_game.c", '    M_rename(temp_savegame_file, savegame_file);',
        '    M_rename(temp_savegame_file, savegame_file);\n'
        '    #ifdef __EMSCRIPTEN__\n'
        '    {\n        extern void Web_SaveFinished(void);\n        Web_SaveFinished();\n    }\n'
        '    #endif')
# The page owns browser Pointer Lock; native grab/menu transitions must not
# silently undo the lock granted to a user click.
replace("src/i_video.c", '        SDL_SetRelativeMouseMode(!show);',
        '        #ifdef __EMSCRIPTEN__\n'
        '        SDL_ShowCursor(show ? SDL_ENABLE : SDL_DISABLE);\n'
        '        #else\n'
        '        SDL_SetRelativeMouseMode(!show);\n'
        '        #endif')
replace("src/i_video.c", '    initialized = true;',
        '    initialized = true;\n'
        '    #ifdef __EMSCRIPTEN__\n'
        '    {\n        extern void Web_GraphicsReady(void);\n        Web_GraphicsReady();\n    }\n'
        '    #endif')
# Emscripten 6 defines __EMSCRIPTEN__; upstream used the old EMSCRIPTEN alias.
opl = root / "opl/opl.c"
text = opl.read_text(encoding="utf-8")
if '#ifdef EMSCRIPTEN' in text:
    opl.write_text(text.replace('#ifdef EMSCRIPTEN', '#ifdef __EMSCRIPTEN__'), encoding="utf-8", newline="\n")
print("Browser patches applied.")
