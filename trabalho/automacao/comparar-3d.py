#!/usr/bin/env python3
"""Compara relatorio/resultados-reais-3d.txt com as previsões congeladas de relatorio/03d-casos-de-teste.md.

As previsões abaixo foram copiadas do arquivo congelado (SHA-256 em hashes-originais.txt); o script confere o hash antes
de comparar. Visor, linhas (H/D/O/B) e bits vêm do UIA, sem transcrição. A expressão de cada leitura prevista vem de
transcricao-capturas-3d.tsv (captura, origem, texto), em que origem = 'ocr' (o OCR leu igual, conferido na captura) ou
'manual' (transcrita a olho da captura).

Critério (fixado em 03d-casos-de-teste.md antes da execução):
  acerto  = todas as leituras previstas conferem;
  parcial = visor, linhas e bits conferem; falha só expressão;
  erro    = algum visor, linha ou conjunto de bits não confere.
Expressões comparadas sem espaços (L20; se a linha estiver cortada, o visível tem de ser sufixo do previsto).

Uso: python3 -I comparar-3d.py <raiz do projeto>"""
import hashlib, re, sys
from pathlib import Path

raiz = Path(sys.argv[1])
CONGELADO = 'e24abc00c11b76f71c9934cfcaa049af6e16b9089e962d42d4d1ca50e5a34955'
h = hashlib.sha256((raiz / 'relatorio/03d-casos-de-teste.md').read_bytes()).hexdigest()
if h != CONGELADO:
    sys.exit(f'03d-casos-de-teste.md mudou: {h}')

