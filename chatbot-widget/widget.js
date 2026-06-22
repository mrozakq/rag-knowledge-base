(function () {
  'use strict';

  /* ── Config from data- attributes on the <script> tag ── */
  var script = document.currentScript ||
    (function () {
      var scripts = document.getElementsByTagName('script');
      return scripts[scripts.length - 1];
    })();

  var cfg = {
    apiUrl: (script.getAttribute('data-api-url') || '').replace(/\/$/, ''),
    apiKey: script.getAttribute('data-api-key') || '',
    title:  script.getAttribute('data-title')   || 'Asystent',
    color:  script.getAttribute('data-primary-color') || '#185FA5',
  };

  /* ── Inject CSS ── */
  var cssUrl = script.src.replace(/widget\.js([?#].*)?$/, 'widget.css');
  var link = document.createElement('link');
  link.rel = 'stylesheet'; link.href = cssUrl;
  document.head.appendChild(link);

  /* ── Apply primary colour overrides ── */
  var style = document.createElement('style');
  style.textContent = ':root { --rag-primary: ' + cfg.color + '; }';
  document.head.appendChild(style);

  /* ── Build DOM ── */
  var btn = document.createElement('button');
  btn.id = 'rag-widget-btn';
  btn.setAttribute('aria-label', 'Otwórz czat');
  btn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>';

  var panel = document.createElement('div');
  panel.id = 'rag-widget-panel';
  panel.style.display = 'none';
  panel.innerHTML =
    '<div id="rag-widget-header">' +
      '<span>' + _esc(cfg.title) + '</span>' +
      '<button id="rag-widget-close" aria-label="Zamknij">&times;</button>' +
    '</div>' +
    '<div id="rag-widget-messages"></div>' +
    '<form id="rag-widget-form">' +
      '<input id="rag-widget-input" type="text" placeholder="Napisz pytanie…" autocomplete="off" />' +
      '<button id="rag-widget-send" type="submit">&#10148;</button>' +
    '</form>';

  document.body.appendChild(btn);
  document.body.appendChild(panel);

  var messages = panel.querySelector('#rag-widget-messages');
  var form     = panel.querySelector('#rag-widget-form');
  var input    = panel.querySelector('#rag-widget-input');
  var sendBtn  = panel.querySelector('#rag-widget-send');

  /* ── Toggle panel ── */
  btn.addEventListener('click', function () { setOpen(panel.style.display === 'none'); });
  panel.querySelector('#rag-widget-close').addEventListener('click', function () { setOpen(false); });

  function setOpen(open) {
    panel.style.display = open ? 'flex' : 'none';
    if (open) { input.focus(); }
  }

  /* ── Form submit ── */
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var question = input.value.trim();
    if (!question) return;
    input.value = '';
    sendBtn.disabled = true;

    _appendMsg(question, 'user');
    var typing = _appendTyping();

    _query(question)
      .then(function (data) {
        typing.remove();
        _appendBot(data.answer, data.sources);
      })
      .catch(function (err) {
        typing.remove();
        _appendMsg('Błąd połączenia z API: ' + err.message, 'error');
      })
      .finally(function () {
        sendBtn.disabled = false;
        input.focus();
      });
  });

  /* ── Enter to send, Shift+Enter for newline ── */
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.dispatchEvent(new Event('submit'));
    }
  });

  /* ── API call ── */
  function _query(question) {
    if (!cfg.apiUrl) return Promise.reject(new Error('data-api-url nie jest skonfigurowane'));
    return fetch(cfg.apiUrl + '/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + cfg.apiKey,
      },
      body: JSON.stringify({ question: question, language: 'pl' }),
    }).then(function (resp) {
      if (!resp.ok) return Promise.reject(new Error('HTTP ' + resp.status));
      return resp.json();
    });
  }

  /* ── DOM helpers ── */
  function _appendMsg(text, type) {
    var div = document.createElement('div');
    div.className = 'rag-msg rag-msg-' + type;
    div.textContent = text;
    messages.appendChild(div);
    _scrollBottom();
    return div;
  }

  function _appendBot(answer, sources) {
    var div = document.createElement('div');
    div.className = 'rag-msg rag-msg-bot';

    var answerEl = document.createElement('div');
    answerEl.textContent = answer;
    div.appendChild(answerEl);

    if (sources && sources.length > 0) {
      var srcDiv = document.createElement('div');
      srcDiv.className = 'rag-sources';
      var label = document.createElement('strong');
      label.textContent = 'Źródła:';
      srcDiv.appendChild(label);
      sources.forEach(function (s) {
        var item = document.createElement('div');
        item.className = 'rag-source-item';
        var page = s.page ? ' (s. ' + s.page + ')' : '';
        item.textContent = '📄 ' + s.source + page;
        srcDiv.appendChild(item);
      });
      div.appendChild(srcDiv);
    }

    messages.appendChild(div);
    _scrollBottom();
    return div;
  }

  function _appendTyping() {
    var div = document.createElement('div');
    div.className = 'rag-typing';
    div.innerHTML = '<span></span><span></span><span></span>';
    messages.appendChild(div);
    _scrollBottom();
    return div;
  }

  function _scrollBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  function _esc(str) {
    return str.replace(/[&<>"']/g, function (c) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }

})();
