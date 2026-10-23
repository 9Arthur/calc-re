#!/usr/bin/env python3
"""Compara relatorio/resultados-reais-3b.txt com as previsões congeladas de relatorio/03b-casos-de-teste.md.

As previsões abaixo foram copiadas do arquivo congelado (SHA-256 em hashes-originais.txt); o script confere o hash
antes de comparar. A expressão de cada leitura vem de transcricao-capturas-3b.tsv (captura, origem, texto), em que
origem = 'ocr' (o OCR leu certo, conferido na captura) ou 'manual' (transcrito a olho porque o OCR errou ou não leu).
Histórico e memória vêm do UIA (texto dos TextBlocks), sem transcrição.

Critério (fixado antes da execução):
  acerto  = todas as leituras previstas conferem;
  parcial = visor, histórico e memória conferem; falha só expressão ou estado de botão;
  erro    = visor, histórico ou memória não conferem.
Expressões são comparadas sem espaços (L20); visor e memória, exatamente.

Uso: python3 -I comparar-3b.py <raiz do projeto>"""
import hashlib, re, sys
from pathlib import Path

raiz = Path(sys.argv[1])
CONGELADO = 'c114045b8fee78a5b462846e2332c0166048675ea3d86df6ba13a5fdf832bf38'
h = hashlib.sha256((raiz / 'relatorio/03b-casos-de-teste.md').read_bytes()).hexdigest()
assert h == CONGELADO, f'03b-casos-de-teste.md mudou: {h}'

DZ = 'Não é possível dividir por zero'
T = '0,3333333333333333'
def R(visor, expr, hist, mem, bot=None):
    return dict(visor=visor, expr=expr, hist=hist, mem=mem, bot=bot or {})
H = lambda *p: list(p)  # itens (expressão, resultado), topo primeiro

PREV = {
 '3b-09': ('A', [R('12', '7 + 5 =', H(('7 + 5 =', '12')), []), R('0', '', H(), []),
                 R('2', '1 + 1 =', H(('1 + 1 =', '2')), []), R('0', '', H(('7 + 5 =', '12')), [])]),
 '3b-11': ('A', [R('7', '', H(), ['7'], {'MC': 'hab', 'MR': 'hab', 'M▾': 'hab'})]),
 '3b-18': ('A', [R('7', '', H(), ['7']), R('7', '', H(), [], {'MC': 'des', 'MR': 'des', 'M▾': 'des'})]),
 '3b-19': ('A', [R(T, '', H(('1 ÷ 3 =', T)), [T]),
                 R('1', f'{T} × 3 =', H((f'{T} × 3 =', '1'), ('1 ÷ 3 =', T)), [T])]),
 '3b-25': ('A', [R('7', '', H(), ['7']), R('0', '', H(), ['7']), R('7', '', H(), ['7'])]),
 '3b-26': ('A', [R(DZ, '8 ÷', H(), ['7'], {'M+': 'des', 'M−': 'des', 'MS': 'des', 'MC': 'hab', 'MR': 'hab'}),
                 R('7', '', H(), ['7'])]),
 '3b-01': ('B', [R('12', '7 + 5 =', H(('7 + 5 =', '12')), [])]),
 '3b-02': ('B', [R('5', '5 ×', H(('2 + 3 =', '5')), []), R('20', '5 × 4 =', H(('5 × 4 =', '20'), ('2 + 3 =', '5')), [])]),
 '3b-02c': ('B', [R('3', '2 + 3 ×', H(), []), R('14', '2 + 3 × 4 =', H(('2 + 3 × 4 =', '14')), [])]),
 '3b-03': ('B', [R('5', '2 + 3 =', H(('2 + 3 =', '5')), []), R('8', '5 + 3 =', H(('5 + 3 =', '8'), ('2 + 3 =', '5')), [])]),
 '3b-04': ('B', [R('5', '5 =', H(('5 =', '5')), []), R('5', '5 =', H(('5 =', '5'), ('5 =', '5')), [])]),
 '3b-05': ('B', [R(DZ, '8 ÷', H(), []), R('2', '1 + 1 =', H(('1 + 1 =', '2')), [])]),
 '3b-06': ('B', [R('3', '√( 9 )', H(), []), R('5', None, H(('√( 9 )', '3')), [])]),
 '3b-07': ('B', [R('3', '√( 9 ) =', H(('√( 9 ) =', '3')), [])]),
 # 3b-08: o arquivo congelado prevê contagem, topo e base
 '3b-08': ('B', [R('22', '21 + 1 =', {'n': 20, 'topo': ('21 + 1 =', '22'), 'base': ('2 + 1 =', '3')}, [])]),
 '3b-10': ('B', [R('2', '1 + 1 =', H(('1 + 1 =', '2')), []), R('2', '1 + 1 =', H(), [])]),
 '3b-12': ('C', [R('3', '', H(), ['3', '7'])]),
 '3b-13': ('C', [R('3', '', H(), ['10'])]),
 '3b-14': ('C', [R('3', '', H(), ['4'])]),
 '3b-15': ('C', [R('5', '', H(), ['5'])]),
 '3b-16': ('C', [R('5', '', H(), ['-5'])]),
 '3b-17': ('C', [R('3', '', H(), ['3', '7'])]),
 '3b-20': ('C', [R('1.234', '', H(), ['1.234'])]),
 '3b-21': ('C', [R('5', '2 + 3 =', H(('2 + 3 =', '5')), []), R('5', '', H(('2 + 3 =', '5')), ['5'])]),
 '3b-22': ('C', [R('12', '5 + 7 =', H(('5 + 7 =', '12')), ['7'])]),
 '3b-23': ('C', [R('7', None, H(('√( 9 )', '3')), ['7'])]),
 '3b-24': ('C', [R('3', '2 +', H(), ['10']), R('5', '2 + 3 =', H(('2 + 3 =', '5')), ['10'])]),
}

