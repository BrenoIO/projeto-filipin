from datetime import date, timedelta

from sqlalchemy import select

from app.extensions import db
from app.faixas import hoje
from app.models import Aluno, Graduacao


def _form(**extra):
    dados = {
        "nome": "João Silva",
        "data_nascimento": "2015-03-20",
        "responsavel": "Maria Silva",
        "telefone_responsavel": "(11) 91234-5678",
        "observacao": "Alergia a amendoim",
        "faixa": "Cinza e Branca",
        "graus": "1",
    }
    dados.update(extra)
    return dados


def test_cadastrar_aluno(logado):
    resp = logado.post("/alunos", data=_form())
    assert resp.status_code == 302
    aluno = db.session.scalar(select(Aluno))
    assert aluno.nome == "João Silva"
    assert aluno.faixa == "Cinza e Branca" and aluno.graus == 1
    assert "João Silva" in logado.get("/alunos").get_data(as_text=True)


def test_responsavel_obrigatorio(logado):
    resp = logado.post("/alunos", data=_form(responsavel="  "))
    assert resp.status_code == 400
    assert "responsável é obrigatório" in resp.get_data(as_text=True)
    assert db.session.scalar(select(Aluno)) is None


def test_rejeita_maior_de_idade(logado):
    nascimento = date(hoje().year - 18, 1, 1).isoformat()
    resp = logado.post("/alunos", data=_form(data_nascimento=nascimento))
    assert resp.status_code == 400
    assert "entre 3 e 17 anos" in resp.get_data(as_text=True)


def test_rejeita_faixa_fora_da_lista(logado):
    resp = logado.post("/alunos", data=_form(faixa="Preta"))
    assert resp.status_code == 400


def test_texto_do_usuario_e_escapado(logado):
    logado.post("/alunos", data=_form(nome="<script>alert(1)</script>"))
    html = logado.get("/alunos").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_editar_aluno(logado, novo_aluno):
    aluno = novo_aluno()
    resp = logado.post(f"/alunos/{aluno.id}/editar", data=_form(nome="Ana Souza"))
    assert resp.status_code == 302
    assert db.session.get(Aluno, aluno.id).nome == "Ana Souza"


def test_graduar_aluno(logado, novo_aluno):
    aluno = novo_aluno()
    resp = logado.post(
        f"/alunos/{aluno.id}/graduar", data={"faixa": "Cinza e Branca", "graus": "0", "data": hoje().isoformat()}
    )
    assert resp.status_code == 302
    aluno = db.session.get(Aluno, aluno.id)
    assert aluno.faixa == "Cinza e Branca"
    assert db.session.scalar(select(Graduacao)).faixa == "Cinza e Branca"


def test_graduacao_nao_aceita_data_futura(logado, novo_aluno):
    aluno = novo_aluno()
    amanha = (hoje() + timedelta(days=1)).isoformat()
    resp = logado.post(f"/alunos/{aluno.id}/graduar", data={"faixa": "Cinza", "graus": "0", "data": amanha})
    assert resp.status_code == 400
    assert db.session.scalar(select(Graduacao)) is None


def test_desativar_aluno_esconde_da_lista(logado, novo_aluno):
    aluno = novo_aluno(nome="Bruno")
    logado.post(f"/alunos/{aluno.id}/ativo", follow_redirects=True)  # consome a mensagem de confirmação
    assert "Bruno" not in logado.get("/alunos").get_data(as_text=True)
    assert "Bruno" in logado.get("/alunos?inativos=1").get_data(as_text=True)


def test_aluno_inexistente(logado):
    assert logado.get("/alunos/999").status_code == 404
