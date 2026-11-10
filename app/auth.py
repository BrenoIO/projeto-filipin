from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db
from .models import Usuario

bp = Blueprint("auth", __name__)

# Usado para gastar o mesmo tempo quando o e-mail não existe (evita descobrir e-mails cadastrados).
_HASH_FALSO = generate_password_hash("senha-inexistente")


@bp.before_app_request
def carregar_usuario():
    uid = session.get("usuario_id")
    g.usuario = db.session.get(Usuario, uid) if uid else None


def exigir_login():
    """Use como before_request nos blueprints que só professores podem acessar."""
    if g.usuario is None:
        return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))


def _destino_seguro(destino: str | None) -> str:
    if destino and destino.startswith("/") and not destino.startswith("//"):
        return destino
    return url_for("chamada.chamada")


@bp.route("/", methods=["GET", "POST"])
def login():
    if g.usuario:
        return redirect(url_for("chamada.chamada"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        usuario = db.session.scalar(select(Usuario).where(Usuario.email == email))

        if usuario is None:
            check_password_hash(_HASH_FALSO, senha)
        elif check_password_hash(usuario.senha_hash, senha):
            session.clear()
            session["usuario_id"] = usuario.id
            session.permanent = True
            return redirect(_destino_seguro(request.args.get("next")))

        flash("E-mail ou senha incorretos.", "erro")
        return render_template("login.html", email=email), 401

    return render_template("login.html")


@bp.post("/sair")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "sucesso")
    return redirect(url_for("auth.login"))
