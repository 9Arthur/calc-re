#!/usr/bin/env python3
"""Compara relatorio/resultados-reais-3c.txt com as previsões congeladas de relatorio/03c-casos-de-teste.md.

As previsões abaixo foram copiadas do arquivo congelado (SHA-256 em hashes-originais.txt); o script confere o hash
antes de comparar. A expressão de cada leitura vem de transcricao-capturas-3c.tsv (captura, origem, texto), em que
origem = 'ocr' (o OCR leu certo, conferido na captura) ou 'manual' (transcrita a olho da captura).

Critério (fixado em 03c-casos-de-teste.md antes da execução):
  visor exato; expressão sem espaços (se cortada na tela, o visível tem de ser sufixo do previsto); None = não prevista.
  A: acerto = tudo confere; parcial = visores conferem e falha expressão; erro = algum visor não confere.
  B: as mesmas classes e 'quase' = o visor só difere no último dígito exibido (|diferença| <= 1 unidade da última casa
     da exibição de 32 dígitos). A taxa do B conta só 'acerto'.

Uso: python3 -I comparar-3c.py <raiz do projeto>"""
import hashlib, re, sys
from decimal import Decimal
from pathlib import Path

raiz = Path(sys.argv[1])
CONGELADO = 'b31e6aee9f9da7aca24ab16dfa0ced279136fc2e34fb48da4467908ad8c5d2e1'
h = hashlib.sha256((raiz / 'relatorio/03c-casos-de-teste.md').read_bytes()).hexdigest()
assert h == CONGELADO, f'03c-casos-de-teste.md mudou: {h}'

