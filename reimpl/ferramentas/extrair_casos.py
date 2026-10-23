#!/usr/bin/env python3
"""Extrai os casos (passos realmente executados) de `trabalho/automacao/rodar-casos.ps1` para `tests/casos.json`.

Os passos usam a notação do script, que é a transcrição máquina das teclas dos arquivos congelados
`relatorio/03*-casos-de-teste.md`. O teste `test_congelados.py` confere que os IDs coincidem com os desses arquivos.

Uso: python3 -I ferramentas/extrair_casos.py <raiz do projeto>
"""
import ast
import json
import re
import sys
from pathlib import Path

raiz = Path(sys.argv[1] if len(sys.argv) > 1 else '..').resolve()
ps1 = (raiz / 'trabalho/automacao/rodar-casos.ps1').read_text(encoding='utf-8')


def avaliar(expr):
    """Só literais de string, `+` e `*` (ex.: `('1 + 1 =' + (' =' * 20))`, `'#1' + ('0' * 64)`)."""
    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (str, int)):
            return n.value
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mult)):
            a, b = ev(n.left), ev(n.right)
            return a + b if isinstance(n.op, ast.Add) else a * b
        raise ValueError(ast.dump(n))
    return ev(ast.parse(expr.strip(), mode='eval').body)


casos = []
for m in re.finditer(r"^\s*@\{ (Id = '(3[a-d]-\d+c?)'.*) \}\s*$", ps1, re.M):
    campos = {}
    corpo = m.group(1)
    passos = re.search(r"Passos = (.*)$", corpo).group(1)
    for k, v in re.findall(r"(\w+) = '([^']*)'", corpo.split('Passos =')[0]):
        campos[k] = v
    campos['Passos'] = avaliar(passos)
    casos.append(campos)

vistos, saida = set(), []
for c in casos:
    if c['Id'] in vistos:
        sys.exit(f"ID repetido: {c['Id']}")
    vistos.add(c['Id'])
    fase = c['Id'][:2]
    modo = {'1': 'padrao', '2': 'cientifico'}.get(c.get('Modo'), 'cientifico' if fase == '3c' else 'programador')
    saida.append({'id': c['Id'], 'fase': fase, 'modo': modo, 'angulo': c.get('Ang'), 'base': c.get('Base'),
                  'tamanho': c.get('Tam'), 'deslocamento': c.get('Desl'),
                  'passos': [t for t in c['Passos'].split(' ') if t]})

destino = Path(__file__).resolve().parent.parent / 'tests' / 'casos.json'
destino.write_text(json.dumps({'fonte': 'trabalho/automacao/rodar-casos.ps1', 'casos': saida}, ensure_ascii=False,
                              indent=1), encoding='utf-8')
por_fase = {}
for c in saida:
    por_fase[c['fase']] = por_fase.get(c['fase'], 0) + 1
print(destino, por_fase)
