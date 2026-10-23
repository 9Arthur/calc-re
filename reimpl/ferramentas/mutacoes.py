#!/usr/bin/env python3
"""Teste negativo do harness: cada mutação quebra uma regra documentada e tem de derrubar casos do oráculo.

Uso (de reimpl/): .venv/bin/python ferramentas/mutacoes.py
"""
import math
import sys
from fractions import Fraction
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(AQUI), str(AQUI / 'tests')]

from calculadora import formatacao, motor, numerico, teclas, viewmodel  # noqa: E402
from executor import comparar, executar  # noqa: E402
from oraculo import casos, leituras  # noqa: E402

REAIS = {f: leituras(f) for f in ('3a', '3b', '3c', '3d')}


def falhas():
    return [c['id'] for c in casos() if comparar(executar(c)[0], REAIS[c['fase']][c['id']])]


def mutacao(nome, alvo, attr, novo):
    velho = getattr(alvo, attr)
    setattr(alvo, attr, novo)
    try:
        f = falhas()
    finally:
        setattr(alvo, attr, velho)
    print(f"{nome}: {len(f)} casos falham {f[:8]}{' …' if len(f) > 8 else ''}")
    return f


assert not falhas(), 'a reimplementação sem mutação deveria passar'
r = [
    mutacao('arredondar truncando (sem meia unidade)', formatacao, '_arredondar',
            lambda s, e, n: ((s[:n].rstrip('0') or '0'), e) if len(s) > n else (s, e)),
    mutacao('linha BIN sem preenchimento até múltiplo de 4', viewmodel, 'preencher_binario', lambda t: t),
    mutacao('mod científico com sinal do dividendo (fmod)', numerico, 'resto_cientifico',
            lambda x, y: x if y == 0 else Fraction(x - y * int(x / y))),
    mutacao('botão desabilitado também é pressionado', teclas, 'desabilitado', lambda vm, t: False),
    mutacao('agrupamento de milhar desligado', motor, 'agrupar', lambda t, *a, **k: t),
    mutacao('sem corte |y| ≤ 10⁻ᴾ nas funções trigonométricas', numerico, '_corte',
            lambda y, p: numerico.de_mp(y)),
]
print('todas as mutações detectadas' if all(r) else 'ALGUMA MUTAÇÃO NÃO FOI DETECTADA')
