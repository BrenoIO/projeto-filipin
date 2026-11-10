"""Cálculos de frequência usados nas telas de alunos."""
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, or_, select

from .extensions import db
from .models import Aluno, Aula, Graduacao, Presenca

JANELA_DIAS = 30
MESES_HISTORICO = 6


@dataclass
class Resumo:
    presencas_janela: int = 0
    aulas_janela: int = 0
    presencas_desde_graduacao: int = 0
    ultima_graduacao: date | None = None
    ultima_presenca: date | None = None

    @property
    def percentual(self) -> int | None:
        if not self.aulas_janela:
            return None
        return round(100 * self.presencas_janela / self.aulas_janela)


def _ultima_graduacao_subq():
    return (
        select(Graduacao.aluno_id, func.max(Graduacao.data).label("data"))
        .group_by(Graduacao.aluno_id)
        .subquery()
    )


def resumo_alunos(alunos: list[Aluno], hoje: date) -> dict[int, Resumo]:
    """Resumo de frequência de vários alunos com um número fixo de consultas (não uma por aluno)."""
    if not alunos:
        return {}
    ids = [a.id for a in alunos]
    inicio = hoje - timedelta(days=JANELA_DIAS - 1)
    ult = _ultima_graduacao_subq()

    datas_aulas = db.session.scalars(
        select(Aula.data).where(Aula.data.between(inicio, hoje))
    ).all()

    graduacoes = dict(db.session.execute(select(ult.c.aluno_id, ult.c.data).where(ult.c.aluno_id.in_(ids))).all())

    linhas = db.session.execute(
        select(
            Presenca.aluno_id,
            func.count().filter(Aula.data.between(inicio, hoje)),
            func.count().filter(or_(ult.c.data.is_(None), Aula.data >= ult.c.data)),
            func.max(Aula.data),
        )
        .join(Aula, Aula.id == Presenca.aula_id)
        .outerjoin(ult, ult.c.aluno_id == Presenca.aluno_id)
        .where(Presenca.aluno_id.in_(ids))
        .group_by(Presenca.aluno_id)
    ).all()
    por_aluno = {aluno_id: (p, d, u) for aluno_id, p, d, u in linhas}

    resumos = {}
    for aluno in alunos:
        p_janela, desde, ultima = por_aluno.get(aluno.id, (0, 0, None))
        cadastro = aluno.criado_em.date() if aluno.criado_em else inicio
        aulas = sum(1 for d in datas_aulas if d >= cadastro)
        resumos[aluno.id] = Resumo(
            presencas_janela=p_janela,
            # Se a chamada de dias anteriores ao cadastro foi lançada depois, não passamos de 100%.
            aulas_janela=max(aulas, p_janela),
            presencas_desde_graduacao=desde,
            ultima_graduacao=graduacoes.get(aluno.id),
            ultima_presenca=ultima,
        )
    return resumos


def historico_mensal(aluno: Aluno, hoje: date) -> list[dict]:
    """Presenças x aulas dos últimos meses (mais recente primeiro)."""
    ano, mes = hoje.year, hoje.month
    meses: OrderedDict[tuple[int, int], dict] = OrderedDict()
    for _ in range(MESES_HISTORICO):
        meses[(ano, mes)] = {"ano": ano, "mes": mes, "aulas": 0, "presencas": 0}
        ano, mes = (ano - 1, 12) if mes == 1 else (ano, mes - 1)
    mais_antigo = next(reversed(meses))
    inicio = date(mais_antigo[0], mais_antigo[1], 1)

    for d in db.session.scalars(select(Aula.data).where(Aula.data.between(inicio, hoje))):
        meses[(d.year, d.month)]["aulas"] += 1
    for d in db.session.scalars(
        select(Aula.data)
        .join(Presenca, Presenca.aula_id == Aula.id)
        .where(Presenca.aluno_id == aluno.id, Aula.data.between(inicio, hoje))
    ):
        meses[(d.year, d.month)]["presencas"] += 1
    return list(meses.values())


def ultimas_presencas(aluno: Aluno, limite: int = 10) -> list[date]:
    return db.session.scalars(
        select(Aula.data)
        .join(Presenca, Presenca.aula_id == Aula.id)
        .where(Presenca.aluno_id == aluno.id)
        .order_by(Aula.data.desc())
        .limit(limite)
    ).all()
