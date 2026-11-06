from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    cargo = Column(String, default="professor")

class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    faixa = Column(String, nullable=False)
    idade = Column(Integer, nullable=False)
    responsavel = Column(String, nullable=False)  # Obrigatório para menores
    observacao = Column(Text, nullable=True)     # Restrições ou alergias
    ativo = Column(Boolean, default=True)

class Presenca(Base):
    __tablename__ = "presencas"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"))
    data_aula = Column(DateTime(timezone=True), server_default=func.now())
    presente = Column(Boolean, default=True)