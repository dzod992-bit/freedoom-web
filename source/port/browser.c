/* Browser glue for Chocolate Doom. SPDX-License-Identifier: GPL-2.0-or-later */
#include <emscripten.h>

EM_JS(void, Web_SaveFinished, (void), {
    if (Module['flushSaves']) Module['flushSaves']();
});

EM_JS(void, Web_GraphicsReady, (void), {
    // SDL installs its listener after the initial user click may have locked
    // the pointer. Synchronize it with the browser's actual lock state.
    document.dispatchEvent(new Event('pointerlockchange'));
    if (Module['onGameReady']) Module['onGameReady']();
});

/* Read-only integration diagnostic: verifies real camera rotation. */
EMSCRIPTEN_KEEPALIVE unsigned int Web_GetViewAngle(void)
{
    extern unsigned int viewangle;
    return viewangle;
}
