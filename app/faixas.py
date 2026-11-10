"""Faixas infantis (4 a 15 anos) da IBJJF, em ordem de progressão.

Cada faixa tem a cor principal e, quando houver, a cor da listra central.
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo

BRANCO = "#ffffff"
PRETO = "#111111"
CINZA = "#8a8a8a"
AMARELO = "#f2c400"
LARANJA = "#f07c00"
VERDE = "#2e8b3d"

_DEFINICAO = [
    ("Branca", BRANCO, None),
    ("Cinza e Branca", CINZA, BRANCO),
    ("Cinza", CINZA, None),
    ("Cinza e Preta", CINZA, PRETO),
    ("Amarela e Branca", AMARELO, BRANCO),
    ("Amarela", AMARELO, None),
    ("Amarela e Preta", AMARELO, PRETO),
    ("Laranja e Branca", LARANJA, BRANCO),
    ("Laranja", LARANJA, None),
    ("Laranja e Preta", LARANJA, PRETO),
    ("Verde e Branca", VERDE, BRANCO),
    ("Verde", VERDE, None),
    ("Verde e Preta", VERDE, PRETO),
]

FAIXAS = [nome for nome, _, _ in _DEFINICAO]
_INFO = {nome: {"cor": cor, "listra": listra or cor} for nome, cor, listra in _DEFINICAO}

MAX_GRAUS = 4
IDADE_MINIMA = 3
IDADE_MAXIMA = 17

FUSO = ZoneInfo("America/Sao_Paulo")


def faixa_info(nome: str) -> dict:
    return _INFO.get(nome, {"cor": BRANCO, "listra": BRANCO})


def hoje() -> date:
    """Data de hoje no horário de Brasília (o servidor pode estar em UTC)."""
    return datetime.now(FUSO).date()


def calcular_idade(nascimento: date, referencia: date | None = None) -> int:
    ref = referencia or hoje()
    return ref.year - nascimento.year - ((ref.month, ref.day) < (nascimento.month, nascimento.day))
