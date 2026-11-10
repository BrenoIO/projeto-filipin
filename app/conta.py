"""Minha conta (nome, e-mail e senha do professor logado) e cadastro de outros professores."""
import re

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from sqlalchemy import func, select
from werkzeug.security import check_password_hash, generate_password_hash

from .auth import exigir_login
from .extensions import db
from .models import Usuario

bp = Blueprint("conta", __name__)
bp.before_request(exigir_login)

SENHA_MIN = 8
SENHA_MAX = 128
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_nome_email(nome: str, email: str, erros: dict, ignorar_id: int | None = None) -> None:
    if not nome:
        erros["nome"] = "Informe o nome."
    elif len(nome) > 120:
        erros["nome"] = "Nome muito longo (máx. 120 caracteres)."

    if not _EMAIL.match(email) or len(email) > 254:
        erros["email"] = "Informe um e-mail válido."
    else:
        outro = db.session.scalar(select(Usuario).where(Usuario.email == email))
        if outro and outro.id != ignorar_id:
            erros["email"] = "Este e-mail já é usado por outro professor."


def validar_nova_senha(senha: str, confirmacao: str, erros: dict) -> None:
    if len(senha) < SENHA_MIN:
        erros["senha_nova"] = f"A senha precisa ter pelo menos {SENHA_MIN} caracteres."
    elif len(senha) > SENHA_MAX:
        erros["senha_nova"] = f"A senha pode ter no máximo {SENHA_MAX} caracteres."
    elif senha != confirmacao:
        erros["senha_confirmacao"] = "As senhas não são iguais."


def _senha_atual_ok(erros: dict) -> bool:
    if not check_password_hash(g.usuario.senha_hash, request.form.get("senha_atual", "")):
        erros["senha_atual"] = "Senha atual incorreta."
        return False
    return True


# ---------------------------------------------------------------- Minha conta

def _render_conta(form_dados=None, erros_dados=None, erros_senha=None, status=200):
    return (
        render_template(
            "conta.html",
            dados=form_dados or {"nome": g.usuario.nome, "email": g.usuario.email},
            erros_dados=erros_dados or {},
            erros_senha=erros_senha or {},
            senha_min=SENHA_MIN,
        ),
        status,
    )


@bp.get("/conta")
def conta():
    return _render_conta()


@bp.post("/conta/dados")
def salvar_dados():
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    erros: dict[str, str] = {}
    validar_nome_email(nome, email, erros, ignorar_id=g.usuario.id)
    # Trocar o e-mail (que é o login) exige confirmar a senha.
    if email != g.usuario.email:
        _senha_atual_ok(erros)

    if erros:
        flash("Não foi possível salvar. Corrija os campos destacados.", "erro")
        return _render_conta(form_dados={"nome": nome, "email": email}, erros_dados=erros, status=400)

    g.usuario.nome, g.usuario.email = nome, email
    db.session.commit()
    flash("Dados atualizados.", "sucesso")
    return redirect(url_for("conta.conta"))


@bp.post("/conta/senha")
def trocar_senha():
    erros: dict[str, str] = {}
    if _senha_atual_ok(erros):
        validar_nova_senha(request.form.get("senha_nova", ""), request.form.get("senha_confirmacao", ""), erros)

    if erros:
        flash("Não foi possível trocar a senha. Corrija os campos destacados.", "erro")
        return _render_conta(erros_senha=erros, status=400)

    g.usuario.senha_hash = generate_password_hash(request.form["senha_nova"])
    db.session.commit()
    flash("Senha alterada com sucesso.", "sucesso")
    return redirect(url_for("conta.conta"))


# ---------------------------------------------------------------- Professores

def _render_professores(form=None, erros=None, status=200):
    professores = db.session.scalars(select(Usuario).order_by(func.lower(Usuario.nome))).all()
    return (
        render_template(
            "professores.html",
            professores=professores,
            form=form or {},
            erros=erros or {},
            senha_min=SENHA_MIN,
        ),
        status,
    )


@bp.get("/professores")
def professores():
    return _render_professores()


@bp.post("/professores")
def adicionar_professor():
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha_nova", "")
    erros: dict[str, str] = {}
    validar_nome_email(nome, email, erros)
    validar_nova_senha(senha, request.form.get("senha_confirmacao", ""), erros)

    if erros:
        flash("Não foi possível cadastrar. Corrija os campos destacados.", "erro")
        return _render_professores(form={"nome": nome, "email": email}, erros=erros, status=400)

    db.session.add(Usuario(nome=nome, email=email, senha_hash=generate_password_hash(senha)))
    db.session.commit()
    flash(f"Professor(a) {nome} cadastrado(a). Passe o e-mail e a senha para a pessoa entrar.", "sucesso")
    return redirect(url_for("conta.professores"))


@bp.post("/professores/<int:usuario_id>/remover")
def remover_professor(usuario_id: int):
    professor = db.session.get(Usuario, usuario_id)
    if professor is None:
        abort(404)
    if professor.id == g.usuario.id:
        flash("Você não pode remover a si mesmo(a).", "erro")
        return redirect(url_for("conta.professores"))

    nome = professor.nome
    db.session.delete(professor)
    db.session.commit()
    flash(f"Acesso de {nome} removido.", "sucesso")
    return redirect(url_for("conta.professores"))
