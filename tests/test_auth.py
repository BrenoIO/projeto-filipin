import pytest

from tests.conftest import SENHA


@pytest.mark.parametrize("url", ["/chamada", "/alunos", "/alunos/1"])
def test_paginas_exigem_login(client, url):
    resp = client.get(url)
    assert resp.status_code == 302
    assert resp.headers["Location"].startswith("/?next=")


def test_login_com_sucesso_vai_para_chamada(client):
    resp = client.post("/", data={"email": "  PROF@teste.com ", "senha": SENHA})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/chamada"
    assert client.get("/chamada").status_code == 200


def test_login_redireciona_para_next(client):
    resp = client.post("/?next=/alunos", data={"email": "prof@teste.com", "senha": SENHA})
    assert resp.headers["Location"] == "/alunos"


def test_login_nao_redireciona_para_outro_site(client):
    resp = client.post("/?next=//site-malicioso.com", data={"email": "prof@teste.com", "senha": SENHA})
    assert resp.headers["Location"] == "/chamada"


@pytest.mark.parametrize("email,senha", [("prof@teste.com", "errada"), ("ninguem@teste.com", SENHA)])
def test_login_invalido(client, email, senha):
    resp = client.post("/", data={"email": email, "senha": senha})
    assert resp.status_code == 401
    assert "E-mail ou senha incorretos" in resp.get_data(as_text=True)


def test_logout(logado):
    logado.post("/sair")
    assert logado.get("/chamada").status_code == 302


def test_csrf_ativo_fora_dos_testes(app):
    app.config["WTF_CSRF_ENABLED"] = True
    resp = app.test_client().post("/", data={"email": "prof@teste.com", "senha": SENHA})
    assert resp.status_code == 400