B64 = ' '.join(['1111'] * 16)
Z64 = '1000 ' + ' '.join(['0000'] * 15)
M63 = '-9.223.372.036.854.775.808'
F64 = 'FFFF FFFF FFFF FFFF'
# ID: (bloco, discr, [visores], {linhas finais}, bits finais ou None, expressão final ou None)
P = {
    '3d-01': ('A', 0, ['255'], dict(H='FF', D='255', O='377', B='1111 1111'), None, None),
    '3d-02': ('A', 0, ['1.000'], dict(H='3E8', D='1.000', O='1 750', B='11 1110 1000'), None, None),
    '3d-03': ('A', 0, ['1A3'], dict(H='1A3', D='419', O='643', B='1 1010 0011'), None, None),
    '3d-04': ('A', 0, ['255', 'FF', '377', '1111 1111', '255'], {}, None, None),
    '3d-05': ('A', 1, ['1234 5678 9ABC DEF0'], dict(D='1.311.768.467.463.790.320'), None, None),
    '3d-06': ('A', 1, ['1 777 777 777 777 777 777 777'], dict(H=F64, D='-1'), None, None),
    '3d-07': ('A', 1, ['277 777 777 777 777 777 777'], dict(H='2FFF FFFF FFFF FFFF', D='3.458.764.513.820.540.927'), None, None),
    '3d-08': ('A', 1, [Z64], dict(H='8000 0000 0000 0000', D=M63), None, None),
    '3d-09': ('A', 1, ['922.337.203.685.477.580'], {}, None, None),
    '3d-10': ('A', 1, ['-922.337.203.685.477.580', M63], dict(H='8000 0000 0000 0000'), None, None),
    '3d-11': ('A', 0, ['9.223.372.036.854.775.807'], dict(H='7FFF FFFF FFFF FFFF'), None, None),
    '3d-12': ('A', 1, ['12'], {}, None, None),
    '3d-13': ('A', 1, ['20'], {}, None, None),
    '3d-14': ('A', 1, ['1234'], dict(D='4.660'), None, None),
    '3d-20': ('B', 1, ['300', '44'], dict(H='2C'), None, None),
    '3d-21': ('B', 1, ['200', '-56', '-56'], dict(H='FFFF FFFF FFFF FFC8', D='-56'), None, None),
    '3d-22': ('B', 1, ['65.535', '-1', '-1'], dict(H=F64), None, None),
    '3d-23': ('B', 1, ['2.147.483.648', '-2.147.483.648'], dict(H='8000 0000'), None, None),
    '3d-24': ('B', 1, ['4.294.967.296', '0'], dict(H='0'), None, None),
    '3d-25': ('B', 1, ['-1', '-1'], dict(H=F64), None, None),
    '3d-26': ('B', 1, ['FF FFFF FFFF', 'FFFF FFFF'], dict(D='-1'), None, None),
    '3d-30': ('C', 0, ['-1'], dict(H=F64, O='1 777 777 777 777 777 777 777', B=B64), None, None),
    '3d-31': ('C', 0, [F64], dict(D='-1'), None, None),
    '3d-32': ('C', 1, ['80'], dict(D='-128'), None, None),
    '3d-33': ('C', 1, [M63], {}, None, '9223372036854775807 + 1 ='),
    '3d-34': ('C', 1, ['-2.147.483.648'], {}, None, '2147483647 + 1 ='),
    '3d-35': ('C', 1, ['-32.768'], {}, None, None),
    '3d-36': ('C', 1, ['-128'], {}, None, None),
    '3d-37': ('C', 1, ['44'], {}, None, '100 × 3 ='),
    '3d-38': ('C', 1, ['0'], {}, None, None),
    '3d-39': ('C', 1, ['-8.589.934.591'], {}, None, None),
    '3d-40': ('C', 1, ['3'], {}, None, '7 ÷ 2 ='),
    '3d-41': ('C', 1, ['-3'], {}, None, '-7 ÷ 2 ='),
    '3d-42': ('C', 1, ['-1'], {}, None, '-7 % 3 ='),
    '3d-43': ('C', 0, ['1'], {}, None, '7 % -3 ='),
    '3d-44': ('C', 0, ['Resultado indefinido'], {}, None, None),
    '3d-45': ('C', 0, ['Não é possível dividir por zero'], {}, None, None),
    '3d-46': ('C', 0, ['Resultado indefinido'], {}, None, None),
    '3d-47': ('C', 0, ['Não é possível dividir por zero', '0'], {}, None, None),
    '3d-48': ('C', 0, ['-1'], dict(H=F64), None, '1 - 2 ='),
    '3d-50': ('D', 0, ['8'], {}, None, '12 AND 10 ='),
    '3d-51': ('D', 0, ['14'], {}, None, '12 OR 10 ='),
    '3d-52': ('D', 0, ['6'], {}, None, '12 XOR 10 ='),
    '3d-53': ('D', 0, ['-9'], dict(H='FFFF FFFF FFFF FFF7'), None, '12 NAND 10 ='),
    '3d-54': ('D', 0, ['-15'], {}, None, '12 NOR 10 ='),
    '3d-55': ('D', 0, ['-6'], dict(H='FFFF FFFF FFFF FFFA'), None, 'NOT( 5 )'),
    '3d-56': ('D', 1, ['-6'], dict(H='FA'), None, 'NOT( 5 )'),
    '3d-57': ('D', 1, ['F'], dict(D='15'), None, None),
    '3d-58': ('D', 1, ['6'], {}, None, '6 OR 1 AND 2 ='),
    '3d-59': ('D', 1, ['14'], {}, None, '12 XOR 10 AND 6 ='),
    '3d-60': ('D', 1, ['-1'], {}, None, '1 OR 5 NAND 3 ='),
    '3d-61': ('D', 1, ['-6', '-1'], {}, None, '5 + NOT( 5 ) ='),
    '3d-62': ('D', 0, ['3'], dict(D='3'), None, 'F AND 3 ='),
    '3d-70': ('E', 0, ['16'], {}, None, '1 Lsh 4 ='),
    '3d-71': ('E', 1, [M63], {}, None, None),
    '3d-72': ('E', 1, ['Resultado não definido'], {}, None, None),
    '3d-73': ('E', 1, ['-4'], {}, None, '-7 Rsh 1 ='),
    '3d-74': ('E', 0, ['-4'], {}, None, None),
    '3d-75': ('E', 1, ['-128'], {}, None, None),
    '3d-76': ('E', 1, ['Resultado não definido'], {}, None, None),
    '3d-77': ('E', 1, ['C0'], dict(D='-64'), None, None),
    '3d-78': ('E', 1, ['Resultado não definido'], {}, None, None),
    '3d-79': ('E', 1, ['5'], {}, None, '1 + 1 Lsh 2 ='),
    '3d-80': ('E', 1, ['Resultado não definido'], {}, None, None),
    '3d-81': ('E', 1, ['9.223.372.036.854.775.807'], {}, None, '-1 Rsh 1 ='),
    '3d-82': ('E', 1, ['15'], {}, None, None),
    '3d-83': ('E', 0, ['40'], dict(D='64'), None, None),
    '3d-84': ('E', 1, [M63], {}, None, None),
    '3d-85': ('E', 1, ['Resultado não definido'], {}, None, None),
    '3d-86': ('E', 1, ['3', '81'], dict(D='-127'), None, 'RoR( RoL( 81 ) )'),
    '3d-87': ('E', 0, [M63], dict(H='8000 0000 0000 0000'), None, 'RoR( 1 )'),
    '3d-88': ('E', 1, ['-128'], dict(H='80'), None, None),
    '3d-89': ('E', 0, ['1'], {}, None, None),
    '3d-90': ('E', 1, ['0', '1', '2'], {}, None, None),
    '3d-91': ('E', 1, ['0', '80', '40'], {}, None, None),
    '3d-92': ('E', 1, ['0', 'B'], {}, None, None),
    '3d-93': ('E', 0, ['0', 'A'], {}, None, None),
    '3d-100': ('F', 0, ['1', '9'], dict(H='9'), {0, 3}, None),
    '3d-101': ('F', 1, [M63], dict(H='8000 0000 0000 0000'), {63}, None),
    '3d-102': ('F', 1, ['-128'], dict(H='80'), {7}, None),
    '3d-103': ('F', 0, ['5', '1'], {}, {0}, None),
    '3d-104': ('F', 1, ['4', '9'], {}, None, None),
    '3d-105': ('F', 1, ['13', '4'], {}, None, None),
    '3d-106': ('F', 1, ['9.223.372.036.854.775.807'], dict(H='7FFF FFFF FFFF FFFF'), None, None),
    '3d-107': ('F', 0, ['11'], dict(D='17'), None, None),
}

