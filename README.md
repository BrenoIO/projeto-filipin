# Projeto Filipin: Controle de Frequência de Jiu-Jitsu Kids

Sistema web *mobile-first* para a instituição comunitária de Jiu-Jitsu **Projeto Filipin**. Ele substitui o controle em papel: o professor faz a chamada pelo celular na beira do tatame, acompanha a frequência de cada aluno e registra as graduações.

🌐 **Acesse:** https://projeto-filipin.onrender.com/

> ⏳ Hospedado no plano gratuito do Render: se o site ficou um tempo sem acessos, o primeiro carregamento pode levar cerca de 1 minuto. Depois disso, fica rápido normalmente.
>
> 🔒 O acesso é restrito aos professores da academia (os dados dos alunos são de menores de idade).

## 🛠️ Stack
* **Backend:** Python 3.12 + Flask (páginas renderizadas no servidor com Jinja) + SQLAlchemy 2.
* **Banco de dados:** PostgreSQL no Supabase (conexão via *Session Pooler*).
* **Autenticação:** sessão assinada (cookie `HttpOnly`/`SameSite`), senhas com hash (scrypt, via Werkzeug), proteção CSRF (Flask-WTF).
* **Testes/CI:** pytest com SQLite em memória + GitHub Actions.
* **Deploy:** Render (plano gratuito), via `render.yaml`.

## 📋 Requisitos atendidos
* **RF01:** Cadastro de professores (linha de comando) e de alunos (nome, nascimento, responsável obrigatório, telefone, observações de saúde, faixa e graus).
* **RF02:** Chamada digital por data, com seletores do tipo *toggle*, "marcar todos" e contador de presentes.
* **RF03:** Histórico de frequência: % nos últimos 30 dias, resumo mensal, últimos treinos.
* **RF04:** Apoio à graduação: presenças desde a última graduação; a decisão e o registro da nova faixa/grau ficam com o professor.
* **RNF01/RNF02:** Rotas protegidas por login, senhas com hash, CSRF, saída HTML escapada (sem XSS), RLS ativo no Supabase.
* **RAC01:** Áreas de toque ≥ 44px, alto contraste, ajuste de fonte, foco visível e informação nunca só por cor (faixa = cor + nome; presença = cor + ícone + texto).

## 📱 Telas
1. **Login** (`/`)
2. **Chamada** (`/chamada`): uso diário no tatame.
3. **Alunos** (`/alunos`): cadastro e frequência de todos.
4. **Ficha do aluno** (`/alunos/<id>`): histórico, graduação, edição e desativação.

Faixas: escala infantil da IBJJF (Branca → Cinza → Amarela → Laranja → Verde, com as variações "e Branca"/"e Preta"), com 0 a 4 graus.

## ▶️ Rodando localmente (Windows / PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

copy .env.example .env      # depois edite o .env com a URL do Supabase e uma SECRET_KEY

flask --app wsgi init-db          # cria as tabelas (pode rodar quantas vezes quiser)
flask --app wsgi criar-professor  # cria um login de professor
flask --app wsgi run --debug      # abre em http://127.0.0.1:5000
```

Testes: `pytest`

## ☁️ Deploy gratuito (Render)
1. Crie uma conta em https://render.com e conecte seu GitHub.
2. **New → Blueprint** e escolha este repositório (o `render.yaml` já configura tudo).
3. Quando pedir, cole em `DATABASE_URL` a mesma URL do seu `.env`.

> O plano gratuito "dorme" após ~15 min sem acesso; a primeira visita depois disso leva ~1 minuto para carregar.

## ♿ ODS
* **ODS 10 (Redução das Desigualdades, Meta 10.2):** apoio à inclusão social e fortalecimento de projetos esportivos comunitários.
