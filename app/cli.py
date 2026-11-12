import click
from flask import Flask
from sqlalchemy import select, text
from werkzeug.security import generate_password_hash

from .extensions import db
from .models import Usuario


def registrar(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db():
        """Cria as tabelas que ainda não existem."""
        db.create_all()
        if db.engine.dialect.name == "postgresql":
            # No Supabase, tabelas do schema "public" ficam expostas pela API REST pública.
            # Ligar o RLS sem políticas bloqueia esse acesso; o app conecta como dono das
            # tabelas (usuário postgres) e por isso não é afetado.
            with db.engine.begin() as conn:
                for tabela in db.metadata.sorted_tables:
                    conn.execute(text(f'ALTER TABLE public."{tabela.name}" ENABLE ROW LEVEL SECURITY'))
        click.echo("Tabelas criadas/verificadas.")

    @app.cli.command("criar-professor")
    @click.option("--nome", prompt="Nome")
    @click.option("--email", prompt="E-mail")
    @click.password_option("--senha", prompt="Senha", confirmation_prompt="Repita a senha")
    def criar_professor(nome: str, email: str, senha: str):
        """Cadastra um professor (ou redefine a senha, se o e-mail já existir)."""
        email = email.strip().lower()
        if len(senha) < 8:
            raise click.ClickException("A senha precisa ter pelo menos 8 caracteres.")
        usuario = db.session.scalar(select(Usuario).where(Usuario.email == email))
        if usuario:
            usuario.nome = nome.strip()
            usuario.senha_hash = generate_password_hash(senha)
            msg = f"Professor {email} atualizado."
        else:
            db.session.add(Usuario(nome=nome.strip(), email=email, senha_hash=generate_password_hash(senha)))
            msg = f"Professor {email} criado."
        db.session.commit()
        click.echo(msg)

    @app.cli.command("proteger-professor")
    @click.argument("email")
    @click.option("--desfazer", is_flag=True, help="Tira a proteção em vez de colocar.")
    def proteger_professor(email: str, desfazer: bool):
        """Impede (ou volta a permitir) que a conta seja removida pela tela de Professores."""
        usuario = db.session.scalar(select(Usuario).where(Usuario.email == email.strip().lower()))
        if usuario is None:
            raise click.ClickException(f"Nenhum professor com o e-mail {email}.")
        usuario.protegido = not desfazer
        db.session.commit()
        click.echo(f"Conta de {usuario.nome} {'desprotegida' if desfazer else 'protegida'}.")
