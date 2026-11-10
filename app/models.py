from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db
from .faixas import calcular_idade


def _agora():
    return datetime.now(timezone.utc)


class Usuario(db.Model):
    """Professor/instrutor com acesso ao sistema."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


class Aluno(db.Model):
    __tablename__ = "alunos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), index=True)
    data_nascimento: Mapped[date] = mapped_column(Date)
    responsavel: Mapped[str] = mapped_column(String(120))
    telefone_responsavel: Mapped[str | None] = mapped_column(String(20))
    faixa: Mapped[str] = mapped_column(String(30))
    graus: Mapped[int] = mapped_column(Integer, default=0)
    observacao: Mapped[str | None] = mapped_column(Text)  # alergias, restrições, remédios
    ativo: Mapped[bool] = mapped_column(default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)

    presencas: Mapped[list["Presenca"]] = relationship(
        back_populates="aluno", cascade="all, delete-orphan", passive_deletes=True
    )
    graduacoes: Mapped[list["Graduacao"]] = relationship(
        back_populates="aluno",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by=lambda: [Graduacao.data.desc(), Graduacao.id.desc()],
    )

    @property
    def idade(self) -> int:
        return calcular_idade(self.data_nascimento)


class Aula(db.Model):
    """Um dia de treino em que a chamada foi feita (a academia tem uma única turma)."""

    __tablename__ = "aulas"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[date] = mapped_column(Date, unique=True, index=True)
    registrado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora, onupdate=_agora)

    presencas: Mapped[list["Presenca"]] = relationship(
        back_populates="aula", cascade="all, delete-orphan", passive_deletes=True
    )


class Presenca(db.Model):
    __tablename__ = "presencas"
    __table_args__ = (UniqueConstraint("aula_id", "aluno_id", name="uq_presenca_aula_aluno"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    aula_id: Mapped[int] = mapped_column(ForeignKey("aulas.id", ondelete="CASCADE"), index=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("alunos.id", ondelete="CASCADE"), index=True)

    aula: Mapped[Aula] = relationship(back_populates="presencas")
    aluno: Mapped[Aluno] = relationship(back_populates="presencas")


class Graduacao(db.Model):
    """Histórico de troca de faixa ou de grau, decidida pelo professor."""

    __tablename__ = "graduacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("alunos.id", ondelete="CASCADE"), index=True)
    faixa: Mapped[str] = mapped_column(String(30))
    graus: Mapped[int] = mapped_column(Integer, default=0)
    data: Mapped[date] = mapped_column(Date)
    registrado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))

    aluno: Mapped[Aluno] = relationship(back_populates="graduacoes")
