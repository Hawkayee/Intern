/* ============================================================
   Zephor RVM Kiosk — shared client helpers
   Kept tiny and dependency-free (Radxa Zero 3W is resource-limited).
   Screen-flow wiring is added in later steps; Step 1 ships only
   the helpers used by the idle/attract screen.
   ============================================================ */
(function (global) {
  'use strict';

  var ZephorKiosk = {

    /* Cross-fade through a list of strings on a target element. */
    rotateTaglines: function (elementId, messages, intervalMs) {
      var el = document.getElementById(elementId);
      if (!el || !messages || messages.length < 2) return;
      var i = 0;
      intervalMs = intervalMs || 4000;
      el.style.transition = 'opacity .5s ease';
      setInterval(function () {
        el.style.opacity = '0';
        setTimeout(function () {
          i = (i + 1) % messages.length;
          el.textContent = messages[i];
          el.style.opacity = '1';
        }, 500);
      }, intervalMs);
    },

    /* Thin POST-JSON helper used by later screens for the /api/* routes. */
    postJSON: function (url, payload) {
      return fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload || {}),
      }).then(function (r) { return r.json(); });
    },

    /* sessionStorage helpers — carry flow state between page screens. */
    setState: function (key, value) {
      try { sessionStorage.setItem('zephor.' + key, JSON.stringify(value)); } catch (e) {}
    },
    getState: function (key) {
      try { return JSON.parse(sessionStorage.getItem('zephor.' + key)); }
      catch (e) { return null; }
    },
    clearState: function () {
      try { sessionStorage.clear(); } catch (e) {}
    },

    /* Return any interactive screen to idle after a period of no touch.
       Resets the timer on every interaction. Default 45s. */
    startIdleTimeout: function (seconds) {
      var ms = (seconds || 45) * 1000;
      var timer;
      var self = this;
      function reset() {
        clearTimeout(timer);
        timer = setTimeout(function () {
          self.clearState();
          window.location.href = '/';
        }, ms);
      }
      ['click', 'touchstart', 'keydown'].forEach(function (ev) {
        document.addEventListener(ev, reset, { passive: true });
      });
      reset();
    },

    /* Build an on-screen keyboard and manage a typed value.
       opts: { keyboardId, displayId, maxLength, onEnter(value) } */
    buildKeyboard: function (opts) {
      var kb = document.getElementById(opts.keyboardId);
      var display = document.getElementById(opts.displayId);
      var maxLength = opts.maxLength || 12;
      var value = '';

      var rows = [
        '1234567890'.split(''),
        'QWERTYUIOP'.split(''),
        'ASDFGHJKL'.split(''),
        'ZXCVBNM'.split(''),
      ];

      function render() {
        if (value) {
          display.textContent = value;
          display.classList.remove('is-error');
        } else {
          display.innerHTML = '<span class="placeholder">Tap to enter</span>';
        }
      }

      function press(ch) {
        if (value.length < maxLength) { value += ch; render(); }
      }
      function backspace() { value = value.slice(0, -1); render(); }
      function clearAll() { value = ''; render(); }

      function makeKey(label, cls, handler) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'key' + (cls ? ' ' + cls : '');
        b.textContent = label;
        b.addEventListener('click', handler);
        return b;
      }

      rows.forEach(function (chars) {
        var row = document.createElement('div');
        row.className = 'krow';
        chars.forEach(function (ch) {
          row.appendChild(makeKey(ch, '', function () { press(ch); }));
        });
        kb.appendChild(row);
      });

      // Control row: Clear, Backspace, Enter
      var ctrl = document.createElement('div');
      ctrl.className = 'krow';
      ctrl.appendChild(makeKey('Clear', 'key-wide key-muted', clearAll));
      ctrl.appendChild(makeKey('⌫', 'key-wide key-muted', backspace));
      ctrl.appendChild(makeKey('Enter', 'key-wide key-accent', function () {
        if (value && opts.onEnter) opts.onEnter(value);
      }));
      kb.appendChild(ctrl);

      render();
      return {
        getValue: function () { return value; },
        setError: function () { display.classList.add('is-error'); },
        clear: clearAll,
      };
    },
  };

  global.ZephorKiosk = ZephorKiosk;
})(window);
