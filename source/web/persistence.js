// Executed inside the Emscripten module. Restore storage BEFORE main reads config.
Module['preRun'] = Module['preRun'] || [];
Module['preRun'].push(function () {
  var status = function (message, failed) {
    if (Module['storageStatus']) Module['storageStatus'](message, !!failed);
  };
  var busy = false;
  var dirty = false;
  var waiters = [];
  Module['storagePending'] = false;
  function pump() {
    if (busy || !dirty) return;
    busy = true;
    dirty = false;
    status('Сохраняем…');
    FS.syncfs(false, function (error) {
      busy = false;
      if (error) {
        Module['storagePending'] = false;
        status('Не удалось записать сохранение. Проверьте доступ к хранилищу браузера.', true);
        var failed = waiters.splice(0);
        failed.forEach(function (item) { item.reject(error); });
        return;
      }
      if (dirty) { pump(); return; }
      Module['storagePending'] = false;
      status('Сохранения записаны в браузер');
      var finished = waiters.splice(0);
      finished.forEach(function (item) { item.resolve(); });
    });
  }
  Module['flushSaves'] = function () {
    dirty = true;
    Module['storagePending'] = true;
    var promise = new Promise(function (resolve, reject) { waiters.push({resolve: resolve, reject: reject}); });
    // The C save hook has no Promise consumer; report failure through the UI.
    promise.catch(function () {});
    pump();
    return promise;
  };
  FS.mkdir('/persist');
  FS.mount(IDBFS, {}, '/persist');
  addRunDependency('restore-saves');
  FS.syncfs(true, function (error) {
    if (error) {
      status('Хранилище недоступно: сохранения действуют только до закрытия страницы.', true);
    } else {
      status('Сохранения готовы');
    }
    if (!FS.analyzePath('/persist/default.cfg').exists) {
      FS.writeFile('/persist/default.cfg', [
        'key_up 17', 'key_down 31', 'key_strafeleft 30', 'key_straferight 32',
        'key_use 57', 'key_fire 29', 'key_speed 54', 'mouse_sensitivity 5',
        'snd_musicdevice 3', 'snd_sfxdevice 3', 'sfx_volume 8', 'music_volume 6',
        'screenblocks 10', ''
      ].join('\n'));
    }
    if (!FS.analyzePath('/persist/chocolate-doom.cfg').exists) {
      FS.writeFile('/persist/chocolate-doom.cfg', [
        'fullscreen 0', 'window_width 960', 'window_height 720',
        'aspect_ratio_correct 1', 'startup_delay 0', 'show_endoom 0',
        'vanilla_savegame_limit 0', 'vanilla_demo_limit 0',
        'novert 1', 'use_libsamplerate 0', 'grabmouse 1', ''
      ].join('\n'));
    }
    removeRunDependency('restore-saves');
  });
});
