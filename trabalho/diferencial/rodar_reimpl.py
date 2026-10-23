"""Executa os casos de relatorio/03-diferencial-casos.json na reimplementação e grava
trabalho/diferencial/reimpl-saida.json (visor final e estado de erro). Confere antes o hash da reimplementação
registrado no arquivo congelado.

Uso: reimpl/.venv/bin/python trabalho/diferencial/rodar_reimpl.py [--casos relatorio/X.json] [--saida Y.json]
     [--livre]   (--livre: não exige o hash congelado; registra o hash atual — só para reimplementação já corrigida)
"""
import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'reimpl'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from calculadora import Calculadora, pressionar  # noqa: E402
from gerar_casos import sha256_arvore  # noqa: E402


def executar(caso):
    vm = Calculadora(caso['modo'])
    p = caso['preparo']
    if 'angulo' in p:
        vm.definir_angulo(p['angulo'])
    if 'base' in p:
        vm.definir_base(p['base'])
    if 'tamanho' in p:
        vm.definir_tamanho(p['tamanho'])
    if 'deslocamento' in p:
        vm.deslocamento = p['deslocamento']
    notas = []
    for tok in caso['passos']:
        try:
            if not pressionar(vm, tok):
                notas.append(f'{tok} desabilitado, não pressionado')
        except Exception as e:  # registra e segue, como a automação
            notas.append(f'{tok}: exceção {type(e).__name__}: {e}')
    return {'id': caso['id'], 'visor': vm.visor, 'erro': vm.em_erro, 'notas': notas}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--casos', default='relatorio/03-diferencial-casos.json')
    ap.add_argument('--saida', default='trabalho/diferencial/reimpl-saida.json')
    ap.add_argument('--livre', action='store_true')
    a = ap.parse_args()
    doc = json.loads((RAIZ / a.casos).read_text(encoding='utf-8'))
    h = sha256_arvore(RAIZ / 'reimpl' / 'calculadora')
    esperado = doc['reimplementacao_congelada']['sha256_arvore']
    if h != esperado and not a.livre:
        sys.exit(f'reimplementação mudou desde o congelamento: {h} != {esperado}')
    saida = [executar(c) for c in doc['casos']]
    destino = RAIZ / a.saida
    destino.write_text(json.dumps({'sha256_arvore': h, 'congelada': h == esperado, 'resultados': saida},
                                  ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'{len(saida)} casos -> {destino}')


if __name__ == '__main__':
    main()