EI, ES = 'Entrada inválida', 'Estouro'
PI = '3,1415926535897932384626433832795'
E = '2,7182818284590452353602874713527'
U = lambda v, x=None: [(v, x)]
PREV = {
 '3c-01': ('A', U('0', 'cos₀( 90 )')), '3c-02': ('A', U(EI, 'tan₀( 90 )')), '3c-03': ('A', U('0', f'sinᵣ( {PI} )')),
 '3c-04': ('A', U('0', 'sin₀( 180 )')), '3c-05': ('A', U('1', 'cosᵣ( 0 )')), '3c-06': ('A', U('90', 'sin₀⁻¹( 1 )')),
 '3c-07': ('A', U(EI, 'sin₀⁻¹( 2 )')), '3c-08': ('A', [('1,e+100', None), (EI, 'sin₀( 1,e+100 )')]),
 '3c-09': ('A', U('2')), '3c-10': ('A', U('120', 'fact( 5 )')), '3c-11': ('A', U('1', 'fact( 0 )')),
 '3c-12': ('A', U('2.432.902.008.176.640.000', 'fact( 20 )')), '3c-13': ('A', U(EI, 'fact( -1 )')),
 '3c-14': ('A', U(ES, 'fact( 3250 )')), '3c-15': ('A', U('1', '7 Mod 3 =')), '3c-16': ('A', U('2', '-7 Mod 3 =')),
 '3c-17': ('A', U('-2', '7 Mod -3 =')), '3c-18': ('A', U('1,5', '7,5 Mod 2 =')), '3c-19': ('A', U('5', '5 Mod 0 =')),
 '3c-20': ('A', U('1.024', '2 ^ 10 =')), '3c-21': ('A', U('0,5', '2 ^ -1 =')), '3c-22': ('A', U(EI, '0 ^')),
 '3c-23': ('A', U('1.000', '10^( 3 )')), '3c-24': ('A', U('10.000.000.000.000.000.000.000.000.000.000', '10^( 31 )')),
 '3c-25': ('A', U('1,e+32', '10^( 32 )')), '3c-26': ('A', U(EI, 'log( 0 )')), '3c-27': ('A', U(EI, 'ln( -1 )')),
 '3c-28': ('A', [('2,e+0', None), ('2,e+3', None), ('2.000', '2000 =')]),
 '3c-29': ('A', [('1,e-4', None), ('0,0001', '0,0001 =')]),
 '3c-30': ('A', [('123', None), ('1,23e+2', None), ('123', None)]), '3c-31': ('A', U('5', 'abs( -5 )')),
 '3c-32': ('A', U('0,33333333333333333333333333333333', '1 ÷ 3 =')),
 '3c-33': ('A', U('0,06666666666666666666666666666667', '2 ÷ 30 =')),
 '3c-34': ('A', U('0,00333333333333333333333333333333', '1 ÷ 300 =')),
 '3c-35': ('A', U('3,3333333333333333333333333333333e-4', '1 ÷ 3000 =')),
 '3c-36': ('A', [('12.345.678.901.234.567.890.123.456.789.012', None)] * 2),
 '3c-37': ('A', [('6', '2 × 3 +'), ('26', '2 × 3 + 4 × 5 =')]), '3c-38': ('A', [('8', '2 ^ 3 ^'), ('64', '2 ^ 3 ^ 2 =')]),
 '3c-39': ('A', U('50', '2 + 3 × 4 ^ 2 =')), '3c-40': ('A', U('6', '7 Mod 4 × 2 =')),
 '3c-41': ('A', [('5', '( 2 + 3 ) ×'), ('20', '( 2 + 3 ) × 4 =')]),
 '3c-42': ('A', [('5', '( 2 + 3 )'), ('20', '( 2 + 3 ) × 4 =')]), '3c-43': ('A', U('5', '( 2 + 3 ) =')),
 '3c-44': ('A', U('12', '2 × ( 3 + ( 4 - 1 ) ) =')), '3c-45': ('A', U('14', '2 × ( 3 + 4 ) =')),
 '3c-46': ('A', [('5', None), ('4', None), ('20', '1 + ( 2 + 3 ) × 4 =')]), '3c-47': ('A', U('14', '2 + 3 × 4 =')),
 '3c-50': ('B', U('0,5', 'sin₀( 30 )')), '3c-51': ('B', U('0,5', 'cos₀( 60 )')),
 '3c-52': ('B', U('0,70710678118654752440084436210485', 'sin₀( 45 )')), '3c-53': ('B', U('1', 'tan₀( 45 )')),
 '3c-54': ('B', U('-0,5', 'sin₀( -30 )')), '3c-55': ('B', U('0,8414709848078965066525023216303', 'sinᵣ( 1 )')),
 '3c-56': ('B', U('1,5574077246549022305069748074584', 'tanᵣ( 1 )')),
 '3c-57': ('B', U('0,99987663248166059863890712773125', 'cos₉( 1 )')), '3c-58': ('B', U('1', 'sin₉( 100 )')),
 '3c-59': ('B', U('30', 'sin₀⁻¹( 0,5 )')), '3c-60': ('B', U('1,0471975511965977461542144610932', 'cosᵣ⁻¹( 0,5 )')),
 '3c-61': ('B', U('50', 'tan₉⁻¹( 1 )')),
 '3c-62': ('B', [('-1,e+100', None), ('0,98480775301220805936674302458952', 'sin₀( -1,e+100 )')]),
 '3c-63': ('B', [(PI, None), (PI + 'e+0', None), (PI, None)]), '3c-64': ('B', U(E)), '3c-65': ('B', U(E, 'e^( 1 )')),
 '3c-66': ('B', U('4,5399929762484851535591515560551e-5', 'e^( -10 )')),
 '3c-67': ('B', U('2,3025850929940456840179914546844', 'ln( 10 )')),
 '3c-68': ('B', U('0,30102999566398119521373889472449', 'log( 2 )')), '3c-69': ('B', U('3', 'log( 1000 )')),
 '3c-70': ('B', U('3,1622776601683793319988935444327', '10^( 0,5 )')),
 '3c-71': ('B', U('1,4142135623730950488016887242097', '2 ^ 0,5 =')), '3c-72': ('B', U('3', '27 yroot 3 =')),
 '3c-73': ('B', U('-2', '-8 yroot 3 =')), '3c-74': ('B', U('3', '8 log base 2 =')),
 '3c-75': ('B', U('0,88622692545275801364908374167057', 'fact( 0,5 )')),
}

sem_esp = lambda s: re.sub(r'\s', '', s or '')

