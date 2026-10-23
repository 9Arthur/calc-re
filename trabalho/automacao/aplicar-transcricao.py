#!/usr/bin/env python3
"""Troca a coluna de expressão de relatorio/resultados-reais.txt (OCR) pela transcrição conferida
nas capturas (transcricao-capturas.tsv). Guarda o OCR original em observação quando difere.
Uso: python3 -I aplicar-transcricao.py <resultados-reais.txt> <transcricao-capturas.tsv>"""
import re, sys
res, tsv = sys.argv[1], sys.argv[2]
tr = dict(l.split('\t', 1) for l in open(tsv, encoding='utf-8').read().splitlines()[1:] if l)
saida = []
for l in open(res, encoding='utf-8').read().splitlines():
    m = re.match(r'^(3a-\S+)( →(\d+) \[[^\]]*\])?: (.*?) \| (.*?)( -- (.*))?$', l)
    if not m:
        saida.append(l.replace('expressao = OCR da captura', 'expressao = transcrita da captura e conferida'))
        continue
    cap = f'{m.group(1)}-{m.group(3)}' if m.group(3) else f'{m.group(1)}-final'
    vis, ocr, obs = m.group(4), m.group(5), m.group(7)
    expr = tr[cap]
    extra = []
    if '  [' in expr:
        expr, nota = expr.split('  [', 1); extra.append(nota.rstrip(']'))
    if re.sub(r'\s', '', ocr) != re.sub(r'\s', '', expr):
        extra.append(f"OCR leu '{ocr}'")
    if obs: extra.append(obs)
    prefixo = l.split(': ', 1)[0]
    saida.append(f'{prefixo}: {vis} | {expr}' + (' -- ' + '; '.join(extra) if extra else ''))
open(res, 'w', encoding='utf-8').write('\n'.join(saida) + '\n')
