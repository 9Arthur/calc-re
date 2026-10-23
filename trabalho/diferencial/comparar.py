"""Compara a Calculadora real (relatorio/resultados-reais-diferencial.jsonl, Etapa Diferencial do rodar-casos.ps1)
com a reimplementação (trabalho/diferencial/reimpl-saida.json). Critério pré-registrado em 03-diferencial-casos.json:
acerto = visor idêntico E estado de erro igual (real: plusButton.IsEnabled == False; reimpl: em_erro).

Grava trabalho/diferencial/comparacao.json e imprime a taxa por modo e as divergências.
Uso: python3 -I trabalho/diferencial/comparar.py [--casos relatorio/X.json] [--reais relatorio/Y.jsonl]
     [--reimpl trabalho/diferencial/Z.json] [--saida trabalho/diferencial/W.json] [--filtro REGEX_DE_ID]
"""
import argparse
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIF = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--casos', default='relatorio/03-diferencial-casos.json')
    ap.add_argument('--reais', default='relatorio/resultados-reais-diferencial.jsonl')
    ap.add_argument('--reimpl', default='trabalho/diferencial/reimpl-saida.json')
    ap.add_argument('--saida', default='trabalho/diferencial/comparacao.json')
    ap.add_argument('--filtro', default='')
    a = ap.parse_args()
    casos = json.loads((RAIZ / a.casos).read_text(encoding='utf-8'))['casos']
    casos = [c for c in casos if re.search(a.filtro, c['id'])]
    reais = {}
    for linha in (RAIZ / a.reais).read_text(encoding='utf-8-sig').splitlines():
        if linha.strip() and not linha.startswith('#'):
            r = json.loads(linha)
            reais.setdefault(r['id'], r)          # primeira passada: a primeira linha de cada ID vale
    rei = {r['id']: r for r in json.loads((RAIZ / a.reimpl).read_text(encoding='utf-8'))['resultados']}
    linhas, por_modo = [], {}
    for c in casos:
        r, m = reais.get(c['id']), rei[c['id']]
        est = por_modo.setdefault(c['modo'], {'casos': 0, 'acertos': 0, 'sem_leitura': 0, 'com_falha_automacao': 0})
        est['casos'] += 1
        if r is None:
            est['sem_leitura'] += 1
            linhas.append({'id': c['id'], 'status': 'sem leitura real'})
            continue
        erro_real = r.get('mais_habilitado') is False
        ok_visor, ok_erro = r['visor'] == m['visor'], erro_real == m['erro']
        falha = bool(r.get('falha')) or any('exceção' in n or 'ausente' in n or 'não abriu' in n or 'não fechou' in n
                                            for n in r.get('notas', []))
        est['com_falha_automacao'] += falha
        acerto = ok_visor and ok_erro
        est['acertos'] += acerto
        linhas.append({'id': c['id'], 'modo': c['modo'], 'preparo': c['preparo'], 'passos': ' '.join(c['passos']),
                       'acerto': acerto, 'visor_real': r['visor'], 'visor_reimpl': m['visor'], 'erro_real': erro_real,
                       'erro_reimpl': m['erro'], 'notas_real': r.get('notas', []), 'falha_real': r.get('falha'),
                       'notas_reimpl': m['notas'], 'suspeita_automacao': falha})
    (RAIZ / a.saida).write_text(json.dumps({'por_modo': por_modo, 'casos': linhas}, ensure_ascii=False,
                                                    indent=1) + '\n', encoding='utf-8')
    for modo, e in por_modo.items():
        print(f"{modo}: {e['acertos']}/{e['casos']} ({100 * e['acertos'] / e['casos']:.0f}%); sem leitura "
              f"{e['sem_leitura']}; com indício de falha da automação {e['com_falha_automacao']}")
    for x in linhas:
        if not x.get('acerto', False):
            print(f"\n{x['id']} {x.get('preparo', '')}: {x.get('passos', '')}\n  real  : {x.get('visor_real')!r} "
                  f"erro={x.get('erro_real')} {x.get('notas_real', '')} {x.get('falha_real') or ''}\n  reimpl: "
                  f"{x.get('visor_reimpl')!r} erro={x.get('erro_reimpl')} {x.get('notas_reimpl', '')}")


if __name__ == '__main__':
    main()
