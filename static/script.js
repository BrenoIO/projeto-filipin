document.addEventListener('DOMContentLoaded', () => {
  const btnContrast = document.getElementById('btn-contrast');
  const btnIncrease = document.getElementById('btn-font-increase');
  const btnDecrease = document.getElementById('btn-font-decrease');
  const form = document.getElementById('booking-form');
  const bookingsList = document.getElementById('bookings-list');

  let currentFontSize = 16;

  // Recurso de Acessibilidade 1: Alto Contraste
  btnContrast.addEventListener('click', () => {
    document.body.classList.toggle('high-contrast');
  });

  // Recurso de Acessibilidade 2: Redimensionamento de Fonte
  btnIncrease.addEventListener('click', () => {
    if (currentFontSize < 24) {
      currentFontSize += 2;
      document.documentElement.style.setProperty('--font-size', `${currentFontSize}px`);
    }
  });

  btnDecrease.addEventListener('click', () => {
    if (currentFontSize > 12) {
      currentFontSize -= 2;
      document.documentElement.style.setProperty('--font-size', `${currentFontSize}px`);
    }
  });

  // Função para buscar os alunos salvos no Banco de Dados via API do Flask
  async function carregarAlunos() {
    try {
      const response = await fetch('/api/alunos');
      const alunos = await response.json();

      bookingsList.innerHTML = '';
      
      if (alunos.length === 0) {
        bookingsList.innerHTML = '<li style="color: #666;">Nenhum aluno cadastrado ainda.</li>';
        return;
      }

      alunos.forEach((aluno, index) => {
        const li = document.createElement('li');
        li.style.marginBottom = '8px';
        // Exibindo os dados salvos no banco (Nome, Idade, Responsável, Faixa e Observação opcional)
        li.innerHTML = `<strong>${index + 1}. Atleta:</strong> ${aluno.nome} (Idade: ${aluno.idade}, Faixa: ${aluno.faixa}) — <em>Resp: ${aluno.responsavel}</em>`;
        if (aluno.observacao) {
          li.innerHTML += ` <br><small style="color: #555;">Obs: ${aluno.observacao}</small>`;
        }
        bookingsList.appendChild(li);
      });
    } catch (error) {
      console.error("Erro ao carregar alunos do banco:", error);
      bookingsList.innerHTML = '<li style="color: red;">Erro ao carregar dados do servidor.</li>';
    }
  }

  // Fluxo de Cadastro: Enviar os dados do formulário para o Flask salvar no PostgreSQL
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const dadosAluno = {
      nome: document.getElementById('student-name').value,
      idade: parseInt(document.getElementById('student-age').value),
      responsavel: document.getElementById('guardian-name').value,
      faixa: document.getElementById('belt').value,
      observacao: document.getElementById('observation').value || ""
    };

    try {
      const response = await fetch('/api/alunos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(dadosAluno)
      });

      if (response.ok) {
        alert("Aluno cadastrado com sucesso no banco de dados!");
        form.reset();
        carregarAlunos(); // Atualiza a lista automaticamente buscando direto do banco
      } else {
        const erroJson = await response.json();
        alert("Erro ao cadastrar: " + (erroJson.error || "Verifique os campos."));
      }
    } catch (error) {
      console.error("Erro na requisição:", error);
      alert("Erro de conexão com o servidor Flask.");
    }
  });

  // Carrega a lista de alunos assim que a página é aberta
  carregarAlunos();
});