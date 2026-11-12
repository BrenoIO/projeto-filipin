from sqlalchemy import func, select
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import Usuario
from tests.conftest import SENHA


def _eu():
    return db.session.get(Usuario, 1)  # professor criado no conftest


def test_paginas_exigem_login(client):
    assert client.get("/conta").status_code == 302
    assert client.get("/professores").status_code == 302


def test_trocar_nome_sem_senha(logado):
    resp = logado.post("/conta/dados", data={"nome": "Breno", "email": "prof@teste.com"})
    assert resp.status_code == 302
    assert _eu().nome == "Breno"


def test_trocar_email_exige_senha_atual(logado):
    resp = logado.post("/conta/dados", data={"nome": "Prof", "email": "novo@teste.com", "senha_atual": "errada"})
    assert resp.status_code == 400
    assert _eu().email == "prof@teste.com"

    resp = logado.post("/conta/dados", data={"nome": "Prof", "email": "Novo@Teste.com", "senha_atual": SENHA})
    assert resp.status_code == 302
    assert _eu().email == "novo@teste.com"


def test_nao_aceita_email_de_outro_professor(logado):
    db.session.add(Usuario(nome="Outro", email="outro@teste.com", senha_hash=generate_password_hash("x" * 8)))
    db.session.commit()
    resp = logado.post("/conta/dados", data={"nome": "Prof", "email": "outro@teste.com", "senha_atual": SENHA})
    assert resp.status_code == 400
    assert "já é usado" in resp.get_data(as_text=True)


def test_trocar_senha(logado, client):
    dados = {"senha_atual": SENHA, "senha_nova": "nova-senha-123", "senha_confirmacao": "nova-senha-123"}
    assert logado.post("/conta/senha", data=dados).status_code == 302
    assert check_password_hash(_eu().senha_hash, "nova-senha-123")


def test_trocar_senha_valida_campos(logado):
    casos = [
        {"senha_atual": "errada", "senha_nova": "nova-senha-123", "senha_confirmacao": "nova-senha-123"},
        {"senha_atual": SENHA, "senha_nova": "curta", "senha_confirmacao": "curta"},
        {"senha_atual": SENHA, "senha_nova": "nova-senha-123", "senha_confirmacao": "diferente-123"},
    ]
    for dados in casos:
        assert logado.post("/conta/senha", data=dados).status_code == 400
    assert check_password_hash(_eu().senha_hash, SENHA)


def test_adicionar_professor_e_ele_consegue_entrar(logado, app):
    dados = {"nome": "Carla", "email": "carla@teste.com", "senha_nova": "senha-carla-1", "senha_confirmacao": "senha-carla-1"}
    assert logado.post("/professores", data=dados).status_code == 302
    assert "Carla" in logado.get("/professores").get_data(as_text=True)

    outro = app.test_client()
    assert outro.post("/", data={"email": "carla@teste.com", "senha": "senha-carla-1"}).status_code == 302


def test_adicionar_professor_com_email_repetido(logado):
    dados = {"nome": "X", "email": "prof@teste.com", "senha_nova": "senha-123456", "senha_confirmacao": "senha-123456"}
    assert logado.post("/professores", data=dados).status_code == 400
    assert db.session.scalar(select(func.count(Usuario.id))) == 1


def test_remover_professor(logado):
    db.session.add(Usuario(nome="Outro", email="outro@teste.com", senha_hash=generate_password_hash("x" * 8)))
    db.session.commit()
    outro_id = db.session.scalar(select(Usuario.id).where(Usuario.email == "outro@teste.com"))
    assert logado.post(f"/professores/{outro_id}/remover").status_code == 302
    assert db.session.get(Usuario, outro_id) is None


def test_nao_pode_remover_a_si_mesmo(logado):
    logado.post(f"/professores/{_eu().id}/remover")
    assert _eu() is not None


def test_conta_protegida_nao_pode_ser_removida(logado):
    db.session.add(Usuario(nome="Dono", email="dono@teste.com", senha_hash=generate_password_hash("x" * 8), protegido=True))
    db.session.commit()
    dono_id = db.session.scalar(select(Usuario.id).where(Usuario.email == "dono@teste.com"))

    pagina = logado.get("/professores").get_data(as_text=True)
    assert f"/professores/{dono_id}/remover" not in pagina
    assert "Protegida" in pagina

    resp = logado.post(f"/professores/{dono_id}/remover", follow_redirects=True)
    assert "é protegida" in resp.get_data(as_text=True)
    assert db.session.get(Usuario, dono_id) is not None


def test_comando_proteger_professor(app):
    runner = app.test_cli_runner()
    assert "protegida" in runner.invoke(args=["proteger-professor", "Prof@Teste.com"]).output
    assert _eu().protegido
    runner.invoke(args=["proteger-professor", "prof@teste.com", "--desfazer"])
    assert not _eu().protegido
