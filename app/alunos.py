from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from sqlalchemy import select

from .auth import exigir_login
from .extensions import db
from .faixas import FAIXAS, IDADE_MAXIMA, IDADE_MINIMA, MAX_GRAUS, calcular_idade, hoje
from .frequencia import JANELA_DIAS, historico_mensal, resumo_alunos, ultimas_presencas
from .models import Aluno, Graduacao

bp = Blueprint("alunos", __name__, url_prefix="/alunos")
bp.before_request(exigir_login)

MESES = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def _ler_data(texto: str) -> date | None:
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None


def _ler_graus(texto: str, erros: dict) -> int:
    try:
        graus = int(texto or 0)
    except ValueError:
        graus = -1
    if not 0 <= graus <= MAX_GRAUS:
        erros["graus"] = f"Graus devem estar entre 0 e {MAX_GRAUS}."
    return graus


def validar_dados_pessoais(form) -> tuple[dict, dict]:
    erros: dict[str, str] = {}
    dados = {
        "nome": form.get("nome", "").strip(),
        "responsavel": form.get("responsavel", "").strip(),
        "telefone_responsavel": form.get("telefone_responsavel", "").strip() or None,
        "observacao": form.get("observacao", "").strip() or None,
    }

    if not dados["nome"]:
        erros["nome"] = "Informe o nome do aluno."
    elif len(dados["nome"]) > 120:
        erros["nome"] = "Nome muito longo (máx. 120 caracteres)."

    if not dados["responsavel"]:
        erros["responsavel"] = "O responsável é obrigatório."
    elif len(dados["responsavel"]) > 120:
        erros["responsavel"] = "Nome muito longo (máx. 120 caracteres)."

    if dados["telefone_responsavel"] and len(dados["telefone_responsavel"]) > 20:
        erros["telefone_responsavel"] = "Telefone muito longo."

    if dados["observacao"] and len(dados["observacao"]) > 1000:
        erros["observacao"] = "Observação muito longa (máx. 1000 caracteres)."

    nascimento = _ler_data(form.get("data_nascimento", ""))
    if nascimento is None:
        erros["data_nascimento"] = "Informe a data de nascimento."
    else:
        idade = calcular_idade(nascimento)
        if not IDADE_MINIMA <= idade <= IDADE_MAXIMA:
            erros["data_nascimento"] = f"A idade deve estar entre {IDADE_MINIMA} e {IDADE_MAXIMA} anos (idade calculada: {idade})."
    dados["data_nascimento"] = nascimento
    return dados, erros


def _obter_aluno(aluno_id: int) -> Aluno:
    aluno = db.session.get(Aluno, aluno_id)
    if aluno is None:
        abort(404)
    return aluno


def _render_lista(form=None, erros=None, status=200):
    mostrar_inativos = request.args.get("inativos") == "1"
    consulta = select(Aluno).order_by(Aluno.nome)
    if not mostrar_inativos:
        consulta = consulta.where(Aluno.ativo.is_(True))
    alunos = db.session.scalars(consulta).all()
    return (
        render_template(
            "alunos.html",
            alunos=alunos,
            resumos=resumo_alunos(alunos, hoje()),
            janela=JANELA_DIAS,
            mostrar_inativos=mostrar_inativos,
            form=form or {},
            erros=erros or {},
            max_graus=MAX_GRAUS,
        ),
        status,
    )


@bp.get("")
def lista():
    return _render_lista()


@bp.post("")
def cadastrar():
    dados, erros = validar_dados_pessoais(request.form)
    faixa = request.form.get("faixa", "")
    if faixa not in FAIXAS:
        erros["faixa"] = "Selecione uma faixa."
    graus = _ler_graus(request.form.get("graus", "0"), erros)

    if erros:
        flash("Corrija os campos destacados.", "erro")
        return _render_lista(form=request.form, erros=erros, status=400)

    aluno = Aluno(**dados, faixa=faixa, graus=graus)
    db.session.add(aluno)
    db.session.commit()
    flash(f"{aluno.nome} cadastrado(a) com sucesso!", "sucesso")
    return redirect(url_for("alunos.lista"))


def _render_detalhe(aluno: Aluno, form=None, erros=None, status=200):
    return (
        render_template(
            "aluno.html",
            aluno=aluno,
            resumo=resumo_alunos([aluno], hoje())[aluno.id],
            janela=JANELA_DIAS,
            historico=historico_mensal(aluno, hoje()),
            ultimas=ultimas_presencas(aluno),
            meses=MESES,
            hoje=hoje(),
            max_graus=MAX_GRAUS,
            form=form,
            erros=erros or {},
        ),
        status,
    )


@bp.get("/<int:aluno_id>")
def detalhe(aluno_id: int):
    return _render_detalhe(_obter_aluno(aluno_id))


@bp.post("/<int:aluno_id>/editar")
def editar(aluno_id: int):
    aluno = _obter_aluno(aluno_id)
    dados, erros = validar_dados_pessoais(request.form)
    if erros:
        flash("Corrija os campos destacados.", "erro")
        return _render_detalhe(aluno, form=request.form, erros=erros, status=400)
    for campo, valor in dados.items():
        setattr(aluno, campo, valor)
    db.session.commit()
    flash("Dados atualizados.", "sucesso")
    return redirect(url_for("alunos.detalhe", aluno_id=aluno.id))


@bp.post("/<int:aluno_id>/graduar")
def graduar(aluno_id: int):
    aluno = _obter_aluno(aluno_id)
    erros: dict[str, str] = {}
    faixa = request.form.get("faixa", "")
    if faixa not in FAIXAS:
        erros["faixa"] = "Selecione uma faixa."
    graus = _ler_graus(request.form.get("graus", "0"), erros)
    data = _ler_data(request.form.get("data", ""))
    if data is None or data > hoje():
        erros["data"] = "Informe uma data válida (não pode ser no futuro)."
    if not erros and faixa == aluno.faixa and graus == aluno.graus:
        erros["faixa"] = "A faixa e os graus são iguais aos atuais."

    if erros:
        flash("Não foi possível registrar a graduação. " + " ".join(erros.values()), "erro")
        return _render_detalhe(aluno, status=400)

    db.session.add(Graduacao(aluno=aluno, faixa=faixa, graus=graus, data=data, registrado_por_id=g.usuario.id))
    aluno.faixa, aluno.graus = faixa, graus
    db.session.commit()
    flash(f"Graduação registrada: {faixa}, {graus} grau(s).", "sucesso")
    return redirect(url_for("alunos.detalhe", aluno_id=aluno.id))


@bp.post("/<int:aluno_id>/ativo")
def alternar_ativo(aluno_id: int):
    aluno = _obter_aluno(aluno_id)
    aluno.ativo = not aluno.ativo
    db.session.commit()
    flash(f"{aluno.nome} foi {'reativado(a)' if aluno.ativo else 'desativado(a) (não aparece mais na chamada)'}.", "sucesso")
    return redirect(url_for("alunos.detalhe", aluno_id=aluno.id))
