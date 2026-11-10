from datetime import timedelta

from sqlalchemy import func, select

from app.extensions import db
from app.faixas import hoje
from app.frequencia import resumo_alunos
from app.models import Aluno, Aula, Graduacao, Presenca


def _salvar(client, data, ids):
    return client.post("/chamada", data={"data": data.isoformat(), "presentes": [str(i) for i in ids]})


def test_chamada_lista_alunos_ativos(logado, novo_aluno):
    novo_aluno(nome="Ana")
    novo_aluno(nome="Inativo", ativo=False)
    html = logado.get("/chamada").get_data(as_text=True)
    assert "Ana" in html
    assert "Inativo" not in html


def test_salvar_chamada(logado, novo_aluno):
    ana, bia = novo_aluno(nome="Ana"), novo_aluno(nome="Bia")
    resp = _salvar(logado, hoje(), [ana.id])
    assert resp.status_code == 302
    assert db.session.scalar(select(func.count(Aula.id))) == 1
    assert db.session.scalars(select(Presenca.aluno_id)).all() == [ana.id]
    assert "1 presente(s)" in logado.get(resp.headers["Location"]).get_data(as_text=True)


def test_salvar_de_novo_substitui_a_chamada(logado, novo_aluno):
    ana, bia = novo_aluno(nome="Ana"), novo_aluno(nome="Bia")
    _salvar(logado, hoje(), [ana.id, bia.id])
    _salvar(logado, hoje(), [bia.id])
    assert db.session.scalar(select(func.count(Aula.id))) == 1
    assert db.session.scalars(select(Presenca.aluno_id)).all() == [bia.id]


def test_chamada_sem_presentes_registra_a_aula(logado, novo_aluno):
    novo_aluno()
    _salvar(logado, hoje(), [])
    assert db.session.scalar(select(func.count(Aula.id))) == 1


def test_chamada_ignora_ids_inexistentes(logado, novo_aluno):
    ana = novo_aluno()
    _salvar(logado, hoje(), [ana.id, 9999])
    assert db.session.scalars(select(Presenca.aluno_id)).all() == [ana.id]


def test_chamada_nao_aceita_data_futura(logado, novo_aluno):
    ana = novo_aluno()
    _salvar(logado, hoje() + timedelta(days=1), [ana.id])
    assert db.session.scalar(select(func.count(Aula.id))) == 0


def test_resumo_de_frequencia(app, logado, novo_aluno):
    ana, bia = novo_aluno(nome="Ana"), novo_aluno(nome="Bia")
    # Cadastro "antigo", para as aulas passadas contarem no percentual.
    for a in (ana, bia):
        a.criado_em = a.criado_em - timedelta(days=60)
    db.session.commit()

    h = hoje()
    _salvar(logado, h - timedelta(days=40), [ana.id])  # fora da janela de 30 dias
    _salvar(logado, h - timedelta(days=10), [ana.id, bia.id])
    _salvar(logado, h - timedelta(days=5), [ana.id])
    _salvar(logado, h, [bia.id])

    # Ana foi graduada há 7 dias: só conta a presença de 5 dias atrás.
    db.session.add(Graduacao(aluno_id=ana.id, faixa="Cinza", graus=0, data=h - timedelta(days=7)))
    db.session.commit()

    alunos = db.session.scalars(select(Aluno).order_by(Aluno.nome)).all()
    r = resumo_alunos(alunos, h)
    assert (r[ana.id].presencas_janela, r[ana.id].aulas_janela, r[ana.id].percentual) == (2, 3, 67)
    assert r[ana.id].presencas_desde_graduacao == 1
    assert r[ana.id].ultima_graduacao == h - timedelta(days=7)
    assert r[ana.id].ultima_presenca == h - timedelta(days=5)
    assert (r[bia.id].presencas_janela, r[bia.id].presencas_desde_graduacao) == (2, 2)

    assert logado.get("/alunos").status_code == 200
    assert logado.get(f"/alunos/{ana.id}").status_code == 200
