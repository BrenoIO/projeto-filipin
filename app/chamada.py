from datetime import date

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from sqlalchemy import func, or_, select

from .auth import exigir_login
from .extensions import db
from .faixas import hoje
from .models import Aluno, Aula, Presenca

bp = Blueprint("chamada", __name__, url_prefix="/chamada")
bp.before_request(exigir_login)


def _ler_data(texto: str | None) -> date | None:
    if not texto:
        return hoje()
    try:
        d = date.fromisoformat(texto)
    except ValueError:
        return None
    return d if d <= hoje() else None


@bp.get("")
def chamada():
    data = _ler_data(request.args.get("data"))
    if data is None:
        flash("Data inválida (não pode ser no futuro).", "erro")
        return redirect(url_for("chamada.chamada"))

    aula = db.session.scalar(select(Aula).where(Aula.data == data))
    presentes = {p.aluno_id for p in aula.presencas} if aula else set()

    # Alunos ativos + quem estava presente nesse dia, mesmo que tenha sido desativado depois.
    alunos = db.session.scalars(
        select(Aluno).where(or_(Aluno.ativo.is_(True), Aluno.id.in_(presentes))).order_by(Aluno.nome)
    ).all()

    ultimas = db.session.execute(
        select(Aula.data, func.count(Presenca.id))
        .outerjoin(Presenca, Presenca.aula_id == Aula.id)
        .group_by(Aula.id, Aula.data)
        .order_by(Aula.data.desc())
        .limit(7)
    ).all()

    return render_template(
        "chamada.html",
        data=data,
        hoje=hoje(),
        aula=aula,
        alunos=alunos,
        presentes=presentes,
        ultimas=ultimas,
    )


@bp.post("")
def salvar():
    data = _ler_data(request.form.get("data"))
    if data is None:
        flash("Data inválida (não pode ser no futuro).", "erro")
        return redirect(url_for("chamada.chamada"))

    try:
        ids = {int(i) for i in request.form.getlist("presentes")}
    except ValueError:
        flash("Lista de presença inválida.", "erro")
        return redirect(url_for("chamada.chamada", data=data.isoformat()))
    if ids:
        ids = set(db.session.scalars(select(Aluno.id).where(Aluno.id.in_(ids))))

    aula = db.session.scalar(select(Aula).where(Aula.data == data))
    if aula is None:
        aula = Aula(data=data)
        db.session.add(aula)
    aula.registrado_por_id = g.usuario.id
    # Aplica só a diferença em relação à chamada já salva (remove quem saiu, adiciona quem entrou).
    for presenca in list(aula.presencas):
        if presenca.aluno_id not in ids:
            aula.presencas.remove(presenca)
    ja_presentes = {p.aluno_id for p in aula.presencas}
    aula.presencas.extend(Presenca(aluno_id=i) for i in sorted(ids - ja_presentes))
    db.session.commit()

    flash(f"Chamada de {data.strftime('%d/%m/%Y')} salva: {len(ids)} presente(s).", "sucesso")
    return redirect(url_for("chamada.chamada", data=data.isoformat()))
