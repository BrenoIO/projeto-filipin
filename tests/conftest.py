from datetime import date

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Aluno, Usuario

SENHA = "senha-de-teste-123"


@pytest.fixture
def app(monkeypatch):
    # Os testes usam SQLite em memória: não dependem do Supabase nem de internet.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "teste",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SQLALCHEMY_ENGINE_OPTIONS": {},
            "WTF_CSRF_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()
        db.session.add(Usuario(nome="Prof. Teste", email="prof@teste.com", senha_hash=generate_password_hash(SENHA)))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logado(client):
    client.post("/", data={"email": "prof@teste.com", "senha": SENHA})
    return client


@pytest.fixture
def novo_aluno(app):
    def _criar(nome="Ana", nascimento=date(2016, 5, 10), faixa="Branca", ativo=True):
        aluno = Aluno(nome=nome, data_nascimento=nascimento, responsavel="Mãe", faixa=faixa, graus=0, ativo=ativo)
        db.session.add(aluno)
        db.session.commit()
        return aluno

    return _criar
