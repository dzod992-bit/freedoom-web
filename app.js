(() => {
  'use strict';
  const canvas = document.getElementById('canvas');
  const stage = document.getElementById('stage');
  const play = document.getElementById('play');
  const status = document.getElementById('status');
  const storage = document.getElementById('storage');
  const log = document.getElementById('log');
  const mousePrompt = document.getElementById('mouse-prompt');
  const mouseMessage = document.getElementById('mouse-message');
  const captureButton = document.getElementById('capture');
  const browserHelp = document.getElementById('browser-help');
  const gameAddress = document.getElementById('game-address');
  const copyAddress = document.getElementById('copy-address');
  const mouseHint = document.getElementById('mouse-hint');
  gameAddress.value = new URL('.', location.href).href;
  let doom;
  let running = false;
  let failed = false;
  let gameReady = false;
  let lockPending = false;
  let captureUnavailable = false;
  const lines = [];
  function write(message) {
    lines.push(String(message));
    if (lines.length > 160) lines.shift();
    log.textContent = lines.join('\n');
    console.log('[Doom]', message);
  }
  function fatal(error) {
    failed = true;
    status.textContent = 'Ошибка запуска. Подробности — в журнале ниже.';
    status.classList.add('error');
    play.disabled = true;
    play.textContent = 'Ошибка';
    write(error);
    stage.classList.add('unlocked');
  }
  function updateCapture() {
    const locked = document.pointerLockElement === canvas;
    stage.classList.toggle('unlocked', !locked);
    stage.classList.toggle('locked', locked);
    mousePrompt.hidden = !running || !gameReady || locked || failed;
    if (locked) {
      mouseMessage.textContent = 'Нажмите, чтобы захватить мышь и продолжить игру.';
      canvas.focus({preventScroll: true});
    }
  }
  function captureError(error) {
    lockPending = false;
    if (document.pointerLockElement === canvas) return;
    if (error && /bug|root document|not supported|not available|not valid for pointer lock/i.test(error.message)) {
      captureUnavailable = true;
      captureButton.hidden = true;
      mouseHint.hidden = true;
      browserHelp.hidden = false;
      mouseMessage.textContent = 'В этом окне браузер не поддерживает захват мыши. Откройте игру в отдельном окне Edge или Chrome: скопируйте адрес ниже и вставьте его в адресную строку браузера.';
    } else if (!captureUnavailable) {
      mouseMessage.textContent = 'Браузер не захватил мышь. Нажмите «Вернуться в игру» ещё раз.';
    }
    updateCapture();
    if (error) write('Захват мыши: ' + error.message);
  }
  // Lock first: requesting fullscreen consumes the click's user activation.
  // Never re-request an existing lock (including on every shot).
  function capture() {
    if (captureUnavailable) return;
    canvas.focus({preventScroll: true});
    if (document.pointerLockElement !== canvas && !lockPending) {
      try {
        lockPending = true;
        const lock = canvas.requestPointerLock();
        if (lock && lock.catch) lock.catch(captureError);
      } catch (error) { captureError(error); }
    }
    if (!document.fullscreenElement && stage.requestFullscreen) {
      stage.requestFullscreen().catch(() => { /* Windowed play remains available. */ });
    }
    const audio = doom && doom.SDL2 && doom.SDL2.audioContext;
    if (audio && audio.state === 'suspended') audio.resume().catch(error => write(error.message));
  }
  play.addEventListener('click', () => {
    if (!doom || failed) return;
    capture();
    if (running) return;
    running = true;
    doom['gameStarted'] = true;
    stage.classList.add('running');
    play.textContent = 'Продолжить';
    status.textContent = 'Запуск…';
    try {
      doom.callMain([
        '-iwad', '/freedoom2.wad', '-savedir', '/persist',
        '-config', '/persist/default.cfg', '-extraconfig', '/persist/chocolate-doom.cfg',
        '-window', '-novert', '-nogui', '-warp', '1', '-skill', '3'
      ]);
      status.textContent = 'Игра запущена';
    } catch (error) { fatal(error); }
  });
  captureButton.addEventListener('click', capture);
  copyAddress.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(gameAddress.value);
      copyAddress.textContent = 'Адрес скопирован';
    } catch (error) {
      gameAddress.focus();
      gameAddress.select();
      copyAddress.textContent = 'Нажмите Ctrl+C, чтобы скопировать';
    }
  });
  gameAddress.addEventListener('click', () => gameAddress.select());
  mousePrompt.addEventListener('click', event => {
    if (event.target !== captureButton && !browserHelp.contains(event.target)) capture();
  });
  canvas.addEventListener('click', () => {
    if (running && !failed && document.pointerLockElement !== canvas) capture();
  });
  canvas.addEventListener('contextmenu', event => event.preventDefault());
  document.addEventListener('pointerlockchange', () => {
    lockPending = false;
    updateCapture();
  });
  document.addEventListener('pointerlockerror', () => captureError());
  document.addEventListener('fullscreenchange', updateCapture);
  // Keep SDL's keyboard input confined to the game canvas.
  canvas.addEventListener('keydown', event => {
    if (['Tab',' ','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12'].includes(event.key)) event.preventDefault();
  });
  function saveSettings() {
    if (!running || failed || !doom) return;
    doom._M_SaveDefaults();
    doom.flushSaves();
  }
  document.addEventListener('visibilitychange', () => { if (document.hidden) saveSettings(); });
  window.addEventListener('pagehide', saveSettings);
  window.addEventListener('beforeunload', event => {
    if (doom && doom.storagePending) { event.preventDefault(); event.returnValue = ''; }
  });
  setInterval(saveSettings, 5000);
  if (typeof createDoom !== 'function') { fatal('Не загружен doom.js. Запустите страницу через локальный HTTP-сервер.'); return; }
  createDoom({
    canvas,
    print: write,
    printErr: write,
    onAbort: fatal,
    onGameReady: () => { gameReady = true; updateCapture(); },
    onExit: code => { running = false; status.textContent = `Игра завершена (${code}). Обновите страницу для нового запуска.`; stage.classList.add('unlocked'); play.disabled = true; },
    storageStatus: (message, error) => { storage.textContent = message; storage.classList.toggle('error', error); },
    monitorRunDependencies: remaining => { if (remaining) status.textContent = 'Загружаем уровни и сохранения…'; }
  }).then(module => {
    doom = module;
    // Also useful when diagnosing browser support from its developer console.
    window.doom = module;
    if (!failed) { play.disabled = false; play.textContent = 'Играть'; status.textContent = 'Всё готово'; }
  }).catch(fatal);
})();
