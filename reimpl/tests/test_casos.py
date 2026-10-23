"""Um teste por caso congelado das fases 3a–3d, com os resultados reais como oráculo."""
import pytest

from executor import comparar, executar
from oraculo import casos, leituras

REAIS = {f: leituras(f) for f in ('3a', '3b', '3c', '3d')}


@pytest.mark.parametrize('caso', casos(), ids=lambda c: c['id'])
def test_caso(caso):
    reais = REAIS[caso['fase']].get(caso['id'])
    assert reais, f"sem resultado real para {caso['id']}"
    fotos, _notas = executar(caso)
    div = comparar(fotos, reais)
    assert not div, '\n'.join(div)
