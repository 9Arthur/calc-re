"""Integridade do oráculo: arquivos de casos congelados com o hash de hashes-originais.txt e os mesmos IDs que
tests/casos.json; e o estado inicial dos botões do Padrão (linha BASE da Fase 4)."""
import hashlib
import re

import pytest

from executor import foto
from calculadora import Calculadora
from oraculo import ARQ_CONGELADO, RAIZ, REL, casos, estado_base_3a

HASHES = dict(reversed(l.split()) for l in (RAIZ / 'hashes-originais.txt').read_text().splitlines() if l.strip())


@pytest.mark.parametrize('fase', sorted(ARQ_CONGELADO))
def test_arquivo_congelado(fase):
    arq = REL / ARQ_CONGELADO[fase]
    assert hashlib.sha256(arq.read_bytes()).hexdigest() == HASHES[f'relatorio/{arq.name}']
    ids = set(re.findall(rf'^\| ({fase}-\d+c?) \|', arq.read_text(encoding='utf-8'), re.M))
    assert ids == {c['id'] for c in casos(fase)}


def test_estado_inicial_padrao():
    base = estado_base_3a()
    est = foto(Calculadora('padrao'))['botoes']
    assert {b: est.get(b) for b in base} == base