sem_esp = lambda s: re.sub(r'\s', '', s or '')
tr = {}
for l in (raiz / 'trabalho/automacao/transcricao-capturas-3b.tsv').read_text(encoding='utf-8').splitlines()[1:]:
    if l.strip():
        cap, origem, texto = l.split('\t', 2)
        tr[cap] = (origem, '' if texto == '(vazia)' else texto)

reais = {}
pat = re.compile(r'^(3b-\S+?)(?: →(\d+) \[apos (?:\[[^\]]*\]|[^\]\[])*\])?: (.*?) \| (.*?) \| hist\((\d+)\): (.*?) \| mem: (.*?) \| (MC=.*?)(?: -- (.*))?$')
for l in (raiz / 'relatorio/resultados-reais-3b.txt').read_text(encoding='utf-8').splitlines():
    m = pat.match(l)
    if not m: continue
    cid, n = m.group(1), m.group(2)
    cap = f'{cid}-{n}' if n else f'{cid}-final'
    hist = [] if m.group(6).startswith('(vazia') else [tuple(x.strip() for x in it[1:-1].split(' | ', 1)) for it in m.group(6).split('; ')]
    mem = [] if m.group(7).startswith('(vazia') else m.group(7).split('; ')
    bot = dict(kv.split('=') for kv in m.group(8).split())
    reais.setdefault(cid, []).append(dict(cap=cap, visor=m.group(3), ocr=m.group(4), n=int(m.group(5)), hist=hist,
                                         mem=mem, bot=bot, obs=m.group(9) or ''))

def fmt_h(h): return '(vazia)' if not h else '; '.join(f'[{e} \\| {r}]' for e, r in h)

linhas, taxa = [], {}
for cid, (bloco, prevs) in PREV.items():
    rs = reais.get(cid, [])
    falhas, cls_falha, origens, det = [], [], [], []
    if len(rs) != len(prevs):
        falhas.append(f'{len(rs)} leituras, previstas {len(prevs)}'); cls_falha.append('erro')
    for i, (p, r) in enumerate(zip(prevs, rs), 1):
        rot = f'L{i}'
        if r['visor'] != p['visor']:
            falhas.append(f"{rot} visor '{r['visor']}' ≠ '{p['visor']}'"); cls_falha.append('erro')
        if isinstance(p['hist'], dict):
            ok = r['n'] == p['hist']['n'] and r['hist'] and \
                 sem_esp(r['hist'][0][0]) == sem_esp(p['hist']['topo'][0]) and r['hist'][0][1] == p['hist']['topo'][1] and \
                 sem_esp(r['hist'][-1][0]) == sem_esp(p['hist']['base'][0]) and r['hist'][-1][1] == p['hist']['base'][1]
            if not ok:
                falhas.append(f"{rot} histórico n={r['n']} topo={r['hist'][:1]} base={r['hist'][-1:]}"); cls_falha.append('erro')
        else:
            ok = len(r['hist']) == len(p['hist']) and all(sem_esp(a[0]) == sem_esp(b[0]) and a[1] == b[1] for a, b in zip(r['hist'], p['hist']))
            if not ok:
                falhas.append(f"{rot} histórico {fmt_h(r['hist'])} ≠ {fmt_h(p['hist'])}"); cls_falha.append('erro')
        if r['mem'] != p['mem']:
            falhas.append(f"{rot} memória {r['mem']} ≠ {p['mem']}"); cls_falha.append('erro')
        for k, v in p['bot'].items():
            if r['bot'].get(k) != v:
                falhas.append(f"{rot} {k}={r['bot'].get(k)} (previsto {v})"); cls_falha.append('parcial')
        origem, texto = tr.get(r['cap'], ('?', None))
        origens.append(f"{rot}:{origem}")
        if p['expr'] is not None:
            if texto is None:
                falhas.append(f'{rot} expressão sem transcrição'); cls_falha.append('parcial')
            elif sem_esp(texto) != sem_esp(p['expr']):
                falhas.append(f"{rot} expressão '{texto}' ≠ '{p['expr']}'"); cls_falha.append('parcial')
        det.append(r)
    cls = 'erro' if 'erro' in cls_falha else 'parcial' if cls_falha else 'acerto'
    taxa.setdefault(bloco, []).append(cls)
    linhas.append((cid, bloco, cls, '; '.join(falhas) or '—', ' '.join(origens)))

print('| ID | Bloco | Classe | Divergências | Origem da expressão por leitura |')
print('|---|---|---|---|---|')
for cid, b, c, f, o in linhas:
    print(f'| {cid} | {b} | {c} | {f} | {o} |')
print()
print('| Bloco | Casos | Acerto | Parcial | Erro | Taxa |')
print('|---|---:|---:|---:|---:|---:|')
tot = []
for b in sorted(taxa):
    v = taxa[b]; tot += v
    print(f"| {b} | {len(v)} | {v.count('acerto')} | {v.count('parcial')} | {v.count('erro')} | {100 * v.count('acerto') / len(v):.0f}% |")
print(f"| Total | {len(tot)} | {tot.count('acerto')} | {tot.count('parcial')} | {tot.count('erro')} | {100 * tot.count('acerto') / len(tot):.0f}% |")
