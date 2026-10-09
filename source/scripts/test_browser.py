"""Integration test against a running server; uses installed Microsoft Edge."""
import hashlib
import json
from pathlib import Path
import sys
import time

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "tools/python-packages"))
from playwright.sync_api import sync_playwright

game_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/"
out = root / "test-results" / ("published" if game_url.startswith("https:") else "local")
out.mkdir(exist_ok=True)
errors = []
console = []

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True, args=[
        "--enable-unsafe-swiftshader", "--use-angle=swiftshader"
    ])
    context = browser.new_context(viewport={"width": 1280, "height": 1100})
    page = context.new_page()
    def on_error(error):
        errors.append(str(error))
        print('PAGE ERROR:', error, flush=True)
    def on_console(message):
        line = f"{message.type}: {message.text}"
        console.append(line)
        (out / "console.log").write_text("\n".join(console), encoding="utf-8")
        print(line, flush=True)
    page.on("pageerror", on_error)
    page.on("console", on_console)
    page.goto(game_url, wait_until="networkidle", timeout=90000)
    page.wait_for_function("window.doom && !document.querySelector('#play').disabled", timeout=60000)
    assert page.locator('#game-address').input_value() == game_url, 'Fallback URL loses the site path'
    page.screenshot(path=str(out / "ready.png"))
    assert page.evaluate("doom.FS.stat('/freedoom2.wad').size") > 20_000_000
    page.get_by_role("button", name="Играть", exact=True).click()
    page.wait_for_function("document.querySelector('#log').textContent.includes('Emulating the behavior')", timeout=60000)
    page.wait_for_timeout(3000)
    assert not page.locator("#status").evaluate("e => e.classList.contains('error')"), page.locator("#log").inner_text()
    page.evaluate("""() => {
      const sdl = doom.SDL2;
      if (!sdl || !sdl.audioContext || !sdl.audio.scriptProcessorNode) throw Error('SDL audio unavailable');
      const context = sdl.audioContext;
      window.testAnalyser = context.createAnalyser();
      const mute = context.createGain();
      mute.gain.value = 0;
      sdl.audio.scriptProcessorNode.connect(testAnalyser);
      testAnalyser.connect(mute);
      mute.connect(context.destination);
    }""")
    page.wait_for_timeout(500)
    audio = page.evaluate("""() => {
      const buffer = new Float32Array(testAnalyser.fftSize);
      testAnalyser.getFloatTimeDomainData(buffer);
      return {state:doom.SDL2.audioContext.state, peak:Math.max(...buffer.map(Math.abs))};
    }""")
    assert audio['state'] == 'running' and audio['peak'] > 0.0001, f'No audible PCM: {audio}'
    capture = page.evaluate("({fullscreen:!!document.fullscreenElement, pointerLock:document.pointerLockElement === document.querySelector('canvas')})")
    assert capture['fullscreen'] and capture['pointerLock'], capture
    # Prove that real browser mouse motion reaches the engine as relative
    # deltas even when coordinates go far beyond the viewport's right edge.
    page.mouse.move(650, 450)
    page.wait_for_timeout(100)
    angles = [page.evaluate("doom._Web_GetViewAngle()")]
    for x in (2200, 4800, 7600, 10300):
        page.mouse.move(x, 450)
        page.wait_for_timeout(120)
        angles.append(page.evaluate("doom._Web_GetViewAngle()"))
        assert page.evaluate("document.pointerLockElement === document.querySelector('canvas')"), 'Pointer escaped during rotation'
    assert all(a != b for a, b in zip(angles, angles[1:])), f'Camera stopped at screen edge: {angles}'
    # Losing lock must expose a working recapture button even in fullscreen.
    page.evaluate("document.exitPointerLock()")
    page.wait_for_function("!document.pointerLockElement && !document.querySelector('#mouse-prompt').hidden")
    assert page.evaluate("!!document.fullscreenElement"), 'Expected fullscreen recovery case'
    page.screenshot(path=str(out / 'mouse-unlocked.png'))
    page.get_by_role('button', name='Вернуться в игру', exact=True).click()
    page.wait_for_function("document.pointerLockElement === document.querySelector('canvas') && document.querySelector('#mouse-prompt').hidden")
    page.keyboard.press('F2')
    page.wait_for_timeout(300)
    assert page.evaluate("document.pointerLockElement === document.querySelector('canvas')"), 'Game menu silently released pointer lock'
    page.keyboard.press('F2')
    page.wait_for_timeout(300)
    # Release fullscreen/lock before menu tests; keyboard still targets the canvas.
    page.evaluate("document.exitPointerLock(); if(document.fullscreenElement) document.exitFullscreen();")
    page.wait_for_timeout(500)
    page.locator("canvas").focus()
    page.screenshot(path=str(out / "game.png"))
    before = page.locator("canvas").screenshot()
    page.keyboard.down("w")
    page.wait_for_timeout(600)
    page.keyboard.up("w")
    page.keyboard.press("Control")
    page.wait_for_timeout(500)
    after = page.locator("canvas").screenshot()
    assert hashlib.sha256(before).digest() != hashlib.sha256(after).digest(), "No rendered movement"
    # Save via the real game menu, never manufacture a save file through FS.
    page.keyboard.press("F2")
    page.wait_for_timeout(400)
    page.screenshot(path=str(out / "save-menu.png"))
    page.keyboard.press("Enter")
    page.keyboard.type("WASM TEST", delay=80)
    page.keyboard.press("Enter")
    page.wait_for_function("doom.FS.readdir('/persist').some(x=>x.endsWith('.dsg'))", timeout=15000)
    page.wait_for_function("!doom.storagePending", timeout=15000)
    saved = page.evaluate("""() => {
      const path = '/persist/' + doom.FS.readdir('/persist').find(x=>x.endsWith('.dsg'));
      return {path, bytes:Array.from(doom.FS.readFile(path))};
    }""")
    assert len(saved["bytes"]) > 1000, "Save is empty"
    page.screenshot(path=str(out / "saved.png"))
    page.reload(wait_until="networkidle")
    page.wait_for_function("window.doom && !document.querySelector('#play').disabled", timeout=60000)
    restored = page.evaluate("path => Array.from(doom.FS.readFile(path))", saved["path"])
    assert restored == saved["bytes"], "IndexedDB save changed after reload"
    page.get_by_role("button", name="Играть", exact=True).click()
    page.wait_for_timeout(2500)
    page.evaluate("document.exitPointerLock(); if(document.fullscreenElement) document.exitFullscreen();")
    page.wait_for_timeout(400)
    page.locator("canvas").focus()
    page.keyboard.press("F3")
    page.wait_for_timeout(400)
    page.screenshot(path=str(out / "load-menu.png"))
    page.keyboard.press("Enter")
    page.wait_for_timeout(1200)
    page.screenshot(path=str(out / "loaded.png"))
    assert not page.locator("#status").evaluate("e => e.classList.contains('error')"), "Engine failed loading its own save"
    # A timer round trip proves the infinite game loop yields to the browser.
    assert page.evaluate("() => new Promise(r => setTimeout(() => r('responsive'), 100))") == "responsive"
    result = {"url":game_url, "browser":browser.version, "capture":capture, "mouse_angles_beyond_viewport":angles,
              "fullscreen_recapture":True, "menu_keeps_pointer_lock":True, "audio":audio, "save_path":saved["path"],
              "save_size":len(saved["bytes"]), "persistence_after_reload":True,
              "movement_rendered":True, "responsive":True, "page_errors":errors}
    (out / "browser.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "console.log").write_text("\n".join(console), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    assert not errors, errors
    browser.close()