# resultados: "ID[ →n [apos X]]: visor | expr | H='..' D='..' O='..' B='..' | bits={..}[ -- obs]"
real = {}
for ln in (raiz / 'relatorio/resultados-reais-3d.txt').read_text(encoding='utf-8').splitlines():
    m = re.match(r'^(3d-\d+)(?: →(\d+) \[[^\]]*\])?: (.*)$', ln)
    if not m:
        continue
    corpo = m.group(3).split(' -- ')[0]
    partes = corpo.split(' | ')
    lin = dict(re.findall(r"([HDOB])='([^']*)'", partes[2]))
    bits = re.search(r'bits=\{([^}]*)\}', partes[3]) if len(partes) > 3 else None
    bset = None if not bits else {int(x) for x in bits.group(1).split(',') if x.strip()}
    real.setdefault(m.group(1), []).append(dict(visor=partes[0], linhas=lin, bits=bset))

trans = {}
tsv = raiz / 'trabalho/automacao/transcricao-capturas-3d.tsv'
if tsv.exists():
    for ln in tsv.read_text(encoding='utf-8').splitlines():
        if ln.strip() and not ln.startswith('#'):
            cap, origem, texto = ln.split('\t')
            trans[cap] = (origem, texto)

sem = lambda s: re.sub(r'\s+', '', s)
linhas_tab, taxa = [], {}
for cid, (bloco, discr, visores, lins, bits, expr) in P.items():
    r = real.get(cid)
    div, classe = [], 'acerto'
    if r is None:
        classe, div = 'erro', ['sem resultado']
    else:
        if len(r) != len(visores):
            div.append(f'{len(r)} leituras (previstas {len(visores)})')
        for i, (v, lr) in enumerate(zip(visores, r)):
            if lr['visor'] != v:
                div.append(f"L{i+1} visor '{lr['visor']}' (previsto '{v}')")
        fim = r[-1]
        for k, v in lins.items():
            if fim['linhas'].get(k) != v:
                div.append(f"linha {k} '{fim['linhas'].get(k)}' (prevista '{v}')")
        if bits is not None and fim['bits'] != bits:
            div.append(f"bits {sorted(fim['bits']) if fim['bits'] is not None else 'não lidos'} (previstos {sorted(bits)})")
        if div:
            classe = 'erro'
        if expr is not None:
            o, t = trans.get(f'{cid}-final', (None, None))
            if t is None:
                div.append('expressão não transcrita'); classe = 'erro' if classe == 'erro' else 'parcial'
            elif not (sem(t) == sem(expr) or (t.startswith('‹') and sem(expr).endswith(sem(t[1:])))):
                div.append(f"expressão '{t}' (prevista '{expr}')")
                if classe == 'acerto':
                    classe = 'parcial'
    origem = trans.get(f'{cid}-final', ('—',))[0] if expr is not None else '—'
    linhas_tab.append(f"| {cid} | {bloco} | {'sim' if discr else 'não'} | {classe} | {'; '.join(div) or '—'} | {origem} |")
    for chave in (bloco, 'Total') + (('Discr.',) if discr else ()):
        t = taxa.setdefault(chave, dict(n=0, acerto=0, parcial=0, erro=0))
        t['n'] += 1; t[classe] += 1

print('| ID | Bloco | Discr. | Classe | Divergências | Origem da expressão |')
print('|---|---|---|---|---|---|')
print('\n'.join(linhas_tab))
print()
print('| Bloco | Casos | Acerto | Parcial | Erro | Taxa (acerto/casos) |')
print('|---|---:|---:|---:|---:|---:|')
for chave in ['A', 'B', 'C', 'D', 'E', 'F', 'Total', 'Discr.']:
    t = taxa[chave]
    print(f"| {chave} | {t['n']} | {t['acerto']} | {t['parcial']} | {t['erro']} | {round(100 * t['acerto'] / t['n'])}% |")
