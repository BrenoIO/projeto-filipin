(function () {
  'use strict';
  var raiz = document.documentElement;

  function salvar(chave, valor) {
    try { localStorage.setItem(chave, valor); } catch (e) { /* armazenamento indisponível */ }
  }

  // ---- Acessibilidade: alto contraste ----
  var btnContraste = document.getElementById('btn-contraste');
  function atualizarContraste() {
    btnContraste.setAttribute('aria-pressed', raiz.classList.contains('alto-contraste') ? 'true' : 'false');
  }
  atualizarContraste();
  btnContraste.addEventListener('click', function () {
    raiz.classList.toggle('alto-contraste');
    salvar('alto-contraste', raiz.classList.contains('alto-contraste') ? '1' : '0');
    atualizarContraste();
  });

  // ---- Acessibilidade: tamanho da fonte ----
  function mudarFonte(delta) {
    var atual = parseFloat(getComputedStyle(raiz).fontSize) || 16;
    var novo = Math.min(24, Math.max(14, atual + delta));
    raiz.style.fontSize = novo + 'px';
    salvar('tamanho-fonte', String(novo));
  }
  document.getElementById('btn-fonte-mais').addEventListener('click', function () { mudarFonte(2); });
  document.getElementById('btn-fonte-menos').addEventListener('click', function () { mudarFonte(-2); });

  // ---- Confirmação em ações sensíveis ----
  document.querySelectorAll('[data-confirmar]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      if (!window.confirm(btn.getAttribute('data-confirmar'))) e.preventDefault();
    });
  });

  // ---- Chamada: contador e marcar/desmarcar todos ----
  var formChamada = document.getElementById('form-chamada');
  if (formChamada) {
    var caixas = formChamada.querySelectorAll('input[name="presentes"]');
    var contador = document.getElementById('contador');
    var alterado = false;

    function atualizarContador() {
      var n = 0;
      caixas.forEach(function (c) { if (c.checked) n++; });
      contador.textContent = n + ' de ' + caixas.length + ' presentes';
    }
    formChamada.addEventListener('change', function () { alterado = true; atualizarContador(); });
    formChamada.querySelectorAll('[data-marcar]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var marcar = btn.getAttribute('data-marcar') === 'todos';
        caixas.forEach(function (c) { c.checked = marcar; });
        alterado = true;
        atualizarContador();
      });
    });
    // Avisa se o professor tentar sair da página sem salvar a chamada.
    formChamada.addEventListener('submit', function () { alterado = false; });
    window.addEventListener('beforeunload', function (e) {
      if (alterado) { e.preventDefault(); e.returnValue = ''; }
    });
  }

  // ---- Lista de alunos: busca pelo nome ----
  var busca = document.getElementById('busca');
  var lista = document.getElementById('lista-alunos');
  if (busca && lista) {
    var semResultados = document.getElementById('sem-resultados');
    var normalizar = function (t) { return t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); };
    busca.addEventListener('input', function () {
      var termo = normalizar(busca.value.trim());
      var visiveis = 0;
      lista.querySelectorAll('li[data-nome]').forEach(function (li) {
        var mostra = normalizar(li.getAttribute('data-nome')).indexOf(termo) !== -1;
        li.hidden = !mostra;
        if (mostra) visiveis++;
      });
      semResultados.hidden = visiveis !== 0;
    });
  }
})();