def num(s):
    try:
        m = re.fullmatch(r'(-?)([0-9.]+(?:,[0-9]*)?)(?:e([+-][0-9]+))?', s)
        if not m: return None
        v = Decimal(m.group(2).replace('.', '').replace(',', '.').rstrip('.') or '0')
        if m.group(3): v = v.scaleb(int(m.group(3)))
        return -v if m.group(1) else v
    except Exception:
        return None

def quase(prev, real):
    p, r = num(prev), num(real)
    if p is None or r is None or p == 0: return False
    a = abs(p)
    ulp = Decimal(10) ** -32 if Decimal('0.001') <= a < 1 else Decimal(10) ** (a.adjusted() - 31)
    return abs(p - r) <= ulp

tr = {}
for l in (raiz / 'trabalho/automacao/transcricao-capturas-3c.tsv').read_text(encoding='utf-8').splitlines()[1:]:
    if l.strip():
        cap, origem, texto = l.split('\t', 2)
        tr[cap] = (origem, '' if texto == '(vazia)' else texto)

reais = {}
pat = re.compile(r'^(3c-\d+)(?: →(\d+) \[apos [^\]]*\])?: (.*?) \| (.*?)(?: -- (.*))?$')
for l in (raiz / 'relatorio/resultados-reais-3c.txt').read_text(encoding='utf-8').splitlines():
    m = pat.match(l)
    if not m: continue
    cid, n = m.group(1), m.group(2)
    cap = f'{cid}-{n}' if n else f'{cid}-final'
    reais.setdefault(cid, []).append((cap, m.group(3), m.group(5)))

linhas, tot = [], {}
for cid, (bloco, prevs) in PREV.items():
    rs = reais.get(cid)
    if not rs:
        linhas.append((cid, bloco, 'sem execução', '—', '')); continue
    div, classe, origens = [], 'acerto', []
    for i, ((pv, pe), (cap, rv, obs)) in enumerate(zip(prevs, rs), 1):
        origem, re_txt = tr.get(cap, ('?', None))
        origens.append(f'L{i}:{origem}')
        if rv != pv:
            if bloco == 'B' and quase(pv, rv):
                div.append(f'L{i} visor {rv!r} (previsto {pv!r}, só o último dígito)')
                if classe == 'acerto' or classe == 'parcial': classe = 'quase'
            else:
                div.append(f'L{i} visor {rv!r} (previsto {pv!r})'); classe = 'erro'
        if pe is not None:
            if re_txt is None:
                div.append(f'L{i} expressão sem transcrição'); classe = 'erro' if classe == 'erro' else ('quase' if classe == 'quase' else 'parcial')
            else:
                a, b = sem_esp(re_txt), sem_esp(pe)
                cortada = re_txt.startswith('…')
                ok = (b.endswith(sem_esp(re_txt.lstrip('…'))) if cortada else a == b)
                if not ok:
                    div.append(f'L{i} expressão {re_txt!r} (prevista {pe!r})')
                    if classe == 'acerto': classe = 'parcial'
        if obs: div.append(f'L{i} obs: {obs}')
    if len(rs) != len(prevs):
        div.append(f'{len(rs)} leituras para {len(prevs)} previstas'); classe = 'erro'
    tot.setdefault(bloco, []).append(classe)
    linhas.append((cid, bloco, classe, '; '.join(div) or '—', ' '.join(origens)))

print('| ID | Bloco | Classe | Divergências | Origem da expressão por leitura |')
print('|---|---|---|---|---|')
for l in linhas:
    print('| ' + ' | '.join(l) + ' |')
print()
print('| Bloco | Casos | Acerto | Quase | Parcial | Erro | Taxa (acerto/casos) |')
print('|---|---:|---:|---:|---:|---:|---:|')
todos = []
for b in sorted(tot):
    c = tot[b]; todos += c
    print(f"| {b} | {len(c)} | {c.count('acerto')} | {c.count('quase')} | {c.count('parcial')} | {c.count('erro')} | {100 * c.count('acerto') / len(c):.0f}% |")
print(f"| Total | {len(todos)} | {todos.count('acerto')} | {todos.count('quase')} | {todos.count('parcial')} | {todos.count('erro')} | {100 * todos.count('acerto') / len(todos):.0f}% |")
