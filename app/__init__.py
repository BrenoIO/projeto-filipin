import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask

from .extensions import csrf, db
from .faixas import FAIXAS, faixa_info


def _normalizar_url(url: str) -> str:
    """Aceita a URL copiada do Supabase (postgres:// ou postgresql://) e força o driver psycopg 3."""
    for prefixo in ("postgres://", "postgresql://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url[len(prefixo):]
    return url


def create_app(config: dict | None = None) -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=_normalizar_url(os.environ.get("DATABASE_URL", "")),
        # O pooler do Supabase (plano gratuito) aceita poucas conexões: mantemos o pool pequeno.
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_pre_ping": True,
            "pool_size": 3,
            "max_overflow": 2,
            "pool_recycle": 300,
        },
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    )
    if config:
        app.config.update(config)

    if not app.config["SECRET_KEY"] or not app.config["SQLALCHEMY_DATABASE_URI"]:
        raise RuntimeError("Defina SECRET_KEY e DATABASE_URL no arquivo .env (veja .env.example).")

    db.init_app(app)
    csrf.init_app(app)

    from . import alunos, auth, chamada, cli, conta

    app.register_blueprint(auth.bp)
    app.register_blueprint(chamada.bp)
    app.register_blueprint(alunos.bp)
    app.register_blueprint(conta.bp)
    cli.registrar(app)

    # Globais (e não context_processor) para ficarem visíveis também dentro das macros.
    app.jinja_env.globals.update(FAIXAS=FAIXAS, faixa_info=faixa_info)

    @app.template_filter("data_br")
    def _data_br(valor):
        return valor.strftime("%d/%m/%Y") if valor else "—"

    return app
